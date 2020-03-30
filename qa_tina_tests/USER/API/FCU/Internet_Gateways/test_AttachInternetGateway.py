from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID


class Test_AttachInternetGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        super(Test_AttachInternetGateway, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, igw=False)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_AttachInternetGateway, cls).teardown_class()

    def setup_method(self, method):
        self.igw_id = None
        self.att = None
        OscTestSuite.setup_method(self, method)
        self.igw_id = self.a1_r1.fcu.CreateInternetGateway().response.internetGateway.internetGatewayId

    def teardown_method(self, method):
        try:
            if self.att:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
            if self.igw_id:
                self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T1690_valid_params(self):
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])

    def test_T1691_missing_vpc_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id)
            assert(False, 'Call should have failed, missing vpc id')
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: VpcID")

    def test_T1692_none_vpc_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=None)
            assert(False, 'Call should have failed, missing vpc id')
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: VpcID")

    def test_T1693_invalid_vpc_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId='123456789012')
            assert(False, 'Call should have failed, invalid vpc id')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.Malformed', "Invalid ID received: 123456789012. Expected format: vpc-")

    def test_T1694_unknown_vpc_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId='vpc-12345678')
            assert(False, 'Call should have failed, unknown vpc id')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.NotFound', "The vpc ID 'vpc-12345678' does not exist")

    def test_T1695_incorrect_type_vpc_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=[self.vpc_info[VPC_ID]])
            assert(False, 'Call should have failed, incorrect vpc id')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'VpcID' must be of type: string. Received: {{'1': '{}'}}".format(self.vpc_info[VPC_ID]))

    def test_T1696_missing_igw_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(VpcId=self.vpc_info[VPC_ID])
            assert(False, 'Call should have failed, unknown igw id')
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: GatewayID')

    def test_T1697_none_igw_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=None, VpcId=self.vpc_info[VPC_ID])
            assert(False, 'Call should have failed, unknown igw id')
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: GatewayID')

    def test_T1698_invalid_igw_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId='123456789012', VpcId=self.vpc_info[VPC_ID])
            assert(False, 'Call should have failed, invalid igw id')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInternetGatewayID.Malformed', "Invalid ID received: 123456789012. Expected format: igw-")

    def test_T1699_unknown_igw_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId='igw-12345678', VpcId=self.vpc_info[VPC_ID])
            assert(False, 'Call should have failed, unknown igw id')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInternetGatewayID.NotFound', "The InternetGatewayId 'igw-12345678' does not exist")

    def test_T1700_incorrect_type_igw_id(self):
        try:
            self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=[self.igw_id], VpcId=self.vpc_info[VPC_ID])
            assert(False, 'Call should have failed, incorrect type igw id')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'InternetGatewayID' must be of type: string. Received: {{'1': '{}'}}".format(self.igw_id))
            
    def test_T3944_from_another_account(self):
        try :
            self.att = self.a2_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidInternetGatewayID.NotFound", "The InternetGatewayId '{}' does not exist".format(self.igw_id))
