from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu

class Test_AddTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.ret = None
        cls.lbu_name = ""
        super(Test_AddTags, cls).setup_class()

    def setup_method(self, method):
        super(Test_AddTags, self).setup_method(method)
        try:
            self.lbu_name = id_generator(prefix='lbu-')
            self.ret = create_load_balancer(self.a1_r1, lb_name=self.lbu_name, listeners=[
                {'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[self.a1_r1.config.region.az_name])
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.ret:
                # I KNOW, IT HURTS ON THE EYE! MAIS C'EST COMME ÇA
                sleep(60)
                delete_lbu(self.a1_r1, self.lbu_name)
        finally:
            super(Test_AddTags, self).teardown_method(method)

    def test_T5378_valid_params(self):
        tag_key = id_generator("tagkey-")
        tag_value = id_generator("tagvalue-")
        filters = {'Key': tag_key, 'Value': tag_value}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(ret.response.DescribeTagsResult.TagDescriptions[0].Tags) == 1
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Key == filters['Key']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value == filters['Value']

    def test_T5379_valid_params_dry_run(self):
        tag_key = id_generator("tagkey-")
        tag_value = id_generator("tagvalue-")
        filters = {'Key': tag_key, 'Value': tag_value}
        ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters], DryRun = True)
        assert_dry_run(ret)

    def test_T5380_without_tag_field(self):
        try:
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter Tags')

    def test_T5381_without_key(self):
        try:
            tag_value = id_generator("tagvalue-")
            filters = {'Value': tag_value}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            if ret.status_code == 200:
                known_error('TINA-6097', 'lbu.AddTags issues (keyTag and invalid param)')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5382_with_empty_key(self):
        try:
            tag_value = id_generator("tagvalue-")
            filters = {'Key': '', 'Value': tag_value}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            if ret.status_code == 200:
                known_error('TINA-6097', 'lbu.AddTags issues (keyTag and invalid param)')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5383_without_value(self):
        tag_key = id_generator("tagkey-")
        filters = {'Key': tag_key}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(ret.response.DescribeTagsResult.TagDescriptions[0].Tags) == 1
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Key == filters['Key']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value is None

    def test_T5384_with_empty_value(self):
        tag_key = id_generator("tagkey-")
        filters = {'Key': tag_key, 'Value': ''}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(ret.response.DescribeTagsResult.TagDescriptions[0].Tags) == 1
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Key == filters['Key']

    def test_T5385_invalid_params(self):
        try:
            tag_key = id_generator("tagkey-")
            tag_value = id_generator("tagvalue-")
            filters = {'Key': tag_key, 'Value': tag_value, 'toto': 'toto'}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            if ret.status_code == 200:
                known_error('TINA-6097', 'lbu.AddTags issues (keyTag and invalid param)')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5386_without_lbu_name(self):
        try:
            tag_key = id_generator("tagkey-")
            tag_value = id_generator("tagvalue-")
            filters = {'Key': tag_key, 'Value': tag_value}
            self.a1_r1.lbu.AddTags(Tags=[filters])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5387_with_one_tag_multiple_lbu(self):
        lbu_2 = None
        name = id_generator(prefix='lbu-')
        try:
            lbu_2 = create_load_balancer(self.a1_r1, lb_name=name, listeners=[
                {'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                             availability_zones=[self.a1_r1.config.region.az_name])
            tag_key = id_generator("tagkey-")
            tag_value = id_generator("tagvalue-")
            filters = {'Key': tag_key, 'Value': tag_value}
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name, name], Tags=[filters])
            ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name, name])
            assert len(ret.response.DescribeTagsResult.TagDescriptions) == 2
            lbu_names = [self.lbu_name, name]
            i = 0
            for tag in ret.response.DescribeTagsResult.TagDescriptions:
                assert tag.LoadBalancerName == lbu_names[i]
                assert len(tag.Tags) == 1
                assert tag.Tags[0].Key == filters['Key']
                assert tag.Tags[0].Value == filters['Value']
            i += 1
        finally:
            if lbu_2:
                sleep(60)
                delete_lbu(self.a1_r1, name)

    def test_T5388_with_multiple_tag_one_lbu(self):
        filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        filters2 = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters, filters2])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].LoadBalancerName == self.lbu_name
        assert len(ret.response.DescribeTagsResult.TagDescriptions[0].Tags) == 2
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Key == filters['Key']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value == filters['Value']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[1].Key == filters2['Key']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[1].Value == filters2['Value']

    def test_T5389_with_multiple_tag_multiple_lbu(self):
        lbu_2 = None
        name = id_generator(prefix='lbu-')
        try:
            lbu_2 = create_load_balancer(self.a1_r1, lb_name=name, listeners=[
                {'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                         availability_zones=[self.a1_r1.config.region.az_name])
            filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            filters2 = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name, self.lbu_name], Tags=[filters, filters2])
        finally:
            if lbu_2:
                sleep(60)
                delete_lbu(self.a1_r1, name)

    def test_T5390_existing_tag(self):
        tag_key = id_generator("tagkey-")
        tag_value = id_generator("tagvalue-")
        filters = {'Key': tag_key, 'Value': tag_value}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
        tag_key_2 = id_generator("tagkey-")
        tag_value_2 = id_generator("tagvalue-")
        filters2 = {'Key': tag_key_2, 'Value': tag_value_2}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters2])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value == filters2['Value']

    def test_T5391_from_another_account(self):
        try:
            tag_key = id_generator("tagkey-")
            tag_value = id_generator("tagvalue-")
            filters = {'Key': tag_key, 'Value': tag_value}
            self.a2_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            assert False, "call should not have been successful, invalid param"
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', "The specified load balancer does not exists.")
