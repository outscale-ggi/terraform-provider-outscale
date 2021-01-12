from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_AddTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AddTags, cls).setup_class()
        cls.ret = None
        cls.tags = {}
        cls.lbu_name = id_generator(prefix='lbu-')
        cls.ret = create_load_balancer(cls.a1_r1, lb_name=cls.lbu_name, listeners=[
            {'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                        availability_zones=[cls.a1_r1.config.region.az_name])

    def setup_method(self, method):
        super(Test_AddTags, self).setup_method(method)
        try:
            self.tags = {}
        except Exception as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            resp = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult.TagDescriptions[0].Tags
            if resp:
                for entry in resp:
                    tags = {}
                    for key, value in entry.__dict__.items():
                        if key.startswith('_'):
                            continue
                        tags[key] = value
                    self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
        finally:
            super(Test_AddTags, self).teardown_method(method)

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret:
                # I KNOW, IT HURTS ON THE EYE! MAIS C'EST COMME ÇA
                sleep(60)
                delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_AddTags, cls).teardown_class()

    def test_T5378_valid_params(self):
        tag_key = id_generator("tagkey-")
        tag_value = id_generator("tagvalue-")
        tags = {'Key': tag_key, 'Value': tag_value}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
        resp = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult
        assert resp.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(resp.TagDescriptions[0].Tags) == 1
        assert resp.TagDescriptions[0].Tags[0].Key == tags['Key']
        assert resp.TagDescriptions[0].Tags[0].Value == tags['Value']

    def test_T5379_valid_params_dry_run(self):
        tags = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags], DryRun=True)
        assert_dry_run(ret)

    def test_T5380_without_tag_field(self):
        try:
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter Tags')

    def test_T5390_existing_tag(self):
        tags = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
        tags_2 = {'Key': tags['Key'], 'Value': id_generator("tagvalue-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags_2])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value == tags_2['Value']

    def test_T5383_without_value(self):
        tags = {'Key': id_generator("tagkey-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult
        assert ret.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(ret.TagDescriptions[0].Tags) == 1
        assert ret.TagDescriptions[0].Tags[0].Key == tags['Key']
        assert hasattr(ret.TagDescriptions[0].Tags[0], 'Value') is False

    def test_T5384_with_empty_value(self):
        tags = {'Key': id_generator("tagkey-"), 'Value': ''}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult
        assert ret.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(ret.TagDescriptions[0].Tags) == 1
        assert ret.TagDescriptions[0].Tags[0].Key == tags['Key']

    def test_T5387_with_one_tag_multiple_lbu(self):
        lbu_2 = None
        name = id_generator(prefix='lbu-')
        try:
            lbu_2 = create_load_balancer(self.a1_r1, lb_name=name, listeners=[
                {'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                             availability_zones=[self.a1_r1.config.region.az_name])
            tags = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name, name], Tags=[tags])
            ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name, name])
            assert len(ret.response.DescribeTagsResult.TagDescriptions) == 2
            lbu_names = [self.lbu_name, name]
            for tag in ret.response.DescribeTagsResult.TagDescriptions:
                assert tag.LoadBalancerName in lbu_names
                assert len(tag.Tags) == 1
                assert tag.Tags[0].Key == tags['Key']
                assert tag.Tags[0].Value == tags['Value']
        finally:
            if lbu_2:
                sleep(60)
                delete_lbu(self.a1_r1, name)

    def test_T5388_with_multiple_tag_one_lbu(self):
        tags = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        tags2 = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags, tags2])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult
        assert ret.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(ret.TagDescriptions[0].Tags) == 2
        assert ret.TagDescriptions[0].Tags[0].Key in [tags['Key'], tags2['Key']]
        assert ret.TagDescriptions[0].Tags[0].Value in [tags['Value'], tags2['Value']]
        assert ret.TagDescriptions[0].Tags[1].Key in [tags['Key'], tags2['Key']]
        assert ret.TagDescriptions[0].Tags[1].Value in [tags['Value'], tags2['Value']]

    def test_T5389_with_multiple_tag_multiple_lbu(self):
        lbu_2 = None
        name = id_generator(prefix='lbu-')
        try:
            lbu_2 = create_load_balancer(self.a1_r1, lb_name=name, listeners=[
                {'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                         availability_zones=[self.a1_r1.config.region.az_name])
            tags = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            tags2 = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name, name], Tags=[tags, tags2])
            ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult
            ret_2 = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[name]).response.DescribeTagsResult
            assert ret.TagDescriptions[0].LoadBalancerName == self.lbu_name
            assert len(ret.TagDescriptions[0].Tags) == 2
            assert ret_2.TagDescriptions[0].LoadBalancerName == name
            assert len(ret_2.TagDescriptions[0].Tags) == 2
        finally:
            if lbu_2:
                sleep(60)
                delete_lbu(self.a1_r1, name)

    def test_T5381_without_key(self):
        try:
            tags = {'Value': id_generator("tagvalue-")}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
            if ret.status_code == 200:
                known_error('TINA-6097', 'lbu.AddTags issues (keyTag and invalid param)')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5382_with_empty_key(self):
        try:
            tags = {'Key': '', 'Value': id_generator("tagvalue-")}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
            if ret.status_code == 200:
                known_error('TINA-6097', 'lbu.AddTags issues (keyTag and invalid param)')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5385_invalid_params(self):
        try:
            tags = {'toto': 'toto'}
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
            ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name])
            if ret.status_code == 200:
                known_error('TINA-6097', 'lbu.AddTags issues (keyTag and invalid param)')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5386_without_lbu_name(self):
        try:
            tags = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            self.a1_r1.lbu.AddTags(Tags=[tags])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5391_from_another_account(self):
        try:
            tags = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            self.a2_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[tags])
            assert False, "call should not have been successful, invalid param"
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', "The specified load balancer does not exists.")
