# -*- coding:utf-8 -*-

from qa_test_tools.misc import id_generator, assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_DeleteLoadBalancerTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteLoadBalancerTags, cls).setup_class()
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
            super(Test_DeleteLoadBalancerTags, cls).teardown_class()

    def test_T4714_missing_load_balancer_names(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(Tags=[{'Key': 'key1'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4715_missing_tags(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4716_incorrect_load_balancer_names(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=['_test_lbu'], Tags=[{'Key': 'key1'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)

    def test_T4717_incorrect_tags(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Toto': 'key1'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', 3001)

    def test_T4718_incorrect_tag_key(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': ''}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4108)

    def test_T4719_unknown_load_balancer_names(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=['test_lbu'], Tags=[{'Key': 'key1'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)

    def test_T4720_incorrect_load_balancer_names_type(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=self.ret_lbu_a1[0].LoadBalancerName, Tags=[{'Key': 'key1'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4721_incorrect_tags_type(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags={'Key': 'key1'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4722_incorrect_tag_key_type(self):
        try:
            self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': ['key1']}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4723_dry_run(self):
        ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key1'}], DryRun=True)
        assert_dry_run(ret)

    def setup_tags(self):
        self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName, self.ret_lbu_a1[1].LoadBalancerName],
                                               Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key2', 'Value': 'value2'}])
        self.a1_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key3', 'Value': 'value3'}])
        self.a2_r1.oapi.CreateLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a2[0].LoadBalancerName],
                                               Tags=[{'Key': 'key1', 'Value': 'value1'}, {'Key': 'key4', 'Value': 'value4'}])

    def check_tags(self, num_a1, num_a2):
        resp = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                       self.ret_lbu_a1[1].LoadBalancerName]).response
        assert num_a1 == 0 or (resp.Tags and len(resp.Tags) == num_a1)
        resp = self.a2_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a2[0].LoadBalancerName]).response
        assert num_a2 == 0 or (resp.Tags and len(resp.Tags) == num_a2)

    def teardown_tags(self):
        ret = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName, self.ret_lbu_a1[1].LoadBalancerName])
        self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName, self.ret_lbu_a1[1].LoadBalancerName],
                                               Tags=[{'Key': key} for key in set([tag.Key for tag in ret.response.Tags])])
        ret = self.a2_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a2[0].LoadBalancerName])
        self.a2_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a2[0].LoadBalancerName],
                                               Tags=[{'Key': key} for key in set([tag.Key for tag in ret.response.Tags])])

    def test_T4724_valid_params(self):
        try:
            self.setup_tags()
            ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key1'}])
            ret.check_response()
            resp = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert 'key1' not in [tag.Key for tag in resp.Tags]
            self.check_tags(4, 2)
        finally:
            self.teardown_tags()

    def test_T4725_multi_load_balancer_names(self):
        try:
            self.setup_tags()
            ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                             self.ret_lbu_a1[1].LoadBalancerName],
                                                          Tags=[{'Key': 'key1'}])
            ret.check_response()
            resp = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                           self.ret_lbu_a1[1].LoadBalancerName]).response
            assert 'key1' not in [tag.Key for tag in resp.Tags]
            self.check_tags(3, 2)
        finally:
            self.teardown_tags()

    def test_T4726_multi_tags(self):
        try:
            self.setup_tags()
            ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key1'}, {'Key': 'key3'}])
            ret.check_response()
            resp = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert 'key1' not in [tag.Key for tag in resp.Tags] and 'key3' not in [tag.Key for tag in resp.Tags]
            self.check_tags(3, 2)
        finally:
            self.teardown_tags()

    def test_T4727_multi_load_balancer_names_multi_tags(self):
        try:
            self.setup_tags()
            ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                             self.ret_lbu_a1[1].LoadBalancerName],
                                                          Tags=[{'Key': 'key1'}, {'Key': 'key3'}])
            ret.check_response()
            resp = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                           self.ret_lbu_a1[1].LoadBalancerName]).response
            assert 'key1' not in [tag.Key for tag in resp.Tags] and 'key3' not in [tag.Key for tag in resp.Tags]
            self.check_tags(2, 2)
        finally:
            self.teardown_tags()

    def test_T4728_duplicate_load_balancer_name(self):
        try:
            self.setup_tags()
            ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName,
                                                                             self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key1'}])
            ret.check_response()
            resp = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert 'key1' not in [tag.Key for tag in resp.Tags]
            self.check_tags(4, 2)
        finally:
            self.teardown_tags()

    def test_T4729_duplicate_key(self):
        try:
            self.setup_tags()
            ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName],
                                                          Tags=[{'Key': 'key1'}, {'Key': 'key1'}])
            ret.check_response()
            resp = self.a1_r1.oapi.ReadLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName]).response
            assert 'key1' not in [tag.Key for tag in resp.Tags]
            self.check_tags(4, 2)
        finally:
            self.teardown_tags()

    def test_T4736_unknown_tag_key(self):
        try:
            self.setup_tags()
            ret = self.a1_r1.oapi.DeleteLoadBalancerTags(LoadBalancerNames=[self.ret_lbu_a1[0].LoadBalancerName], Tags=[{'Key': 'key5'}])
            ret.check_response()
            self.check_tags(5, 2)
        finally:
            self.teardown_tags()
