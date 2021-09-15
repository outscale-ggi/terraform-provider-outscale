

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina.info_keys import SUBNET_ID, SUBNETS
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.wait_tools import wait_nat_gateways_state

NUM_NAT_GTW = 4

class Test_DescribeNatGateways(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.vpc_infos = []
        cls.eips = []
        cls.ng_ids = []
        super(Test_DescribeNatGateways, cls).setup_class()
        try:
            for i in range(NUM_NAT_GTW):
                cls.vpc_infos.append(create_vpc(cls.a1_r1))
                cls.eips.append(cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response.allocationId)
                cls.ng_ids.append(cls.a1_r1.fcu.CreateNatGateway(AllocationId=cls.eips[i],
                                                                 SubnetId=cls.vpc_infos[i][SUBNETS][0][SUBNET_ID]).response.natGateway.natGatewayId)
            wait_nat_gateways_state(cls.a1_r1, nat_gateway_id_list=cls.ng_ids, state='available')
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for ng_id in cls.ng_ids:
                cls.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
            for eip in cls.eips:
                cls.a1_r1.fcu.ReleaseAddress(AllocationId=eip)
            for vpc_info in cls.vpc_infos:
                delete_vpc(cls.a1_r1, vpc_info)
        finally:
            super(Test_DescribeNatGateways, cls).teardown_class()

    def test_T3080_others_get_DescribeNatGateways(self):
        try:
            self.a2_r1.fcu.DescribeNatGateways(NatGatewayId=[self.ng_ids[0]])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, 'NatGatewayNotFound', "The NAT gateway '" + self.ng_ids[0] + "' does not exist")

    def test_T4034_valid_param(self):
        ret = self.a1_r1.fcu.DescribeNatGateways(NatGatewayId=self.ng_ids[0])
        assert len(ret.response.natGatewaySet) == 1 and ret.response.natGatewaySet[0].natGatewayId == self.ng_ids[0]

    def test_T4035_non_existent_nat_gateway_id(self):
        try:
            self.a1_r1.fcu.DescribeNatGateways(NatGatewayId="ng-12345678")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, 'NatGatewayNotFound', "The NAT gateway 'ng-12345678' does not exist")

    def test_T5959_with_tag_filter(self):
        misc.execute_tag_tests(self.a1_r1, 'NatGateway', self.ng_ids,
                               'fcu.DescribeNatGateways', 'natGatewaySet.natGatewayId')
