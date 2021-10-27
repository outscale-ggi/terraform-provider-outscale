import os
import time
from time import sleep
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run
from qa_test_tools.compare_objects import verify_response, create_hints
from qa_test_tools.test_base import known_error
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_load_balancers
from qa_tina_tools.constants import TWO_REGIONS_NEEDED
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_lbu
from qa_tina_tools.tina import oapi, info_keys
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form
from specs import check_oapi_error


class Test_CreateLoadBalancer(LoadBalancer):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'lb_limit': 20}
        cls.lb_names = None
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
                    print('Could not delete lbu')

        finally:
            super(Test_CreateLoadBalancer, self).teardown_method(method)

    def test_T2580_empty_param(self):
        try:
            self.a1_r1.oapi.CreateLoadBalancer()
            assert False, "Call should not have been successful, request must contain LoadBalancerName"
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2581_with_invalid_load_balancer_name(self):
        try:
            name = 'totototototototototototototototototototo'
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid LoadBalancerName"
        except OscApiException as error:
            if error.data != 'The length of the provided value for parameter \'{param}\' is invalid: \'{vlength}\'. ' \
                             'The expected length is \'{length}\'.':
                assert False, 'remove known error'
                check_oapi_error(error, 4106, param=name, vlength=len(name), length='32')
            known_error('API-355', 'Incorrect error formatting (LoadBalancer)')
        try:
            name = 'lbu_-1'
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid LoadBalancerName"
        except OscApiException as error:
            check_oapi_error(error, 4036)

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
                check_oapi_error(error, 4036)
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
            check_oapi_error(error, 7000)

    def test_T2583_with_invalid_listener(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 0, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            check_oapi_error(error, 4095)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65536, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            check_oapi_error(error, 4095)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 1, 'LoadBalancerProtocol': 'toto', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            check_oapi_error(error, 4095)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 1, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 65536}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid Listener param"
        except OscApiException as error:
            check_oapi_error(error, 4037)

    def test_T2584_with_invalid_sub_region_names(self):
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name)
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=['toto'])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as error:
            check_oapi_error(error, 4095)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name,
                                                       self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid availabilityZone"
        except OscApiException as error:
            check_oapi_error(error, 8010)

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
            if error.data != 'The provided value \'{invalid}\' does not respect the expected ID prefix \'{prefixes}\'.':
                assert False, 'remove known error'
                check_oapi_error(error, 4104, invalid='toto', prefixes='sg-')
            known_error('API-355', 'Incorrect error formatting (LoadBalancer)')
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
            if error.data != 'The provided value \'{invalid}\' does not respect the expected ID prefix \'{prefixes}\'.':
                assert False, 'remove known error'
                check_oapi_error(error, 4104, invalid='toto', prefixes='sg-')
            known_error('API-355', 'Incorrect error formatting (LoadBalancer)')
        name = id_generator(prefix='lbu-')
        self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{"BackendPort": 65535, "BackendProtocol":"HTTP", 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, Subnets=[self.subnet_id],
        )
        self.lb_names.append(name)

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
            if error.data != 'The provided value \'{invalid}\' does not respect the expected ID prefix \'{prefixes}\'.':
                assert False, 'remove known error'
                check_oapi_error(error, 4104, invalid='toto', prefixes='')
            known_error('API-355', 'Incorrect error formatting (LoadBalancer)')

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
            if error.data != 'The provided value \'{invalid}\' does not respect the expected ID prefix \'{prefixes}\'.':
                assert False, 'remove known error'
                check_oapi_error(error, 4104, invalid='toto', prefixes='subnet-')
            known_error('API-355', 'Incorrect error formatting (LoadBalancer)')
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
            check_oapi_error(error, 8010)
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
            check_oapi_error(error, 8010)

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
            check_oapi_error(error, 9013)

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
            check_oapi_error(error, 9013)

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
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name]
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
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name]
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
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name]
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
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name]
            ).response.LoadBalancer
            validate_load_balancer_global_form(
                ret,
                name=name,
                lst=[{'BackendPort': 80, 'BackendProtocol': 'TCP', 'LoadBalancerPort': 1024,
                      'LoadBalancerProtocol': 'TCP'}],
            )
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
        except OscApiException as error:
            check_oapi_error(error)

    def test_T2591_with_valid_security_group(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(
            SecurityGroups=[self.sg_id, self.sg_id_2],
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internal', Subnets=[self.subnet_id],
        ).response.LoadBalancer
        assert len(ret.SecurityGroups) == 2
        for sec_grp in ret.SecurityGroups:
            assert sec_grp in [self.sg_id, self.sg_id_2]
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
            Subnets=[self.subnet_id]
        ).response.LoadBalancer
        self.lb_names.append(name)
        validate_load_balancer_global_form(
            ret,
            lb_type='internet-facing',
            name=name,
        )

    def test_T5145_without_igw(self):
        new_vpc = None
        try:
            name = id_generator(prefix='lbu-')
            new_vpc = create_vpc(self.a1_r1, az=self.a1_r1.config.region.az_name, igw=False)
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internet-facing', SecurityGroups=[self.sg_id],
                Subnets=[new_vpc['subnets'][0]['subnet_id']])
        except OscApiException as error:
            check_oapi_error(error, 1003)
        finally:
            if new_vpc:
                delete_vpc(self.a1_r1, new_vpc)

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
            check_oapi_error(error, 5020)

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
            check_oapi_error(error, 4036)

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
            check_oapi_error(error, 4036)

    def test_T2598_private_internal_without_security_group(self):
        name = id_generator(prefix='lbu-')
        self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, LoadBalancerType='internal', Subnets=[self.subnet_id],
        )
        self.lb_names.append(name)

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

        name = id_generator(prefix='lbu-')
        self.a1_r1.oapi.CreateLoadBalancer(
            Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
            LoadBalancerName=name, Subnets=[self.subnet_id],
        )
        self.lb_names.append(name)

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
            check_oapi_error(error, 3002)

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
            check_oapi_error(error)

    def test_T4160_private_with_incompatible_subnet_and_subregion(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        try:
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, SecurityGroups=[self.sg_id], Subnets=[self.subnet_id], SubregionNames=[self.a1_r2.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, subregion and subnet are incompatible"
        except OscApiException as error:
            check_oapi_error(error)

    def test_T4738_multi_lbu_same_name_diff_users(self):
        ret_create_lbu1 = None
        ret_create_lbu2 = None
        name = id_generator(prefix='lbu-')
        try:
            ret_create_lbu1 = self.a2_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=name, SubregionNames=[self.a2_r1.config.region.az_name])
            ret_create_lbu2 = self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80},
                           {'BackendPort': 1856, 'LoadBalancerProtocol': 'TCP', 'LoadBalancerPort': 1080}],
                LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
        finally:
            if ret_create_lbu1:
                try:
                    self.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
                except:
                    print('Could not delete lbu')
            if ret_create_lbu2:
                try:
                    self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
                except:
                    print('Could not delete lbu')

    def test_T5559_after_delete_same_name(self):
        name = id_generator(prefix='lbu-')
        self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                            LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
        time.sleep(10)  # to make sure lbu is started
        self.a1_r1.oapi.CreateLoadBalancerPolicy(LoadBalancerName=name, PolicyName=id_generator(prefix='policy-'), PolicyType='load_balancer')
        self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
        try:
            self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                               LoadBalancerName=name, SubregionNames=[self.a1_r1.config.region.az_name])
            self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
            assert False, 'Could should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 9013)

    def test_T5806_lbu_dry_run(self):
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                                 LoadBalancerName=name,
                                                 SubregionNames=[self.a1_r1.config.region.az_name],
                                                 Tags=[{'Key': 'tag_key', 'Value': 'tag_value'}],
                                                 DryRun=True)
        assert_dry_run(ret)

    def test_T5807_public_lbu_with_valid_param(self):
        hints = []
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                                 LoadBalancerName=name,
                                                 SubregionNames=[self.a1_r1.config.region.az_name])
        self.lb_names.append(name)

        hints.append(name)
        hints.append(self.a1_r1.config.region.az_name)

        hints = create_hints(hints)

        verify_response(ret.response,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5807_public_lbu_with_valid_param.json'),
                        hints,
                        ignored_keys=["DnsName"])

    def test_T5808_public_lbu_with_empty_public_ip(self):
        hints = []
        public_ip = ''
        name = id_generator(prefix='lbu-')

        ret = self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                                 LoadBalancerName=name, PublicIp=public_ip, SubregionNames=[self.a1_r1.config.region.az_name])
        self.lb_names.append(name)

        hints.append(name)
        hints.append(self.a1_r1.config.region.az_name)

        hints = create_hints(hints)

        verify_response(ret.response,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5808_public_lbu_with_empty_public_ip.json'),
                        hints,
                        ignored_keys=["DnsName"])

    def test_T5809_public_lbu_with_invalid_value_public_ip(self):
        try:
            public_ip = 'toto'
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                               LoadBalancerName=name,
                                               PublicIp=public_ip,
                                               SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid public ip param"
        except OscApiException as error:
            check_oapi_error(error, 4047)

    def test_T5810_public_lbu_with_invalid_type_public_ip(self):
        try:
            public_ip = 80
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                               LoadBalancerName=name,
                                               PublicIp=public_ip,
                                               SubregionNames=[self.a1_r1.config.region.az_name])
            self.lb_names.append(name)
            assert False, "Call should not have been successful, request must contain valid public ip param"
        except OscApiException as error:
            check_oapi_error(error, 4110)

    def test_T5811_public_lbu_with_public_ip(self):
        hints = []
        public_ip = self.a1_r1.oapi.CreatePublicIp().response.PublicIp.PublicIp
        name = id_generator(prefix='lbu-')
        ret = self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                                 LoadBalancerName=name,
                                                 PublicIp=public_ip,
                                                 SubregionNames=[self.a1_r1.config.region.az_name])
        hints.append(name)
        hints.append(public_ip)
        hints.append(self.a1_r1.config.region.az_name)

        hints = create_hints(hints)

        verify_response(ret.response,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5811_public_lbu_with_eip.json'),
                        hints,
                        ignored_keys=["DnsName"])
        if name:
            try:
                self.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=name)
                delete_lbu(self.a1_r1, name)
                cleanup_load_balancers(self.a1_r1,  filters={'LoadBalancerNames': name}, force=True)
            except:
                print('Could not delete lbu')
        if public_ip:
            sleep(2)
            self.a1_r1.oapi.DeletePublicIp(PublicIp=public_ip)

    def test_T5813_public_lbu_with_used_public_ip(self):
        public_ip = None
        vm_info = None
        try:
            public_ip = self.a1_r1.oapi.CreatePublicIp().response.PublicIp.PublicIp
            vm_info = oapi.create_Vms(self.a1_r1)
            self.a1_r1.oapi.LinkPublicIp(VmId=vm_info[info_keys.VM_IDS][0], PublicIp=public_ip)
            name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                                   LoadBalancerName=name,
                                                   PublicIp=public_ip,
                                                   SubregionNames=[self.a1_r1.config.region.az_name])
        except OscApiException as error:
            check_oapi_error(error, 9031)
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if public_ip:
                self.a1_r1.oapi.DeletePublicIp(PublicIp=public_ip)
