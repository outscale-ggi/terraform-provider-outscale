
import os

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_test_tools.compare_objects import create_hints, verify_response
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer


class Test_UpdateLoadBalancer(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateLoadBalancer, cls).setup_class()
        cls.lb_name = None
        cls.sg_ids = []
        try:
            cls.lb_name = id_generator(prefix='lbu-')
            resp_create_lb = cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=cls.lb_name, SubregionNames=[cls.a1_r1.config.region.az_name],
            ).response
            cls.policy_name_app = []
            cls.policy_name_lb = []
            for _ in range(3):
                name = id_generator(prefix='policy-')
                cls.policy_name_app.append(name)
                cookie_name = id_generator(prefix='cookie-')
                cls.hint_values.append(cookie_name)
                cls.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=cls.lb_name, PolicyName=name, PolicyType='app', CookieName=cookie_name)
                name = id_generator(prefix='policy-')
                cls.policy_name_lb.append(name)
                cls.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=cls.lb_name, PolicyName=name, PolicyType='load_balancer')
            for _ in range(3):
                cls.sg_ids.append(cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test',
                                                                    GroupName=id_generator(prefix='sg_name-')).response.groupId)

            cls.hint_values.append(cls.lb_name)
            cls.hint_values.append(resp_create_lb.LoadBalancer.DnsName)
            cls.hint_values.extend(cls.policy_name_app)
            cls.hint_values.extend(cls.policy_name_lb)
            cls.hint_values.extend(cls.sg_ids)
            cls.hints = create_hints(cls.hint_values)
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb_name:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=cls.lb_name)
                except Exception as error:
                    raise error
            for sg_id in cls.sg_ids:
                cls.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg_id)
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
        # validate_load_balancer_global_form(lb)
        for listener in lb.Listeners:
            if listener.LoadBalancerPort == port:
                assert not hasattr(listener, 'PolicyNames')
                break

    # http - app : 0 -> 1 -> 0
    def test_T5331_http_app_single_policy(self):
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                                 PolicyNames=self.policy_name_app[0:1]).response
        self.empty_policies(80)
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_http_app_single_policy.json'), self.hints)
        # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app[0:1]}])

    # http - app : 0 -> n -> 0
    def test_T5332_http_app_policy_multi(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                               PolicyNames=self.policy_name_app)
            # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app}])
            self.empty_policies(80)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9034')

    # http - app : 0 -> n1 -> n2 -> 0
    def test_T5333_http_app_policy_mixed(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                               PolicyNames=self.policy_name_app[0:2])
            # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app[0:2]}])
            # verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_http_app_policy_mixed.json'), self.hints)
            # resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
            #                                           PolicyNames=self.policy_name_app[1:3]).response
            # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_app[1:3]}])
            self.empty_policies(80)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9034')

    # http - lb : 0 -> 1 -> 0
    def test_T5334_http_lb_policy_single(self):
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                                  PolicyNames=self.policy_name_lb[0:1]).response
        # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb[0:1]}])
        self.empty_policies(80)
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_http_lb_policy_single.json'), self.hints)

    # http - lb : 0 -> n -> 0
    def test_T5335_http_lb_policy_multi(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                               PolicyNames=self.policy_name_lb)
            # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb}])
            self.empty_policies(80)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9035')

    # http - lb : 0 -> n1 -> n2 -> 0
    def test_T5336_http_lb_policy_mixed(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                                     PolicyNames=self.policy_name_lb[0:2])
            # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb[0:2]}])
            # lb = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
            #                                         PolicyNames=self.policy_name_lb[1:3]).response.LoadBalancer
            # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': self.policy_name_lb[1:3]}])
            self.empty_policies(80)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9035')

    # http - lb, app
    def test_T5337_http_app_lb_same_listener(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                               PolicyNames=[self.policy_name_lb[0], self.policy_name_app[0]])
            # validate_load_balancer_global_form(lb, lst=[{'LoadBalancerPort': 80, 'PolicyNames': [self.policy_name_lb[0], self.policy_name_app[0]]}])
            self.empty_policies(80)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9036')

    # ftp - lb : 0 -> n
    def test_T5338_ftp_lb_policy(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=1080, PolicyNames=self.policy_name_lb)
            self.empty_policies(1080)
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9056')

    # ftp - app : 0 -> n
    def test_T5339_ftp_app_policy(self):
        try:
            self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=1080, PolicyNames=self.policy_name_app)
            self.empty_policies(1080)
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
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 10,
                                                     'Port': 80,
                                                     'Protocol': 'TCP',
                                                     'Timeout': 10,
                                                     'UnhealthyThreshold': 3,
                                                 }).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_valid_heath_check_1.json'), self.hints)
