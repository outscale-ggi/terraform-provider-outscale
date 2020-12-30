from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_AddTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AddTags, cls).setup_class()
        cls.ret1 = None
        cls.ret2 = None
        cls.lbu_names = []
        try:
            name = id_generator(prefix='lbu-')
            cls.ret1 = create_load_balancer(cls.a1_r1, lb_name=name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
            cls.lbu_names.append(name)
            name = id_generator(prefix='lbu-')
            cls.ret2 = create_load_balancer(cls.a1_r1, lb_name=name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
            cls.lbu_names.append(name)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret1:
                delete_lbu(cls.a1_r1, cls.lbu_names[0])
            if cls.ret2:
                delete_lbu(cls.a1_r1, cls.lbu_names[1])
        finally:
            super(Test_AddTags, cls).teardown_class()

    def test_TXXX_valid_params(self):
        filters = {'Key': 'tag_key', 'Value': 'tag_value'}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_names[0]])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].LoadBalancerName == self.lbu_names[0]
        assert len(ret.response.DescribeTagsResult.TagDescriptions[0].Tags) == 1
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Key == filters['Key']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value == filters['Value']

    def test_TXXX_valid_params_dry_run(self):
        filters = {'Key': 'tag_key', 'Value': 'tag_value'}
        ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters], DryRun = True)
        assert_dry_run(ret)

    def test_TXXX_without_tag_field(self):
        # call succeed
        try:
            self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]])
            known_error('', '')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_TXXX_without_key(self):
        # call succeed
        try:
            filters = {'Value': 'tag_value'}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
            if ret.status_code == 200:
                known_error('', '')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_TXXX_with_empty_key(self):
        # call succeed
        try:
            filters = {'Key': '', 'Value': 'tag_value'}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
            if ret.status_code == 200:
                known_error('', '')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_TXXX_without_value(self):
        # call succeed
        try:
            filters = {'Key': 'tag_key'}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
            if ret.status_code == 200:
                known_error('', '')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_TXXX_with_empty_value(self):
        # call succeed
        try:
            filters = {'Key': 'tag_key', 'Value': ''}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
            if ret.status_code == 200:
                known_error('', '')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_TXXX_invalid_params(self):
        #call succeed
        try:
            filters = {'Key': 'tag_key', 'Value': 'tag_value', 'toto': 'toto'}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
            if ret.status_code == 200:
                known_error('', '')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_TXXX_without_lbu_name(self):
        #teardown issue
        try:
            filters = {'Key': 'tag_key', 'Value': 'tag_value'}
            self.a1_r1.lbu.AddTags(Tags=[filters])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_TXXX_with_one_tag_multiple_lbu(self):
        filters = {'Key': 'tag_key', 'Value': 'tag_value'}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0], self.lbu_names[1]], Tags=[filters])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_names[0], self.lbu_names[1]])
        assert len(ret.response.DescribeTagsResult.TagDescriptions) == 2
        i = 0
        for tag in ret.response.DescribeTagsResult.TagDescriptions:
            assert tag.LoadBalancerName == self.lbu_names[i]
            assert len(tag.Tags) == 1
            assert tag.Tags[0].Key == filters['Key']
            assert tag.Tags[0].Value == filters['Value']
            i += 1

    def test_TXXX_with_multiple_tag_one_lbu(self):
        filters = {'Key': 'tag_key1', 'Value': 'tag_value1'}
        filters2 = {'Key': 'tag_key2', 'Value': 'tag_value2'}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters, filters2])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_names[0]])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].LoadBalancerName == self.lbu_names[0]
        assert len(ret.response.DescribeTagsResult.TagDescriptions[0].Tags) == 2
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Key == filters['Key']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value == filters['Value']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[1].Key == filters2['Key']
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[1].Value == filters2['Value']

    def test_TXXX_with_multiple_tag_multiple_lbu(self):
        filters = {'Key': 'tag_key1', 'Value': 'tag_value1'}
        filter2 = {'Key': 'tag_key2', 'Value': 'tag_value2'}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0], self.lbu_names[1]], Tags=[filters, filter2])

    def test_TXXX_existed_tag(self):
        filters = {'Key': 'tag_key', 'Value': 'tag_value'}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
        filters2 = {'Key': 'tag_key', 'Value': 'tag_value2'}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters2])
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_names[0]])
        assert ret.response.DescribeTagsResult.TagDescriptions[0].Tags[0].Value == filters2['Value']

    def test_TXXX_from_another_account(self):
        try:
            filters = {'Key': 'tag_key', 'Value': 'tag_value'}
            self.a2_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_names[0]], Tags=[filters])
            assert False, "call should not have been successful, invalid param"
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', "The specified load balancer does not exists.")
