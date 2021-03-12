
import pytest

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNETS, SECURITY_GROUP_ID, SUBNET_ID
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_lbu, delete_vpc
from qa_tina_tools.tools.tina.wait_tools import wait_load_balancer_state


class Test_gc(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.ret_lbu = None
        super(Test_gc, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=1)
            sg_id = cls.vpc_info[SUBNETS][0][SECURITY_GROUP_ID]
            cls.lb_name = id_generator('lbu')
            cls.ret_lbu = cls.a1_r1.lbu.CreateLoadBalancer(Listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                                           LoadBalancerName=cls.lb_name,
                                                           SecurityGroups=[sg_id], Subnets=[cls.vpc_info[SUBNETS][0][SUBNET_ID]])
            wait_load_balancer_state(cls.a1_r1, load_balancer_name_list=[cls.lb_name])
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret_lbu:
                try:
                    delete_lbu(cls.a1_r1, lbu_name=cls.lb_name)
                except:
                    print('Could not delete lbu')
            if cls.vpc_info:
                try:
                    delete_vpc(cls.a1_r1, cls.vpc_info)
                except:
                    print('Could not delete vpc')
        finally:
            super(Test_gc, cls).teardown_class()

    @pytest.mark.region_qa
    def test_T3999_with_lbu_using_inst_sg(self):
        self.a1_r1.intel_lbu.control.gc(name=self.lb_name, owner=self.a1_r1.config.account.account_id)
        self.ret_lbu = None
