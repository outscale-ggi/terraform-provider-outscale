# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error

from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form
from qa_test_tools.test_base import known_error


class Test_UpdateLoadBalancer(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateLoadBalancer, cls).setup_class()
        cls.lb_name = None
        cls.setup_error = False
        try:
            cls.lb_name = id_generator(prefix='lbu-')
            try:
                cls.a1_r1.oapi.CreateLoadBalancer(
                    Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                               {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                    LoadBalancerName=cls.lb_name, SubregionNames=[cls.a1_r1.config.region.az_name],
                )
                cls.policy_name_app = id_generator(prefix='policy-')
                cls.a1_r1.oapi.CreateLoadBalancerPolicy(
                    LoadBalancerName=cls.lb_name, PolicyName=cls.policy_name_app, PolicyType='app',
                    CookieName=id_generator(prefix='cookie-'))
                cls.policy_name_lb = id_generator(prefix='policy-')
                cls.a1_r1.oapi.CreateLoadBalancerPolicy(
                    LoadBalancerName=cls.lb_name, PolicyName=cls.policy_name_lb, PolicyType='load_balancer')
            except OscApiException as err:
                assert_oapi_error(err, 404, 'InvalidAction', 12000)
                cls.setup_error = True
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb_name:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=cls.lb_name)
                except:
                    pass
        finally:
            super(Test_UpdateLoadBalancer, cls).teardown_class()

    def test_T2852_missing_param(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer()
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(PolicyNames=[id_generator(prefix='policy-')])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(AccessLog={})
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(AccessLog={'OsuBucketPrefix': 'tata'})
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(ServerCertificateId='testid')
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerPort=12345)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerPort=12345, ServerCertificateId='testid')
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerPort=12345, PolicyNames=[id_generator(prefix='policy-')])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(HealthCheck={})
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2853_invalid_parameter_combinaison(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=12345,
                                               ServerCertificateId='testid',
                                               PolicyNames=[id_generator(prefix='policy-')])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(AccessLog={'OsuBucketPrefix': 'tata'}, LoadBalancerName=self.lb_name,
                                               LoadBalancerPort=12345, PolicyNames=[id_generator(prefix='policy-')])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(AccessLog={'OsuBucketPrefix': 'tata'}, LoadBalancerName=self.lb_name,
                                               LoadBalancerPort=12345, ServerCertificateId='testid')
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2854_app_policy_http(self):
        lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                                PolicyNames=[self.policy_name_app]).response.LoadBalancer
        validate_load_balancer_global_form(lb)

    def test_T2855_app_policy_tcp(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=1080,
                                               PolicyNames=[self.policy_name_lb])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9056')

    def test_T2856_lb_policy_http(self):
        self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                           PolicyNames=[self.policy_name_lb])

    def test_T2857_lb_policy_tcp(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=1080,
                                               PolicyNames=[self.policy_name_lb])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9056')

    def test_T2858_access_log_invalid_interval(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(
                AccessLog={
                    'IsEnabled': True,
                    'OsuBucketName': 'bucket',
                    'OsuBucketPrefix': 'prefix',
                    'PublicationInterval': 1,
                },
                LoadBalancerName=self.lb_name,
            )
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2859_access_log_missing_is_enabled(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(
                AccessLog={
                    'OsuBucketName': 'bucket',
                    'OsuBucketPrefix': 'prefix',
                    'PublicationInterval': 6,
                },
                LoadBalancerName=self.lb_name,
            )
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4088')

    # def test_valid_access_log(self):
    #     ## This test need osu_bucket
    #     self.a1_r1.oapi.UpdateLoadBalancer(
    #         AccessLog={
    #             'IsEnabled': True,
    #             'OsuBucketName': 'bucket',
    #             'OsuBucketPrefix': 'prefix',
    #             'PublicationInterval': 5,
    #         },
    #         LoadBalancerName=self.lb_name,
    #     )

    def test_T2860_with_invalid_server_certificate_id(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(
                LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                ServerCertificateId='testid'
            )
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5070')

    def test_T3145_invalid_lb_name(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName='tata',
                                               HealthCheck={
                                                   'CheckInterval': 15,
                                                   'HealthyThreshold': 10,
                                                   'Port': 80,
                                                   'Protocol': 'TCP',
                                                   'Timeout': 10,
                                                   'UnhealthyThreshold': 3,
                                               })
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5030')

    def test_T3146_empty_health_check(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, HealthCheck={})
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3147_invalid_health_check(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                               HealthCheck={
                                                   'CheckInterval': 15,
                                                   'HealthyThreshold': 10,
                                                   'Path': 'ABC',
                                                   'Port': 80,
                                                   'Protocol': 'TCP',
                                                   'Timeout': 10,
                                                   'UnhealthyThreshold': 15,
                                               })
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                               HealthCheck={
                                                   'CheckInterval': 15,
                                                   'HealthyThreshold': 10,
                                                   'Path': '/path',
                                                   'Port': 80,
                                                   'Protocol': 'TCP',
                                                   'Timeout': 10,
                                                   'UnhealthyThreshold': 3,
                                               })
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                               HealthCheck={
                                                   'CheckInterval': 15,
                                                   'HealthyThreshold': 10,
                                                   'Path': '',
                                                   'Port': 80,
                                                   'Protocol': 'TCP',
                                                   'Timeout': 10,
                                                   'UnhealthyThreshold': 3,
                                               })
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                               HealthCheck={
                                                   'CheckInterval': 15,
                                                   'HealthyThreshold': 10,
                                                   'Port': 800000,
                                                   'Protocol': 'TCP',
                                                   'Timeout': 10,
                                                   'UnhealthyThreshold': 3,
                                               })
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')

    def test_T2627_valid_health_check(self):
        ret = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 10,
                                                     'Port': 80,
                                                     'Protocol': 'TCP',
                                                     'Timeout': 10,
                                                     'UnhealthyThreshold': 3,
                                                 }).response.LoadBalancer
        validate_load_balancer_global_form(
            ret,
            hc={'CheckInterval': 15, 'HealthyThreshold': 10, 'Port': 80, 'Protocol': 'TCP', 'Timeout': 10,
                'UnhealthyThreshold': 3}
        )
        ret = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 30,
                                                     'HealthyThreshold': 10,
                                                     'Port': 65535,
                                                     'Protocol': 'TCP',
                                                     'Timeout': 5,
                                                     'UnhealthyThreshold': 2,
                                                 }).response.LoadBalancer
        validate_load_balancer_global_form(
            ret,
            hc={'CheckInterval': 30, 'HealthyThreshold': 10, 'Port': 65535, 'Protocol': 'TCP', 'Timeout': 5,
                'UnhealthyThreshold': 2}
        )
        ret = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 10,
                                                     'Path': '/path',
                                                     'Port': 80,
                                                     'Protocol': 'HTTP',
                                                     'Timeout': 7,
                                                     'UnhealthyThreshold': 3,
                                                 }).response.LoadBalancer
        validate_load_balancer_global_form(
            ret,
            hc={'CheckInterval': 15, 'HealthyThreshold': 10, 'Path': '/path', 'Port': 80, 'Protocol': 'HTTP',
                'Timeout': 7, 'UnhealthyThreshold': 3}
        )
        ret = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 5,
                                                     'Path': '/path',
                                                     'Port': 80,
                                                     'Protocol': 'HTTPS',
                                                     'Timeout': 10,
                                                     'UnhealthyThreshold': 7,
                                                 }).response.LoadBalancer
        validate_load_balancer_global_form(
            ret,
            hc={'CheckInterval': 15, 'HealthyThreshold': 5, 'Path': '/path', 'Port': 80, 'Protocol': 'HTTPS',
                'Timeout': 10, 'UnhealthyThreshold': 7}
        )
        ret = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 7,
                                                     'Path': '/',
                                                     'Port': 80,
                                                     'Protocol': 'HTTPS',
                                                     'Timeout': 15,
                                                     'UnhealthyThreshold': 3,
                                                 }).response.LoadBalancer
        validate_load_balancer_global_form(
            ret,
            hc={'CheckInterval': 15, 'HealthyThreshold': 7, 'Path': '/', 'Port': 80, 'Protocol': 'HTTPS',
                'Timeout': 15, 'UnhealthyThreshold': 3}
        )

    @pytest.mark.tag_sec_confidentiality
    def test_T3468_other_account(self):
        try:
            self.a2_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=[self.policy_name_lb])
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)

    def test_T4678_multi_lbu_same_name_diff_users(self):
        ret_create_lbu = None
        try:
            ret_create_lbu = self.a2_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=self.lb_name, SubregionNames=[self.a2_r1.config.region.az_name],
            )
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=[self.policy_name_lb])
        finally:
            if ret_create_lbu:
                try:
                    self.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=self.lb_name)
                except:
                    pass
