import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNET_ID, SUBNETS
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_nat_gateways_state


class Test_CreateNatGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.eip = None
        super(Test_CreateNatGateway, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=2, state=None)
            cls.eip = cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response

        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
            if cls.eip:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.eip.publicIp)
        finally:
            super(Test_CreateNatGateway, cls).teardown_class()

    def test_T1683_correct_params(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4087_missing_subnet_id_param(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId)
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: SubnetId")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4088_missing_allocation_id_param(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: AllocationId")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4089_without_params(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway()
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: SubnetId, AllocationId")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4090_with_invalid_allocation_id(self):
        ng_id = None
        eipalloc = id_generator(size=8, chars=string.ascii_lowercase)
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=eipalloc, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidAllocationID.NotFound", "The allocation ID '{}' does not exist".format(eipalloc))
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4091_with_none_allocation_id(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=None, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: AllocationId")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4092_with_empty_allocation_id(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId="", SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidAllocationID.NotFound", "The allocation ID '' does not exist")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4093_with_empty_subnet_id(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId, SubnetId="")
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSubnetID.NotFound", "The subnet ID '' does not exist")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4094_with_none_subnet_id(self):
        ng_id = None
        try:
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId, SubnetId=None)
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Request is missing the following parameter: SubnetId")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T4095_with_another_account(self):
        ng_id = None
        try:
            ret = self.a2_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId, SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a2_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSubnetID.NotFound", "The subnet ID '{}' does not exist".format(self.vpc_info[SUBNETS][0][SUBNET_ID]))
        finally:
            if ng_id:
                self.a2_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a2_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T279_in_private_subnet(self):
        ng_id = None
        try:
            # create a NAT gateway in the private subnet
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId,
                                                    SubnetId=self.vpc_info[SUBNETS][1][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSubnet.NotPublic",
                        "The subnet ID '{}' must have route to internet".format(self.vpc_info[SUBNETS][1][SUBNET_ID]))
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T5678_with_adress_in_use(self):
        ng_id = None
        try:
            # create one instance in public subnet in running mode
            vm_info_vpc = create_instances(self.a1_r1, subnet_id=self.vpc_info[SUBNETS][0]["subnet_id"], state='running')

            # # public instance has en eip to access to another instance
            self.a1_r1.fcu.AssociateAddress(InstanceId=vm_info_vpc[INSTANCE_ID_LIST][0],
                                                        PublicIp=self.eip.publicIp)

            # create a NAT gateway in the private subnet
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId,
                                                    SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidIPAddress.InUse",
                                     "Address {} is in use.".format(self.eip.publicIp))
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')
            if vm_info_vpc:
                delete_instances(self.a1_r1, vm_info_vpc, wait=True)
