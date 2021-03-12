from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNET_ID, SUBNETS
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.wait_tools import wait_nat_gateways_state


class Test_DeleteNatGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.eip = None
        cls.ng_id = None
        super(Test_DeleteNatGateway, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
            cls.eip = cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.eip:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip.publicIp)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DeleteNatGateway, cls).teardown_class()

    def setup_method(self, method):
        self.ng_id = None
        OscTestSuite.setup_method(self, method)
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            self.ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[self.ng_id], state='available')
        except:
            try:
                OscTestSuite.teardown_method(self, method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=self.ng_id)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T4028_correct_params(self):
        self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=self.ng_id)
        wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[self.ng_id], state='deleted')
        self.ng_id = None

    def test_T4029_without_param(self):
        try:
            self.a1_r1.fcu.DeleteNatGateway()
            self.ng_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: NatGatewayId")

    def test_T4030_none_nat_gateway_id(self):
        try:
            self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=None)
            self.ng_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: NatGatewayId")

    def test_T4031_empty_nat_gateway_id(self):
        try:
            self.a1_r1.fcu.DeleteNatGateway(NatGatewayId="")
            self.ng_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: NatGatewayID')

    def test_T4032_non_existent_nat_gateway_id(self):
        try:
            self.a1_r1.fcu.DeleteNatGateway(NatGatewayId="XYXYXYXYXY")
            self.ng_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidNatGatewayID.Malformed", "Invalid ID received: XYXYXYXYXY. Expected format: nat-")

    def test_T4033_another_account(self):
        try:
            self.a2_r1.fcu.DeleteNatGateway(NatGatewayId=self.ng_id)
            self.ng_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "NatGatewayNotFound", "The NAT gateway '{}' does not exist".format(self.ng_id))
