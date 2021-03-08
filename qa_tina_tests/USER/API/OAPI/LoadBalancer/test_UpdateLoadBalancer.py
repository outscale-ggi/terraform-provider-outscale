# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form


class Test_UpdateLoadBalancer(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateLoadBalancer, cls).setup_class()
        cls.lb_name = None
        try:
            cls.lb_name = id_generator(prefix='lbu-')
            cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=cls.lb_name, SubregionNames=[cls.a1_r1.config.region.az_name],
            )
            cls.policy_name_app = []
            cls.policy_name_lb = []
            for _ in range(3):
                name = id_generator(prefix='policy-')
                cls.policy_name_app.append(name)
                cls.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=cls.lb_name, PolicyName=name, PolicyType='app', CookieName=id_generator(prefix='cookie-'))
                name = id_generator(prefix='policy-')
                cls.policy_name_lb.append(name)
                cls.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=cls.lb_name, PolicyName=name, PolicyType='load_balancer')
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

    def empty_policies(self, port):
        lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=port, PolicyNames=[]).response.LoadBalancer
        validate_load_balancer_global_form(lb)
        for listener in lb.Listeners:
            if listener.LoadBalancerPort == port:
                assert not hasattr(listener, 'PolicyNames')
                break

    # http - app : 0 -> 1 -> 0
    def test_T5331_http_app_single_policy(self):
        lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_app[0:1]).response.LoadBalancer
        validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app[0:1]}])
        self.empty_policies(80)

    # http - app : 0 -> n -> 0
    def test_T5332_http_app_policy_multi(self):
        try:
            lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_app).response.LoadBalancer
            validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app}])
            self.empty_policies(80)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9034')

    # http - app : 0 -> n1 -> n2 -> 0
    def test_T5333_http_app_policy_mixed(self):
        try:
            lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_app[0:2]).response.LoadBalancer
            validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app[0:2]}])
            lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_app[1:3]).response.LoadBalancer
            validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app[1:3]}])
            self.empty_policies(80)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9034')

    # http - lb : 0 -> 1 -> 0
    def test_T5334_http_lb_policy_single(self):
        lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_lb[0:1]).response.LoadBalancer
        validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb[0:1]}])
        self.empty_policies(80)

    # http - lb : 0 -> n -> 0
    def test_T5335_http_lb_policy_multi(self):
        try:
            lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_lb).response.LoadBalancer
            validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb}])
            self.empty_policies(80)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9035')

    # http - lb : 0 -> n1 -> n2 -> 0
    def test_T5336_http_lb_policy_mixed(self):
        try:
            lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_lb[0:2]).response.LoadBalancer
            validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb[0:2]}])
            lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_lb[1:3]).response.LoadBalancer
            validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb[1:3]}])
            self.empty_policies(80)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9035')

    # http - lb, app
    def test_T5337_http_app_lb_same_listener(self):
        try:
            lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=[self.policy_name_lb[0], self.policy_name_app[0]]).response.LoadBalancer
            validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': [self.policy_name_lb[0], self.policy_name_app[0]]}])
            self.empty_policies(80)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9036')

    # ftp - lb : 0 -> n
    def test_T5338_ftp_lb_policy(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=1080, PolicyNames=self.policy_name_lb)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9056')

    # ftp - app : 0 -> n
    def test_T5339_ftp_app_policy(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=1080, PolicyNames=self.policy_name_app)
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
                                                     'Port': 80,
                                                     'Protocol': 'HTTPS',
                                                     'Timeout': 15,
                                                     'UnhealthyThreshold': 3,
                                                 }).response.LoadBalancer
        validate_load_balancer_global_form(
            ret,
            hc={'CheckInterval': 15, 'HealthyThreshold': 7, 'Port': 80, 'Protocol': 'HTTPS',
                'Timeout': 15, 'UnhealthyThreshold': 3, 'Path': '/'}
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
            self.a2_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_lb[0:1])
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
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_lb[0:1])
        finally:
            if ret_create_lbu:
                try:
                    self.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=self.lb_name)
                except:
                    pass
