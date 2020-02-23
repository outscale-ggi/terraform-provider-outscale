# -*- coding:utf-8 -*-

from qa_common_tools.misc import id_generator, assert_oapi_error, assert_dry_run
from qa_common_tools.test_base import OscTestSuite, known_error
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response
import string


class Test_CreateLoadBalancerTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateLoadBalancerTags, cls).setup_class()
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

        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            for ret_lbu in cls.ret_lbu_a1:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=ret_lbu.LoadBalancerName)
                except:
                    pass
            for ret_lbu in cls.ret_lbu_a2:
                try:
                    cls.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=ret_lbu.LoadBalancerName)
                except:
                    pass
        finally:
            super(Test_CreateLoadBalancerTags, cls).teardown_class()

    def test_T4692_missing_load_balancer_names(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4693_missing_tags(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4694_missing_tag_key(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                   Tags=[{'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4069)

    def test_T4695_missing_tag_value(self):
        create_lbu_tags_resp = None
        try:
            create_lbu_tags_resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                                          Tags=[{'Key': 'key'}]).response
        finally:
            if create_lbu_tags_resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                       Tags=[{'Key': 'key'}])

    def test_T4696_empty_tag_key(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                   Tags=[{'Key': '', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4069)

    def test_T4697_empty_tag_value(self):
        create_lbu_tags_resp = None
        try:
            create_lbu_tags_resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                                          Tags=[{'Key': 'key', 'Value': ''}])
        finally:
            if create_lbu_tags_resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key'}])

    def test_T4698_incorrect_load_balancer_names(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=["_test"],
                                                   Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)

    def test_T4699_incorrect_tag_key(self):
        create_lbu_tags_resp = None
        incorrect_key = id_generator(chars=string.ascii_lowercase, size=300)
        try:
            create_lbu_tags_resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                                          Tags=[{'Key': incorrect_key, 'Value': 'value'}]).response
            known_error('GTW-1129', 'No error is for incorrect tag key value')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error'
            assert_oapi_error(error, 400, '', 0)
        finally:
            if create_lbu_tags_resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': incorrect_key}])

    def test_T4700_incorrect_tag_value(self):
        create_lbu_tags_resp = None
        try:
            create_lbu_tags_resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                                          Tags=[{'Value': id_generator(chars=string.ascii_lowercase, size=300),
                                                                                 'Key': 'key'}]).response
            known_error('GTW-1129', 'No error is for incorrect tag value value')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error'
            assert_oapi_error(error, 400, '', 0)
        finally:
            if create_lbu_tags_resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key'}])

    def test_T4701_unknown_load_balancer_names(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=['Test_lbu'],
                                                   Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)

    def test_T4702_incorrect_load_balancer_names_type(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=self.ret_lbu_a1[0].LoadBalancerName,
                                                   Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4703_incorrect_tags_type(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                   Tags={'Key': 'key', 'Value': 'value'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4704_incorrect_tag_key_type(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                   Tags={'Key': ['key'], 'Value': 'value'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4705_incorrect_tag_value_type(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames='Test_lbu',
                                                   Tags={'Key': 'key', 'Value': ['value']})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4706_dry_run(self):
        dr_ret = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                        Tags=[{'Key': 'key', 'Value': 'value'}])
        assert_dry_run(dr_ret)

    def test_T4707_valid_params(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key', 'Value': 'value'}]).response
            check_oapi_response(resp, 'CreateLoadBalancerTagsResponse')
            read = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert read.Tags and len(read.Tags) == 1
        finally:
            if resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key'}])

    def test_T4708_multi_load_balancer_names(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                             self.ret_lbu_a1[1].LoadBalancerName],
                                                          Tags=[{'Key': 'key', 'Value': 'value'}]).response
            check_oapi_response(resp, 'CreateLoadBalancerTagsResponse')
            read = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                           self.ret_lbu_a1[1].LoadBalancerName]).response
            assert read.Tags and len(read.Tags) == 2
        finally:
            if resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName, self.ret_lbu_a1[1].LoadBalancerName],
                                                       Tags=[{'Key': 'key'}])

    def test_T4709_multi_tags(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key2', 'Value': 'value2'}]).response
            check_oapi_response(resp, 'CreateLoadBalancerTagsResponse')
            read = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert read.Tags and len(read.Tags) == 2
        finally:
            if resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                       Tags=[{'Key': 'key1'}, {'Key': 'key2'}])

    def test_T4710_multi_load_balancer_names_multi_tags(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                             self.ret_lbu_a1[1].LoadBalancerName],
                                                          Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key2', 'Value': 'value2'}]).response
            check_oapi_response(resp, 'CreateLoadBalancerTagsResponse')
            read = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                           self.ret_lbu_a1[1].LoadBalancerName]).response
            assert read.Tags and len(read.Tags) == 4
        finally:
            if resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName, self.ret_lbu_a1[1].LoadBalancerName],
                                                       Tags=[{'Key': 'key1'}, {'Key': 'key2'}])

    def test_T4711_duplicate_loadbalancer_name(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                             self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key', 'Value': 'value'}]).response
            check_oapi_response(resp, 'CreateLoadBalancerTagsResponse')
            read = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert read.Tags and len(read.Tags) == 1
        finally:
            if resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key'}])

    def test_T4712_duplicate_key_same_value(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key1', 'Value': 'value1'}]).response
            check_oapi_response(resp, 'CreateLoadBalancerTagsResponse')
            read = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert read.Tags and len(read.Tags) == 1
        finally:
            if resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key1'}])

    def test_T4713_duplicate_key_diff_value(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key1', 'Value': 'value2'}]).response
            check_oapi_response(resp, 'CreateLoadBalancerTagsResponse')
            read = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert read.Tags and len(read.Tags) == 1
        finally:
            if resp:
                self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key1'}])
