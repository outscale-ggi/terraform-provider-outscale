

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite


class Test_ReadLoadBalancerTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadLoadBalancerTags, cls).setup_class()
        cls.ret_lbu_a1 = []
        cls.ret_lbu_a2 = []
        listeners = [{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}]
        try:
            cls.ret_lbu_a1.append(cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=listeners, LoadBalancerName=id_generator(prefix='lbu-'),
                SubregionNames=[cls.a1_r1.config.region.az_name]).response.LoadBalancer)
            cls.ret_lbu_a1.append(cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=listeners, LoadBalancerName=id_generator(prefix='lbu-'),
                SubregionNames=[cls.a1_r1.config.region.az_name]).response.LoadBalancer)

            cls.ret_lbu_a2.append(cls.a2_r1.oapi.CreateLoadBalancer(
                Listeners=listeners, LoadBalancerName=id_generator(prefix='lbu-'),
                SubregionNames=[cls.a2_r1.config.region.az_name]).response.LoadBalancer)

            # create tags
            cls.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[cls.ret_lbu_a1[0].LoadBalancerName, cls.ret_lbu_a1[1].LoadBalancerName],
                                                  Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key2', 'Value': 'value2'}])
            cls.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[cls.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key3', 'Value': 'value3'}])
            cls.a2_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[cls.ret_lbu_a2[0].LoadBalancerName],
                                                  Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key4', 'Value': 'value4'}])

        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for ret_lbu in cls.ret_lbu_a1:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=ret_lbu.LoadBalancerName)
                except:
                    print('Could not delete lbu')
            for ret_lbu in cls.ret_lbu_a2:
                try:
                    cls.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=ret_lbu.LoadBalancerName)
                except:
                    print('Could not delete lbu')
        finally:
            super(Test_ReadLoadBalancerTags, cls).teardown_class()

    def test_T4730_missing_load_balancer_names(self):
        try:
            self.a1_r1.oapi.ReadLoadBalancerTags()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4731_incorrect_load_balancer_names(self):
        try:
            self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=['_test_lbu'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)

    def test_T4732_unknown_load_balancer_names(self):
        try:
            self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=['test_lbu'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)

    def test_T4733_incorrect_load_balancer_names_type(self):
        try:
            self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=self.ret_lbu_a1[0].LoadBalancerName)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    @pytest.mark.tag_sec_confidentiality
    def test_T4734_valid_params(self):
        ret = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName])
        ret.check_response()
        assert ret.response.Tags and len(ret.response.Tags) == 3

    @pytest.mark.tag_sec_confidentiality
    def test_T4735_multi_load_balancer_names(self):
        ret = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                       self.ret_lbu_a1[1].LoadBalancerName])
        ret.check_response()
        assert ret.response.Tags and len(ret.response.Tags) == 5
