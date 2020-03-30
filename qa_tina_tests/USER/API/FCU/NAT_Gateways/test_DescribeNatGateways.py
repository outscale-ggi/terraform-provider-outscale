# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tina.info_keys import SUBNET_ID, SUBNETS
from qa_tina_tools.tools.tina.wait_tools import wait_nat_gateways_state
from qa_test_tools.misc import assert_error


class Test_DescribeNatGateways(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.eip = None
        cls.ng_id = None
        super(Test_DescribeNatGateways, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
            cls.eip = cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response.allocationId
            cls.ng_id = cls.a1_r1.fcu.CreateNatGateway(AllocationId=cls.eip,
                                                       SubnetId=cls.vpc_info[SUBNETS][0][SUBNET_ID]).response.natGateway.natGatewayId
            wait_nat_gateways_state(cls.a1_r1, nat_gateway_id_list=[cls.ng_id], state='available')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ng_id:
                cls.a1_r1.fcu.DeleteNatGateway(NatGatewayId=cls.ng_id)
            if cls.eip:
                cls.a1_r1.fcu.ReleaseAddress(AllocationId=cls.eip)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DescribeNatGateways, cls).teardown_class()

    def test_T3080_others_get_DescribeNatGateways(self):
        try:
            self.a2_r1.fcu.DescribeNatGateways(NatGatewayId=self.ng_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NatGatewayNotFound', "The NAT gateway '" + self.ng_id + "' does not exist")

    def test_T4034_valid_param(self):
        ret = self.a1_r1.fcu.DescribeNatGateways(NatGatewayId=self.ng_id)
        assert len(ret.response.natGatewaySet) == 1 and ret.response.natGatewaySet[0].natGatewayId == self.ng_id
            
    def test_T4035_non_existent_nat_gateway_id(self):
        try:
            self.a1_r1.fcu.DescribeNatGateways(NatGatewayId="ng-12345678")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NatGatewayNotFound', "The NAT gateway 'ng-12345678' does not exist")        
