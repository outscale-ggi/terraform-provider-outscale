

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SUBNETS, SUBNET_ID


def validate_load_balancer_global_form(lb, **kwargs):
    """

    :param lb:
    :param kwargs:
        str lb_type: the Load Balancer type
        str name: the Load Balancer name
        lst[(str, str)]tags: the Load Balancer tags, it's a lst of (key, value)
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
        lst(dict) lst: the lst of listener
            int BackendPort
            str BackendProtocol
            int LoadBalancerPort
            str LoadBalancerProtocol
            lst(str)PolicyNames
            str ServerCertificateId
        str net_id: the net_id.
        str subnet_id: the subnet_id.
        str az: the az.
        str sg_id: the security group id.
    :return:
    """
    assert hasattr(lb, 'AccessLog')
    access_log = kwargs.get('access_log')
    if access_log:
        for key, value in access_log.items():
            assert getattr(lb.AccessLog, key) == value
    assert hasattr(lb, 'ApplicationStickyCookiePolicies')
    for pol in lb.ApplicationStickyCookiePolicies:
        assert hasattr(pol, 'CookieName')
        assert hasattr(pol, 'PolicyName')
    assert hasattr(lb, 'BackendVmIds')
    assert hasattr(lb, 'DnsName')
    if kwargs.get('dns_name'):
        assert kwargs.get('dns_name') in lb.DnsName
    assert hasattr(lb, 'HealthCheck')
    health_check = kwargs.get('hc')
    if health_check:
        for key, value in health_check.items():
            assert getattr(lb.HealthCheck, key) == value, ('In HealthCheck, {} is different of expected value {} for key {}'
                                                     .format(getattr(lb.HealthCheck, key), value, key))
        for attr in lb.HealthCheck.__dict__:
            if not attr.startswith('_'):
                assert attr in health_check, 'In HealthCheck, {} has not been validated'.format(attr)
    assert hasattr(lb, 'Listeners')
    lsts = kwargs.get('lst', [])
    for lst in lsts:
        for llst in lb.Listeners:
            if llst.LoadBalancerPort == lst['LoadBalancerPort']:
                for key, value in lst.items():
                    assert getattr(llst, key) == value, ('In listener, {} is different of expected value {} for key {}'
                                                .format(getattr(llst, key), value, key))
    assert hasattr(lb, 'LoadBalancerName')
    if kwargs.get('name'):
        assert lb.LoadBalancerName == kwargs.get('name')
    assert hasattr(lb, 'LoadBalancerStickyCookiePolicies')
    for pol in lb.LoadBalancerStickyCookiePolicies:
        assert hasattr(pol, 'PolicyName')
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
        cls.inst_info = None
        super(LoadBalancer, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, az=cls.a1_r1.config.region.az_name, nb_subnet=2)
            cls.vpc_id = cls.vpc_info[VPC_ID]
            cls.subnet_id = cls.vpc_info[SUBNETS][0][SUBNET_ID]
            cls.subnet_id2 = cls.vpc_info[SUBNETS][1][SUBNET_ID]
            cls.inst_info = create_instances(cls.a1_r1, subnet_id=cls.subnet_id)
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
            print('Could not delete security group')
        try:
            if cls.sg_id_2:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id_2)
        except:
            print('Could not delete security group')
        try:
            if cls.sg_id_3:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id_3)
        except:
            print('Could not delete security group')
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        except:
            print('Could not delete instances')
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        except:
            print('Could not delete vpc')
        finally:
            super(LoadBalancer, cls).teardown_class()
