# -*- coding:utf-8 -*-
import pytest

from qa_test_tools.misc import id_generator
from qa_tina_tests.USER.API.OAPI.LoadBalancer.LoadBalancer import LoadBalancer, validate_load_balancer_global_form


class Test_ReadLoadBalancers(LoadBalancer):

    @classmethod
    def setup_class(cls):
        super(Test_ReadLoadBalancers, cls).setup_class()
        cls.lb_names_a1 = []
        cls.lb_names_a2 = []
        cls.lb_dnsnames_a1 = []
        cls.lb_dnsnames_a2 = []
        cls.setup_error = False
        try:
            name = id_generator(prefix='lbu-')
            ret = cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[cls.a1_r1.config.region.az_name])
            cls.lb_names_a1.append(name)
            cls.lb_dnsnames_a1.append(ret.response.LoadBalancer.DnsName)
            name = id_generator(prefix='lbu-')
            ret = cls.a1_r1.oapi.CreateLoadBalancer(
                SecurityGroups=[cls.sg_id],
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                LoadBalancerName=name, LoadBalancerType='internal',
                Subnets=[cls.subnet_id])
            cls.lb_names_a1.append(name)
            cls.lb_dnsnames_a1.append(ret.response.LoadBalancer.DnsName)
            name = id_generator(prefix='lbu-')
            ret = cls.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'TCP'}],
                LoadBalancerName=name, LoadBalancerType='internal',
                Subnets=[cls.subnet_id],
                SecurityGroups=[cls.sg_id])
            cls.lb_names_a1.append(name)
            cls.lb_dnsnames_a1.append(ret.response.LoadBalancer.DnsName)

            name = cls.lb_names_a1[0]
            ret = cls.a2_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=name, SubregionNames=[cls.a2_r1.config.region.az_name],
            )
            cls.lb_names_a2.append(name)
            cls.lb_dnsnames_a2.append(ret.response.LoadBalancer.DnsName)

        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            for lb_name in cls.lb_names_a1:
                try:
                    cls.a1_r1.oapi.DeleteLoadBalancer(LoadBalancerName=lb_name)
                except:
                    pass
            for lb_name in cls.lb_names_a2:
                try:
                    cls.a2_r1.oapi.DeleteLoadBalancer(LoadBalancerName=lb_name)
                except:
                    pass
        finally:
            super(Test_ReadLoadBalancers, cls).teardown_class()

    def test_T2606_empty_param(self):
        ret = self.a1_r1.oapi.ReadLoadBalancers().response.LoadBalancers
        assert len(ret) == 3
        count = 0
        for lb in ret:
            if lb.LoadBalancerName == self.lb_names_a1[0]:
                count += 1
                validate_load_balancer_global_form(
                    lb,
                    access_log={'IsEnabled': False, 'PublicationInterval': 60},
                    az=self.a1_r1.config.region.az_name,
                    dns_name='.lbu.outscale.com',
                    hc={'CheckInterval': 30, 'HealthyThreshold': 10, 'Port': 65535, 'Protocol': 'TCP', 'Timeout': 5,
                        'UnhealthyThreshold': 2},
                    lb_type='internet-facing',
                    lst=[{'BackendPort': 65535, 'BackendProtocol': 'HTTP', 'LoadBalancerPort': 80,
                          'LoadBalancerProtocol': 'HTTP'}],
                    name=self.lb_names_a1[0],
                    subnet_id=None,
                )
                assert lb.SourceSecurityGroup.SecurityGroupAccountId == 'outscale-elb'
                assert lb.SourceSecurityGroup.SecurityGroupName == 'outscale-elb-sg'
            elif lb.LoadBalancerName == self.lb_names_a1[1]:
                count += 2
                validate_load_balancer_global_form(
                    lb,
                    access_log={'IsEnabled': False, 'PublicationInterval': 60},
                    az=self.a1_r1.config.region.az_name,
                    dns_name='.lbu.outscale.com',
                    hc={'CheckInterval': 30, 'HealthyThreshold': 10, 'Port': 80, 'Protocol': 'TCP', 'Timeout': 5,
                        'UnhealthyThreshold': 2},
                    lb_type='internal',
                    lst=[{'BackendPort': 80, 'BackendProtocol': 'HTTP', 'LoadBalancerPort': 80,
                          'LoadBalancerProtocol': 'HTTP'}],
                    name=self.lb_names_a1[1],
                    net_id=self.vpc_id,
                    sg_id=self.sg_id,
                    subnet_id=self.subnet_id,
                )
                assert lb.SourceSecurityGroup.SecurityGroupAccountId == self.a1_r1.config.account.account_id
                assert lb.SourceSecurityGroup.SecurityGroupName == self.sg_name
            elif lb.LoadBalancerName == self.lb_names_a1[2]:
                count += 4
                validate_load_balancer_global_form(
                    lb,
                    access_log={'IsEnabled': False, 'PublicationInterval': 60},
                    az=self.a1_r1.config.region.az_name,
                    dns_name='.lbu.outscale.com',
                    hc={'CheckInterval': 30, 'HealthyThreshold': 10, 'Port': 80, 'Protocol': 'TCP', 'Timeout': 5,
                        'UnhealthyThreshold': 2},
                    lb_type='internal',
                    lst=[{'BackendPort': 80, 'BackendProtocol': 'TCP', 'LoadBalancerPort': 80,
                          'LoadBalancerProtocol': 'TCP'}],
                    name=self.lb_names_a1[2],
                    net_id=self.vpc_id,
                    sg_id=self.sg_id,
                    subnet_id=self.subnet_id,
                )
                assert lb.SourceSecurityGroup.SecurityGroupAccountId == self.a1_r1.config.account.account_id
                assert lb.SourceSecurityGroup.SecurityGroupName == self.sg_name
        assert count == 7

    @pytest.mark.tag_sec_confidentiality
    def test_T3404_other_account(self):
        ret = self.a2_r1.oapi.ReadLoadBalancers().response.LoadBalancers
        assert len(ret) == 1
        assert ret[0].DnsName == self.lb_dnsnames_a2[0]

    @pytest.mark.tag_sec_confidentiality
    def test_T3405_other_account_with_filter_wrong_name(self):
        ret = self.a2_r1.oapi.ReadLoadBalancers(Filters={'LoadBalancerNames': [self.lb_names_a1[1]]}).response.LoadBalancers
        assert len(ret) == 0

    def test_T3406_with_filter_same_name(self):
        ret = self.a1_r1.oapi.ReadLoadBalancers(Filters={'LoadBalancerNames': [self.lb_names_a1[0]]}).response.LoadBalancers
        assert len(ret) == 1
        assert ret[0].DnsName == self.lb_dnsnames_a1[0]

    @pytest.mark.tag_sec_confidentiality
    def test_T3407_other_account_with_filter_same_name(self):
        ret = self.a2_r1.oapi.ReadLoadBalancers(Filters={'LoadBalancerNames': [self.lb_names_a2[0]]}).response.LoadBalancers
        assert len(ret) == 1
        assert ret[0].DnsName == self.lb_dnsnames_a2[0]
