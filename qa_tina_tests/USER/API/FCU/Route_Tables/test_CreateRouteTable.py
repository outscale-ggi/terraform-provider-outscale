from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID


class Test_CreateRouteTable(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        super(Test_CreateRouteTable, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
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
        finally:
            super(Test_CreateRouteTable, cls).teardown_class()

    def test_T4261_missing_vpcid(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.fcu.CreateRouteTable()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: VpcID')
        finally:
            if ret_create:
                self.a1_r1.fcu.DeleteRouteTable(RouteTableId=ret_create.response.routeTable.routeTableId)

    def test_T4262_unknown_vpcid(self):
        try:
            self.a1_r1.fcu.CreateRouteTable(VpcId='vpc-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.NotFound', "The vpc ID 'vpc-12345678' does not exist")

    def test_T4263_invalid_vpcid(self):
        try:
            self.a1_r1.fcu.CreateRouteTable(VpcId='XXXXXXXX')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.Malformed', 'Invalid ID received: XXXXXXXX. Expected format: vpc-')

    def test_T4264_invalid_vpcid_type(self):
        try:
            self.a1_r1.fcu.CreateRouteTable(VpcId=[self.vpc_info[VPC_ID]])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'VpcID' must be of type: string. Received: {{'1': '{}'}}".format(self.vpc_info[VPC_ID]))

    def test_T4265_valid_params(self):
        ret_create = None
        try:
            ret_create = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID])
        finally:
            if ret_create:
                self.a1_r1.fcu.DeleteRouteTable(RouteTableId=ret_create.response.routeTable.routeTableId)
