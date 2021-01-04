from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_DescribeTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeTags, cls).setup_class()
        cls.ret1 = None
        cls.ret2 = None
        cls.lbu_names = []
        cls.filters_list = []
        try:
            name = id_generator(prefix='lbu-')
            cls.ret1 = create_load_balancer(cls.a1_r1, lb_name=name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
            cls.lbu_names.append(name)
            filters = {'Key': id_generator("tagkey-11-"), 'Value': id_generator("tagvalue-11-")}
            cls.filters_list.append(filters)
            cls.a1_r1.lbu.AddTags(LoadBalancerNames=[cls.lbu_names[0]], Tags=[cls.filters_list[0]])

            name = id_generator(prefix='lbu-')
            cls.ret2 = create_load_balancer(cls.a1_r1, lb_name=name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
            cls.lbu_names.append(name)
            filters = {'Key': id_generator("tagkey-21-"), 'Value': id_generator("tagvalue-21-")}
            cls.filters_list.append(filters)
            filters = {'Key': id_generator("tagkey-22-"), 'Value': id_generator("tagvalue-22-")}
            cls.filters_list.append(filters)
            cls.a1_r1.lbu.AddTags(LoadBalancerNames=[cls.lbu_names[1]], Tags=[cls.filters_list[1], cls.filters_list[2]])

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret1 or cls.ret2:
                # I KNOW, IT HURTS ON THE EYE! MAIS C'EST COMME ÇA
                sleep(60)
                delete_lbu(cls.a1_r1, cls.lbu_names[0])
                delete_lbu(cls.a1_r1, cls.lbu_names[1])
        finally:
            super(Test_DescribeTags, cls).teardown_class()

    def test_T5392_without_params(self):
        try:
            self.a1_r1.lbu.DescribeTags()
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5393_valid_params(self):
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_names[0]]).response.DescribeTagsResult
        assert ret.TagDescriptions[0].LoadBalancerName == self.lbu_names[0]
        assert len(ret.TagDescriptions[0].Tags) == 1
        assert ret.TagDescriptions[0].Tags[0].Key == self.filters_list[0]['Key']
        assert ret.TagDescriptions[0].Tags[0].Value == self.filters_list[0]['Value']
        ret = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_names[1]]).response.DescribeTagsResult
        assert len(ret.TagDescriptions[0].Tags) == 2
        assert ret.TagDescriptions[0].Tags[0].Key == self.filters_list[2]['Key']
        assert ret.TagDescriptions[0].Tags[0].Value == self.filters_list[2]['Value']
        assert ret.TagDescriptions[0].Tags[1].Key == self.filters_list[1]['Key']
        assert ret.TagDescriptions[0].Tags[1].Value == self.filters_list[1]['Value']

    def test_T5394_with_empty_lbu_name(self):
        try:
            self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5395_with_invalid_lbu_name(self):
        try:
            self.a1_r1.lbu.DescribeTags(LoadBalancerNames=self.lbu_names[0])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'OWS.Error', 'Request is not valid.')

    def test_T5396_with_incorrect_lbu_name(self):
        try:
            self.a1_r1.lbu.DescribeTags(LoadBalancerNames=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', 'The specified load balancer does not exists.')

    def test_T5397_from_another_account(self):
        try:
            self.a2_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_names[0]])
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', "The specified load balancer does not exists.")
