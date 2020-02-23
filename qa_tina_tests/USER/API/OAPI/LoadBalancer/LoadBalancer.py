# -*- coding:utf-8 -*-

from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_common_tools.misc import id_generator
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SUBNETS, SUBNET_ID


def validate_load_balancer_global_form(lb, **kwargs):
    """

    :param lb:
    :param kwargs:
        str lb_type: the Load Balancer type
        str name: the Load Balancer name
        list[(str, str)]tags: the Load Balancer tags, it's a list of (key, value)
        dict access_log: expected access log
            bool IsEnabled
            str OsuBucketName
            str OsuBucketPrefix
            int PublicationInterval
        dict hc: expected health check
            int CheckInterval
            int HealthyThreshold
            str Path
            int Port
            str Protocol
            int Timeout
            int UnhealthyThreshold
        str dns_name: the static part of the dns_name
        list(dict) lst: the list of listener
            int BackendPort
            str BackendProtocol
            int LoadBalancerPort
            str LoadBalancerProtocol
            list(str)PolicyNames
            str ServerCertificateId
        str net_id: the net_id.
        str subnet_id: the subnet_id.
        str az: the az.
        str sg_id: the security group id.
    :return:
    """
    assert hasattr(lb, 'AccessLog')
    al = kwargs.get('access_log')
    if al:
        for k, v in al.items():
            assert getattr(lb.AccessLog, k) == v
    assert hasattr(lb, 'ApplicationStickyCookiePolicies')
    for p in lb.ApplicationStickyCookiePolicies:
        assert hasattr(p, 'CookieName')
        assert hasattr(p, 'PolicyName')
    assert hasattr(lb, 'BackendVmIds')
    assert hasattr(lb, 'DnsName')
    if kwargs.get('dns_name'):
        assert kwargs.get('dns_name') in lb.DnsName
    assert hasattr(lb, 'HealthCheck')
    hc = kwargs.get('hc')
    if hc:
        for k, v in hc.items():
            assert getattr(lb.HealthCheck, k) == v, ('In HealthCheck, {} is different of expected value {} for key {}'
                                                     .format(getattr(lb.HealthCheck, k), v, k))
    assert hasattr(lb, 'Listeners')
    lsts = kwargs.get('lst', [])
    for lst in lsts:
        for l in lb.Listeners:
            if l.LoadBalancerPort == lst['LoadBalancerPort']:
                for k, v in lst.items():
                    assert getattr(l, k) == v, ('In listener, {} is different of expected value {} for key {}'
                                                .format(getattr(l, k), v, k))
            else:
                pass
    assert hasattr(lb, 'LoadBalancerName')
    if kwargs.get('name'):
        assert lb.LoadBalancerName == kwargs.get('name')
    assert hasattr(lb, 'LoadBalancerStickyCookiePolicies')
    for p in lb.LoadBalancerStickyCookiePolicies:
        assert hasattr(p, 'PolicyName')
    assert hasattr(lb, 'LoadBalancerType')
    if kwargs.get('lb_type'):
        assert lb.LoadBalancerType == kwargs.get('lb_type')
    if kwargs.get('net_id'):
        assert kwargs.get('net_id') == lb.NetId
    if kwargs.get('sg_id'):
        assert hasattr(lb, 'SecurityGroups')
        assert kwargs.get('sg_id') == lb.SecurityGroups[0]
    assert hasattr(lb, 'SourceSecurityGroup')
    if kwargs.get('source_sg'):
        assert hasattr(lb.SourceSecurityGroup, 'SecurityGroupName')
        assert hasattr(lb.SourceSecurityGroup, 'SecurityGroupOwner')
    assert hasattr(lb, 'Subnets')
    if kwargs.get(SUBNET_ID):
        assert kwargs.get(SUBNET_ID) == lb.Subnets[0]
    assert hasattr(lb, 'SubregionNames')
    if kwargs.get('az'):
        assert kwargs.get('az') == lb.SubregionNames[0]
    assert hasattr(lb, 'Tags')
    tags = kwargs.get('tags')
    if tags:
        assert len(lb.Tags) == len(tags)
        for tag in lb.Tags:
            assert (tag.Key, tag.Value) in tags


class LoadBalancer(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.vpc_id = None
        cls.igw_id = None
        cls.subnet_id = None
        cls.subnet_id2 = None
        cls.sg_id = None
        cls.sg_name = None
        cls.sg_id_2 = None
        cls.sg_id_3 = None
        super(LoadBalancer, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, az=cls.a1_r1.config.region.az_name, nb_subnet=2)
            cls.vpc_id = cls.vpc_info[VPC_ID]
            cls.subnet_id = cls.vpc_info[SUBNETS][0][SUBNET_ID]
            cls.subnet_id2 = cls.vpc_info[SUBNETS][1][SUBNET_ID]
            sg_name = id_generator(prefix='sg_name')
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test', GroupName=sg_name, VpcId=cls.vpc_id)
            cls.sg_id = ret.response.groupId
            cls.sg_name = sg_name
            sg_name = id_generator(prefix='sg_name')
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test', GroupName=sg_name, VpcId=cls.vpc_id)
            cls.sg_id_2 = ret.response.groupId
            sg_name = id_generator(prefix='sg_name')
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test', GroupName=sg_name)
            cls.sg_id_3 = ret.response.groupId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.sg_id:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id)
        except:
            pass
        try:
            if cls.sg_id_2:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id_2)
        except:
            pass
        try:
            if cls.sg_id_3:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id_3)
        except:
            pass
        try:
            if cls.vpc_info:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info[VPC_ID]])
        finally:
            super(LoadBalancer, cls).teardown_class()
