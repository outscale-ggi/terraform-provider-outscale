# -*- coding:utf-8 -*-

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_oapi_error
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form
import pytest
from qa_tina_tools.constants import TWO_REGIONS_NEEDED
from qa_test_tools.test_base import known_error


class Test_CreateLoadBalancer(LoadBalancer):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'lb_limit': 20}
        super(Test_CreateLoadBalancer, cls).setup_class()

    def setup_method(self, method):
        super(Test_CreateLoadBalancer, self).setup_method(method)
        self.lb_names = []

    def teardown_method(self, method):
        try:
            for lb_name in self.lb_names:
                try:
                    self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=lb_name)
                except:
                    pass
        finally:
            super(Test_CreateLoadBalancer, self).teardown_method(method)

    def test_T2580_empty_param(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancer()
            assert False, "Call should not have been successful, request must contain LoadBalancerName"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2581_with_invalid_load_balancer_name(self):
        try:
            name = 'totototototototototototototototototototo'
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid LoadBalancerName"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4036')
        try:
            name = 'lbu_-1'
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid LoadBalancerName"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4036')

        char_list = "!\"#$%&'()*/:;<>?[\\]^`{|}~"
        for char in char_list:
            ret = None
            try:
                group_name = id_generator(prefix='group_{}_'.format(char))
                ret = self.a1_r1.oapi.CreateLoadBalancer(
                    Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                    LoadBalancerName=group_name, SubregionNames=[self.a1_r1.config.region.az_name])
                assert False, "Creategroup must fail with invalid groupName"
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4036')
            finally:
                if ret:
                    self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=group_name)


    def test_T2582_with_empty_listener(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain Listener param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2583_with_invalid_listener(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 0, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65536, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 1, 'LoadBalancerProtocol': 'toto', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 1, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 65536}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4037')

    def test_T2584_with_invalid_sub_region_names(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name)
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=['toto'])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name,
                                                       self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8010')

    def test_T2585_with_invalid_security_group(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                SecurityGroups=['toto'],
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal', Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid security group param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                SecurityGroups=[self.sg_id, 'toto'],
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal',
                Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid security group param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{"BackendPort": 65535, "BackendProtocol":"HTTP", 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid security group param"
        except OscApiException as error:
            if error.status_code == 400 and error.message == 'InvalidParameter':
                known_error("GTW-1170", '"InvalidParameter" Response when trying to create Load Balancer')
            assert False, "Remove known error code"
            
    def test_T2586_with_invalid_load_balancer_type(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                SecurityGroups=['sg1'],
                Listeners=[{'BackendPort': 1, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 65535}],
                LoadBalancerName=name, LoadBalancerType='toto', SubregionNames=[self.a1_r1.config.region.az_name],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid load_balancer_type param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2587_with_invalid_subnet(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal', SecurityGroups=[self.sg_id], Subnets=['toto'],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid subnet param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal', SecurityGroups=[self.sg_id],
                Subnets=[self.subnet_id, 'toto'],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid subnet param"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8010')
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal', SecurityGroups=[self.sg_id],
                Subnets=[self.subnet_id, self.subnet_id2],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain only 1 subnet"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8010')

    def test_T2588_with_existing_name_diff_param(self):
        name = id_generator(prefix='lbu-')
        self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
            LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
        )
        self.lb_names.append(name)

        try:
            assert self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65534, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9013')

    def test_T2589_with_existing_name_same_param(self):
        name = id_generator(prefix='lbu-')
        assert self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
            LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
        )
        self.lb_names.append(name)
        try:
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
            )
            assert False, "Call should not have been successful, same name and same params"
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9013')

    def test_T2590_with_valid_listener(self):
        name = id_generator(prefix='lbu-')
        try:
            ret = self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
            ).response.LoadBalancer
            validate_load_balancer_global_form(
                ret,
                name=name,
                lst=[{'BackendPort': 65535, 'BackendProtocol': 'HTTP', 'LoadBalancerPort': 80,
                      'LoadBalancerProtocol': 'HTTP'}],
            )
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)

            name = id_generator(prefix='lbu-')
            ret = self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[
                    {'BackendPort': 1, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 25,
                     'BackendProtocol': 'HTTP'}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
            ).response.LoadBalancer
            validate_load_balancer_global_form(
                ret,
                name=name,
                lst=[{'BackendPort': 1, 'BackendProtocol': 'HTTP', 'LoadBalancerPort': 25,
                      'LoadBalancerProtocol': 'HTTP'}],
            )
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)

            name = id_generator(prefix='lbu-')
            ret = self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 1, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1,
                            'BackendProtocol': 'TCP'}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
            ).response.LoadBalancer
            validate_load_balancer_global_form(
                ret,
                name=name,
                lst=[{'BackendPort': 1, 'BackendProtocol': 'TCP', 'LoadBalancerPort': 1,
                      'LoadBalancerProtocol': 'TCP'}],
            )
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)

            name = id_generator(prefix='lbu-')
            ret = self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 1, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1023,
                            'BackendProtocol': 'TCP'}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
            ).response.LoadBalancer
            validate_load_balancer_global_form(
                ret,
                name=name,
                lst=[{'BackendPort': 1, 'BackendProtocol': 'TCP', 'LoadBalancerPort': 1023,
                      'LoadBalancerProtocol': 'TCP'}],
            )
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)

            name = id_generator(prefix='lbu-')
            ret = self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1024,
                            'BackendProtocol': 'TCP'}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
            ).response.LoadBalancer
            validate_load_balancer_global_form(
                ret,
                name=name,
                lst=[{'BackendPort': 80, 'BackendProtocol': 'TCP', 'LoadBalancerPort': 1024,
                      'LoadBalancerProtocol': 'TCP'}],
            )
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
        except OscApiException as error:
            assert_oapi_error(error, 400, '', '')

    def test_T2591_with_valid_security_group(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            SecurityGroups=[self.sg_id, self.sg_id_2],
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internal', Subnets=[self.subnet_id],
        ).response.LoadBalancer
        assert len(ret.SecurityGroups) == 2
        for x in ret.SecurityGroups:
            assert x in [self.sg_id, self.sg_id_2]
        assert ret.Subnets == [self.subnet_id]
        self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)

        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            SecurityGroups=[self.sg_id],
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internal',
            Subnets=[self.subnet_id],
        ).response.LoadBalancer
        assert ret.SecurityGroups == [self.sg_id]
        self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)

    def test_T2592_with_valid_subnet(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internal', SecurityGroups=[self.sg_id], Subnets=[self.subnet_id],
        ).response.LoadBalancer
        self.lb_names.append(name)
        validate_load_balancer_global_form(
            ret,
            name=name,
            subnet_id=self.subnet_id,
        )

    def test_T2593_with_valid_load_balancer_type(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internet-facing', SecurityGroups=[self.sg_id],
            Subnets=[self.subnet_id],
        ).response.LoadBalancer
        self.lb_names.append(name)
        validate_load_balancer_global_form(
            ret,
            lb_type='internet-facing',
            name=name,
        )

    def test_T2594_with_all_param_valid(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internal', SecurityGroups=[self.sg_id],
            Subnets=[self.subnet_id], Tags=[{'Key': 'tag_key', 'Value': 'tag_value'}],
        ).response.LoadBalancer
        self.lb_names.append(name)
        validate_load_balancer_global_form(
            ret,
            access_log={'IsEnabled': False, 'PublicationInterval': 60},
            lb_type='internal',
            name=name,
            tags=[('tag_key', 'tag_value')],
            hc={'CheckInterval': 30, 'HealthyThreshold': 10, 'Port': 80, 'Protocol': 'TCP',
                'Timeout': 5, 'UnhealthyThreshold': 2},
            dns_name='.outscale.com',
            lst=[
                {'BackendPort': 80, 'BackendProtocol': 'HTTP', 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            subnet_id=self.subnet_id,
            net_id=self.vpc_id,
            az=self.a1_r1.config.region.az_name,
        )

    def test_T2595_private_internal_with_wrong_security_group(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal', SecurityGroups=[self.sg_id_3],
                Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, security group not in vpc"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5020')

    def test_T2596_name_starting_with_dash(self):
        try:
            name = '-T1413'
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal',
                SecurityGroups=[self.sg_id], Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, lbu name starts with '-'"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4036')

    def test_T2597_name_ending_with_dash(self):
        try:
            name = 'T1544-'
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal',
                SecurityGroups=[self.sg_id], Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, lbu name ends with '-'"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4036')

    def test_T2598_private_internal_without_security_group(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal', Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, missing security group for private internal lbu"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2599_private_internal_with_security_group(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internal',
            SecurityGroups=[self.sg_id], Subnets=[self.subnet_id],
        ).response.LoadBalancer
        self.lb_names.append(name)
        validate_load_balancer_global_form(
            ret,
            lb_type='internal',
            name=name,
            subnet_id=self.subnet_id,
            sg_id=self.sg_id
        )

    def test_T2600_private_without_security_group(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, Subnets=[self.subnet_id],
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, missing security group for private internet lbu"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2601_private_with_security_group(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, SecurityGroups=[self.sg_id], Subnets=[self.subnet_id],
        ).response.LoadBalancer
        self.lb_names.append(name)
        validate_load_balancer_global_form(
            ret,
            name=name,
            subnet_id=self.subnet_id,
            sg_id=self.sg_id
        )

    def test_T2602_public_with_security_group(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, SecurityGroups=[self.sg_id], SubregionNames=[self.a1_r1.config.region.az_name]
            )
            self.lb_names.append(name)
            assert False, "Call should not have been successful, public can't have security group"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4095')

    def test_T4159_public_other_sub_region(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r2.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as error:
            assert_oapi_error(error, 400, '', '')

    def test_T4160_private_with_incompatible_subnet_and_subregion(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, SecurityGroups=[self.sg_id], Subnets=[self.subnet_id], SubregionNames=[self.a1_r2.config.region.az_name]
            ).response.LoadBalancer
            self.lb_names.append(name)
            assert False, "Call should not have been successful, subregion and subnet are incompatible"
        except OscApiException as error:
            assert_oapi_error(error, 400, '', '')

    def test_T4738_multi_lbu_same_name_diff_users(self):
        ret_create_lbu1 = None 
        ret_create_lbu2 = None
        name = id_generator(prefix='lbu-')
        try:
            ret_create_lbu1 = self.a2_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=name, SubregionNames=[self.a2_r1.config.region.az_name],
            )
            ret_create_lbu2 = self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name],
        )
        finally:
            if ret_create_lbu1:
                try:
                    self.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
                except:
                    pass
            if ret_create_lbu2:
                try:
                    self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
                except:
                    pass
