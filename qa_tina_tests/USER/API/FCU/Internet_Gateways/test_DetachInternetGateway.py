from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_internet_gateways_state


class Test_DetachInternetGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.igw_id = None
        cls.att = None
        super(Test_DetachInternetGateway, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, igw=False)
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
            super(Test_DetachInternetGateway, cls).teardown_class()

    def setup_method(self, method):
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

    def test_T3923_valid_params(self):
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
        self.att = None
        self.igw_id = None

    def test_T3924_missing_vpc_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id)
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: VpcID")
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
                self.att = None
                self.igw_id = None

    def test_T3925_none_vpc_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=None)
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: VpcID")
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                wait_internet_gateways_state(self.a1_r1, [self.igw_id], state='detached')
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3926_invalid_vpc_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId="123456789012")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.Malformed', "Invalid ID received: 123456789012. Expected format: vpc-")
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3927_unknown_vpc_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId="vpc-12345678")
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'Gateway.NotAttached', "resource " + str(self.igw_id) + " is not attached to network vpc-12345678")
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3929_incorrect_type_vpc_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=[self.vpc_info[VPC_ID]])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'VpcID' must be of type: string. Received: {{'1': '{}'}}".format(self.vpc_info[VPC_ID]))
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3930_missing_igw_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(VpcId=self.vpc_info[VPC_ID])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: GatewayID')
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3931_none_igw_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=None, VpcId=self.vpc_info[VPC_ID])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: GatewayID')
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3933_invalid_igw_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId="123456789", VpcId=self.vpc_info[VPC_ID])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidInternetGatewayID.Malformed", "Invalid ID received: 123456789. Expected format: igw-")
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3938_unknown_igw_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId="igw-12345678", VpcId=self.vpc_info[VPC_ID])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidInternetGatewayID.NotFound", "The InternetGatewayId 'igw-12345678' does not exist")
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3941_incorrect_type_igw_id(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=[self.igw_id], VpcId=self.vpc_info[VPC_ID])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'InternetGatewayID' must be of type: string. Received: {{'1': '{}'}}".format(self.igw_id))
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None

    def test_T3943_from_another_account(self):
        detach_result = None
        self.att = self.a1_r1.fcu.AttachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
        try:
            detach_result = self.a2_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
            assert False, "Call should not be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidInternetGatewayID.NotFound", "The InternetGatewayId '{}' does not exist".format(self.igw_id))
        finally:
            if not detach_result:
                self.a1_r1.fcu.DetachInternetGateway(InternetGatewayId=self.igw_id, VpcId=self.vpc_info[VPC_ID])
                self.att = None
            self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.igw_id)
            self.igw_id = None
