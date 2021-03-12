from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import  assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNETS, SUBNET_ID
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc


class Test_DeleteNetworkInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.network_interface_id = None
        super(Test_DeleteNetworkInterface, cls).setup_class()
        try:
            # create VPC
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=1)
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
            super(Test_DeleteNetworkInterface, cls).teardown_class()

    def setup_method(self, method):
        self.network_interface_id = None
        try:
            res_create = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID],
                                                               PrivateIpAddress=Configuration.get('ipaddress', '10_0_1_4'))
            self.network_interface_id = res_create.response.networkInterface.networkInterfaceId
        finally:
            OscTestSuite.setup_method(self, method)

    def teardown_method(self, method):
        try:
            if self.network_interface_id:
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=self.network_interface_id)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T4036_valid_params(self):
        self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=self.network_interface_id)
        self.network_interface_id = None

    def test_T4037_empty_network_interface_id(self):
        try:
            self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId="")
            self.network_interface_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: NetworkInterfaceId")

    def test_T4038_none_network_interface_id(self):
        try:
            self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=None)
            self.network_interface_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: NetworkInterfaceId")

    def test_T4039_without_params(self):
        try:
            self.a1_r1.fcu.DeleteNetworkInterface()
            self.network_interface_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: NetworkInterfaceId")

    def test_T4040_with_another_account(self):
        try:
            self.a2_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=self.network_interface_id)
            self.network_interface_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400,
                         "InvalidNetworkInterfaceID.NotFound", "The networkInterface ID '{}' does not exist".format(self.network_interface_id))

    def test_T4041_non_existent_network_interface_id(self):
        try:
            self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId="eni-01234567")
            self.network_interface_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidNetworkInterfaceID.NotFound", "The networkInterface ID 'eni-01234567' does not exist")

    def test_T4042_invalid_network_interface_id(self):
        try:
            self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId="XYZ0123456789")
            self.network_interface_id = None
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidNetworkInterfaceID.Malformed", "Invalid ID received: XYZ0123456789. Expected format: eni-")
