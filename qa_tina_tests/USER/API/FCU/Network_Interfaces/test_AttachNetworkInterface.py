from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, detach_network_interface
from qa_tina_tools.tools.tina.info_keys import SUBNETS, SUBNET_ID, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_network_interfaces_state


class Test_AttachNetworkInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.ni_id = None
        cls.att_id = None
        super(Test_AttachNetworkInterface, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, igw=False, nb_instance=1)
            ret = cls.a1_r1.fcu.CreateNetworkInterface(SubnetId=cls.vpc_info[SUBNETS][0][SUBNET_ID])
            cls.ni_id = ret.response.networkInterface.networkInterfaceId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ni_id:
                try:
                    cls.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=cls.ni_id)
                except:
                    pass
            if cls.vpc_info:
                try:
                    delete_vpc(cls.a1_r1, cls.vpc_info)
                except:
                    pass
        except Exception as error:
            raise error
        finally:
            super(Test_AttachNetworkInterface, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.att_id = None

    def teardown_method(self, method):
        try:
            if self.att_id:
                wait_network_interfaces_state(self.a1_r1, [self.ni_id], state='in-use')
                detach_network_interface(self.a1_r1, self.ni_id, self.att_id)
                wait_network_interfaces_state(self.a1_r1, [self.ni_id], state='available',)
        except Exception as error:
            raise error
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T1704_missing_instance_id(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(NetworkInterfaceId=self.ni_id, DeviceIndex=1).response.attachmentId
            assert False, 'Call should not have been successful, missing InstanceId'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: InstanceID')

    def test_T1705_missing_network_interface_id(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                                DeviceIndex=1).response.attachmentId
            assert False, 'Call should not have been successful, missing NetworkInterfaceId'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: NetworkInterfaceId')

    def test_T1706_missing_device_index(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                                NetworkInterfaceId=self.ni_id).response.attachmentId
            assert False, 'Call should not have been successful, missing DeviceIndex'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: DeviceIndex')

    def test_T1707_invalid_instance_id(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId='xxx-12345678',
                                                                NetworkInterfaceId=self.ni_id, DeviceIndex=1).response.attachmentId
            assert False, 'Call should not have been successful, missing InstanceId'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.Malformed', 'Invalid ID received: xxx-12345678. Expected format: i-')

    def test_T1708_unknown_instance_id(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId='i-12345678',
                                                                NetworkInterfaceId=self.ni_id, DeviceIndex=1).response.attachmentId
            assert False, 'Call should not have been successful, missing InstanceId'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', 'The instance IDs do not exist: i-12345678')

    def test_T1709_invalid_network_interface_id(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                                NetworkInterfaceId='xxx-12345678', DeviceIndex=1).response.attachmentId
            assert False, 'Call should not have been successful, missing InstanceId'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidNetworkInterfaceID.Malformed', 'Invalid ID received: xxx-12345678. Expected format: eni-')

    def test_T1710_unknown_network_interface_id(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                                NetworkInterfaceId='eni-12345678', DeviceIndex=1).response.attachmentId
            assert False, 'Call should not have been successful, missing InstanceId'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidNetworkInterfaceID.NotFound', "The networkInterface ID 'eni-12345678' does not exist")

    def test_T1711_invalid_device_index(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                                NetworkInterfaceId=self.ni_id, DeviceIndex='abc').response.attachmentId
            assert False, 'Call should not have been successful, missing InstanceId'
        except OscApiException as error:
            assert_error(error, 400, 'OWS.Error', 'Request is not valid.')

    def test_T1712_unknown_device_index(self):
        try:
            self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                                NetworkInterfaceId=self.ni_id, DeviceIndex=12345678).response.attachmentId
            assert False, 'Call should not have been successful, missing InstanceId'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value of parameter 'DeviceIndex' is not valid: 12345678. Supported values: (1, 7), please interpret 'None' as no-limit.")

    def test_T1703_with_valid_params(self):
        self.att_id = self.a1_r1.fcu.AttachNetworkInterface(InstanceId=self.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0],
                                                            NetworkInterfaceId=self.ni_id, DeviceIndex=1).response.attachmentId
