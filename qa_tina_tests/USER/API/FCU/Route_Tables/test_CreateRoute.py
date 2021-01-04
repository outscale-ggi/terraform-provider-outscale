from qa_test_tools.config.configuration import Configuration
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_error
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.delete_tools import delete_vpc


class Test_CreateRoute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.rtb1 = None
        super(Test_CreateRoute, cls).setup_class()
        try:
            # create VPC
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=1)
            ret = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_info[VPC_ID])
            cls.rtb1 = ret.response.routeTable.routeTableId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.rtb1:
                cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=cls.rtb1)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_CreateRoute, cls).teardown_class()

    def test_T600_invalid_igw_id(self):
        gtw_id = 'igw-12345678'
        try:
            self.a1_r1.fcu.CreateRoute(DestinationCidrBlock=Configuration.get('cidr', 'allips'), RouteTableId=self.rtb1,
                                       GatewayId=gtw_id)
            assert False, 'CreateRoute should have not succeeded'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInternetGatewayID.NotFound', "The InternetGatewayId '{}' does not exist".format(gtw_id))

    def test_T601_invalid_vgw_id(self):
        gtw_id = 'vgw-12345678'
        try:
            self.a1_r1.fcu.CreateRoute(DestinationCidrBlock=Configuration.get('cidr', 'allips'), RouteTableId=self.rtb1,
                                       GatewayId=gtw_id)
            assert False, 'CreateRoute should have not succeeded'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpnGatewayID.NotFound', "The VpnGatewayId '{}' does not exist".format(gtw_id))

    def test_T602_invalid_vpcpeeringconnection_id(self):
        pcx_id = 'pcx-12345678'
        try:
            self.a1_r1.fcu.CreateRoute(DestinationCidrBlock=Configuration.get('cidr', 'allips'), RouteTableId=self.rtb1,
                                       VpcPeeringConnectionId=pcx_id)
            assert False, 'CreateRoute should have not succeeded'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcPeeringConnectionID.NotFound', "The VpcPeeringConnectionId '{}' does not exist".format(pcx_id))

    def test_T599_no_param(self):
        try:
            self.a1_r1.fcu.CreateRoute()
            assert False, 'CreateRoute without parameters should have not succeeded'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Request is missing the following parameter: RouteTableId')

    def test_T5377_invalid_cidr(self):
        gtw_id = 'igw-12345678'
        try:
            self.a1_r1.fcu.CreateRoute(DestinationCidrBlock='10.10.10.23/24', RouteTableId=self.rtb1,
                                       GatewayId=gtw_id)
            assert False, 'CreateRoute should have not succeeded'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "'10.10.10.23/24' is not a valid CIDR")
