from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SUBNETS, SUBNET_ID
from qa_common_tools.misc import assert_error
from osc_common.exceptions.osc_exceptions import OscApiException


class Test_AssociateRouteTable(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info1 = None
        cls.vpc_info2 = None
        cls.vpc_info3 = None
        cls.rtb_id1 = None
        cls.rtb_id2 = None
        cls.rtb_id3 = None
        super(Test_AssociateRouteTable, cls).setup_class()
        try:
            cls.vpc_info1 = create_vpc(cls.a1_r1, nb_subnet=1, default_rtb=True, igw=False)
            cls.rtb_id1 = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_info1[VPC_ID]).response.routeTable.routeTableId
            cls.vpc_info2 = create_vpc(cls.a1_r1, nb_subnet=1, default_rtb=True, igw=False)
            cls.rtb_id2 = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_info2[VPC_ID]).response.routeTable.routeTableId
            cls.vpc_info3 = create_vpc(cls.a2_r1, nb_subnet=1, default_rtb=True, igw=False)
            cls.rtb_id3 = cls.a2_r1.fcu.CreateRouteTable(VpcId=cls.vpc_info3[VPC_ID]).response.routeTable.routeTableId
        except Exception:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.rtb_id1:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb_id1)
            if cls.vpc_info1:
                delete_vpc(cls.a1_r1, cls.vpc_info1)
            if cls.rtb_id2:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb_id2)
            if cls.vpc_info2:
                delete_vpc(cls.a1_r1, cls.vpc_info2)
            if cls.rtb_id3:
                cls.a2_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb_id3)
            if cls.vpc_info3:
                delete_vpc(cls.a2_r1, cls.vpc_info3)
        finally:
            super(Test_AssociateRouteTable, cls).teardown_class()

    def test_T4249_missing_routetableid(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: RouteTableID")

    def test_T4250_missing_subnetid(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: SubnetID')

    def test_T4251_unknown_routetableid(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId='rtb-12345678', SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRouteTableID.NotFound', "The route table ID 'rtb-12345678' does not exist")

    def test_T4252_invalid_routetableid(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId='XXXXXXXX', SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRouteTableID.Malformed', 'Invalid ID received: XXXXXXXX. Expected format: rtb-')

    def test_T4253_invalid_routetableid_type(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=[self.rtb_id1], SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'RouteTableID' must be of type: string. Received: {{'1': '{}'}}".format(self.rtb_id1))

    def test_T4254_unknown_subnetid(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id1, SubnetId='subnet-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSubnetID.NotFound', "The subnet ID 'subnet-12345678' does not exist")

    def test_T4255_invalid_subnetid(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id1, SubnetId='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSubnetID.Malformed', 'Invalid ID received: XXXXXXXX. Expected format: subnet-')

    def test_T4256_invalid_subnetid_type(self):
        subnet_id = self.vpc_info1[SUBNETS][0][SUBNET_ID]
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id1, SubnetId=[subnet_id])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'SubnetID' must be of type: string. Received: {{'1': '{}'}}".format(subnet_id))

    def test_T4257_inconsistent_owner_vpc(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id2, SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         'Route table {} and subnet {} are not in same VPC'.format(self.rtb_id2, self.vpc_info1[SUBNETS][0][SUBNET_ID]))

    def test_T4258_other_account(self):
        try:
            self.a2_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id1, SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRouteTableID.NotFound', "The route table ID '{}' does not exist".format(self.rtb_id1))

    def test_T4259_inconsistent_account(self):
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id3, SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRouteTableID.NotFound', "The route table ID '{}' does not exist".format(self.rtb_id3))
        try:
            self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id1, SubnetId=self.vpc_info3[SUBNETS][0][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSubnetID.NotFound', "The subnet ID '{}' does not exist".format(self.vpc_info3[SUBNETS][0][SUBNET_ID]))

    def test_T4260_valid_params(self):
        ret_assoc = None
        try:
            ret_assoc = self.a1_r1.fcu.AssociateRouteTable(RouteTableId=self.rtb_id1, SubnetId=self.vpc_info1[SUBNETS][0][SUBNET_ID])
        finally:
            if ret_assoc:
                self.a1_r1.fcu.DisassociateRouteTable(AssociationId=ret_assoc.response.associationId)
