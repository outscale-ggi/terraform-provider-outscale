import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNET_ID, SUBNETS
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_nat_gateways_state, wait_instances_state
from qa_tina_tools.tools.tina.create_tools import create_instances


class Test_CreateNatGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.eip = None
        super(Test_CreateNatGateway, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='available')
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
            assert False, "Call shouldn't be successful"
            ng_id = ret.response.natGateway.natGatewayId
            wait_nat_gateways_state(self.a2_r1, nat_gateway_id_list=[ng_id], state='available')
        except OscApiException as error:
            assert_error(error, 400, "InvalidSubnetID.NotFound", "The subnet ID '{}' does not exist".format(self.vpc_info[SUBNETS][0][SUBNET_ID]))
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a2_r1, nat_gateway_id_list=[ng_id], state='deleted')

    def test_T279_in_private_subnet(self):
        vpc_info = None
        ng_id = None
        try:
            # create a vpc with an internet gateway and a public subnet
            vpc_info = create_vpc(self.a1_r1, igw=True, nb_subnet=1)

            # create one instance in public subnet in running mode
            vm_info_public = create_instances(self.a1_r1, subnet_id=vpc_info[SUBNETS][0]["subnet_id"], state='ready')
            wait_instances_state(self.a1_r1, vm_info_public[INSTANCE_ID_LIST], state='running')

            # public instance has en eip to access to another instance
            ret = self.a1_r1.fcu.AssociateAddress(InstanceId=vm_info_public[INSTANCE_ID_LIST][0],
                                                       PublicIp=self.eip.publicIp)

            # create a private subnet with no route to internet
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId=vpc_info[VPC_ID], CidrBlock='10.0.7.0/24').response.subnet.subnetId

            # create an instance in private subnet in running mode
            vm_info_private = create_instances(self.a1_r1, subnet_id=subnet_id, state='ready')
            wait_instances_state(self.a1_r1, vm_info_private[INSTANCE_ID_LIST], state='running')

            # create a NAT gateway in the private subnet
            ret = self.a1_r1.fcu.CreateNatGateway(AllocationId=self.eip.allocationId, SubnetId=subnet_id)
        #     assert False, "The subnet ID '{subnet_id}' don't have route to internet"
        except OscApiException as error:
            assert_error(error, 400, "InvalidSubnet.NotPublic"
                                    , f"The subnet ID '{subnet_id}' must have route to internet")
        finally:
            if ng_id:
                self.a1_r1.fcu.DeleteNatGateway(NatGatewayId=ng_id)
                wait_nat_gateways_state(self.a1_r1, nat_gateway_id_list=[ng_id], state='deleted')
            if ret:
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.eip.publicIp)
            # if vpc_info:
            #    delete_vpc(self.a1_r1, vpc_info)
