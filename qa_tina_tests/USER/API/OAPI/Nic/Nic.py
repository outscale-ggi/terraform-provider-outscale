# -*- coding:utf-8 -*-
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_security_group
from qa_tina_tools.tools.tina.delete_tools import delete_security_group


class Nic(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc1_info = None
        cls.vpc_id1 = None
        cls.subnet_id1 = None
        cls.subnet_id2 = None
        cls.firewall_id1 = None
        super(Nic, cls).setup_class()
        try:
            cls.vpc1_info = create_vpc(cls.a1_r1, cidr_prefix='10.0', igw=False, nb_subnet=2)
            cls.vpc_id1 = cls.vpc1_info['vpc_id']
            cls.subnet_id1 = cls.vpc1_info['subnets'][0]['subnet_id']
            cls.subnet_id2 = cls.vpc1_info['subnets'][1]['subnet_id']
            cls.firewall_id1 = create_security_group(cls.a1_r1, name='nic_test', vpc_id=cls.vpc_id1)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.firewall_id1:
                delete_security_group(cls.a1_r1, cls.firewall_id1)
            if cls.vpc1_info:
                cleanup_vpcs(cls.a1_r1, cls.vpc_id1, threshold=90)
        finally:
            super(Nic, cls).teardown_class()
