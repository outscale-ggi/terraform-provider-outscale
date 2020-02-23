import time

from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_lbu
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_load_balancer_state


class Test_find_tag_resource_owner(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find_tag_resource_owner, cls).setup_class()
        cls.vpc_info = None
        try:
            cls.vpc_info = create_vpc(osc_sdk=cls.a1_r1)
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info[VPC_ID]])
        finally:
            super(Test_find_tag_resource_owner, cls).teardown_class()

    def test_T4434_with_vpc(self):
        ret=self.a1_r1.intel.netimpl.create_firewalls(resource=self.vpc_info[VPC_ID])
        ret = self.a1_r1.intel.tag.find(resource=ret.response.result.master.vm, key='resource-owner')
        assert len(ret.response.result) == 1
        assert ret.response.result[0].value == self.a1_r1.config.account.account_id

    def test_T4436_with_vgw(self):
        vgw_id = None
        try:
            vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
            self.a1_r1.intel.vpn.virtual_private_gateway.spawn(vpg=vgw_id)
            ret = self.a1_r1.intel.netimpl.firewall.find_firewalls(filters={'resource': vgw_id})
            ret = self.a1_r1.intel.tag.find(resource=ret.response.result[0].vm, key='resource-owner')
            assert len(ret.response.result) == 1
            assert ret.response.result[0].value == self.a1_r1.config.account.account_id
        finally:
            self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)

    def test_T4440_with_lbu(self):
        try:
            lb_name = id_generator(prefix='lbu-')
            self.a1_r1.oapi.CreateLoadBalancer(
                Listeners=[{'BackendPort': 65535, 'LoadBalancerProtocol': 'HTTP', 'LoadBalancerPort': 80}],
                LoadBalancerName=lb_name, SubregionNames=[self.a1_r1.config.region.az_name],
            )
            ret = self.a1_r1.intel_lbu.lb.get(owner=self.a1_r1.config.account.account_id, names=[lb_name])
            resource = ret.response.result[0].dns_name.split('.')[0]
            time.sleep(30)
            ret = self.a1_r1.intel.netimpl.firewall.find_firewalls(filters={'resource': resource})
            ret = self.a1_r1.intel.tag.find(resource=ret.response.result[0].vm, key='resource-owner')
            self.logger.info(ret.response.result)
            assert len(ret.response.result) == 1
            assert ret.response.result[0].value == self.a1_r1.config.account.account_id
        finally:
            delete_lbu(self.a1_r1, lbu_name=lb_name)