#         validate_load_balancer_global_form(
#             ret,
#             hc={'CheckInterval': 15, 'HealthyThreshold': 10, 'Port': 80, 'Protocol': 'TCP', 'Timeout': 10,
#                 'UnhealthyThreshold': 3}
#         )
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 30,
                                                     'HealthyThreshold': 10,
                                                     'Port': 65535,
                                                     'Protocol': 'TCP',
                                                     'Timeout': 5,
                                                     'UnhealthyThreshold': 2,
                                                 }).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_valid_heath_check_2.json'), self.hints)
#         validate_load_balancer_global_form(
#             ret,
#             hc={'CheckInterval': 30, 'HealthyThreshold': 10, 'Port': 65535, 'Protocol': 'TCP', 'Timeout': 5,
#                 'UnhealthyThreshold': 2}
#         )
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 10,
                                                     'Path': '/path',
                                                     'Port': 80,
                                                     'Protocol': 'HTTP',
                                                     'Timeout': 7,
                                                     'UnhealthyThreshold': 3,
                                                 }).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_valid_heath_check_3.json'), self.hints)
#         validate_load_balancer_global_form(
#             ret,
#             hc={'CheckInterval': 15, 'HealthyThreshold': 10, 'Path': '/path', 'Port': 80, 'Protocol': 'HTTP',
#                 'Timeout': 7, 'UnhealthyThreshold': 3}
#         )
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 5,
                                                     'Path': '/path',
                                                     'Port': 80,
                                                     'Protocol': 'HTTPS',
                                                     'Timeout': 10,
                                                     'UnhealthyThreshold': 7,
                                                 }).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_valid_heath_check_4.json'), self.hints)
#         validate_load_balancer_global_form(
#             ret,
#             hc={'CheckInterval': 15, 'HealthyThreshold': 5, 'Path': '/path', 'Port': 80, 'Protocol': 'HTTPS',
#                 'Timeout': 10, 'UnhealthyThreshold': 7}
#         )
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 7,
                                                     'Port': 80,
                                                     'Protocol': 'HTTPS',
                                                     'Timeout': 15,
                                                     'UnhealthyThreshold': 3,
                                                 }).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_valid_heath_check_5.json'), self.hints)
#         validate_load_balancer_global_form(
#             ret,
#             hc={'CheckInterval': 15, 'HealthyThreshold': 7, 'Port': 80, 'Protocol': 'HTTPS',
#                 'Timeout': 15, 'UnhealthyThreshold': 3, 'Path': '/'}
#         )
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name,
                                                 HealthCheck={
                                                     'CheckInterval': 15,
                                                     'HealthyThreshold': 7,
                                                     'Path': '/',
                                                     'Port': 80,
                                                     'Protocol': 'HTTPS',
                                                     'Timeout': 15,
                                                     'UnhealthyThreshold': 3,
                                                 }).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_valid_heath_check_6.json'), self.hints)
#         validate_load_balancer_global_form(
#             ret,
#             hc={'CheckInterval': 15, 'HealthyThreshold': 7, 'Path': '/', 'Port': 80, 'Protocol': 'HTTPS',
#                 'Timeout': 15, 'UnhealthyThreshold': 3}
#         )

    @pytest.mark.tag_sec_confidentiality
    def test_T3468_other_account(self):
        try:
            self.a2_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80, PolicyNames=self.policy_name_lb[0:1])
            assert False, "call should not have been successful"
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
            resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, LoadBalancerPort=80,
                                                      PolicyNames=self.policy_name_lb[0:1]).response
            verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_multi_lbu_same_name_diff_users.json'), self.hints)
        finally:
            if ret_create_lbu:
                try:
                    self.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=self.lb_name)
                except Exception as error:
                    raise error

    def test_T5556_single_sg_sgroup(self):
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, SecurityGroups=[self.sg_id[0]]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_single_sg_sgroup.json'), self.hints)
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, SecurityGroups=[]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_rmpty_sg_sgroup.json'), self.hints)

    def test_T5557_multi_sg_sgroup(self):
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, SecurityGroups=self.sg_id[1:2]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_multi_sg_sgroup.json'), self.hints)
        resp = self.a1_r1.oapi.UpdateLoadBalancer(LoadBalancerName=self.lb_name, SecurityGroups=[]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_rmpty_sg_sgroup.json'), self.hints)
