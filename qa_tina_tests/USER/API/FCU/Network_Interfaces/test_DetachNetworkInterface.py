
import time

from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config import config_constants as constants
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.delete_tools import delete_subnet, detach_network_interface
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_network_interfaces_state


class Test_DetachNetworkInterface(OscTestSuite):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_DetachNetworkInterface, cls).setup_class()
        cls.subnet1 = None
        cls.inst_id = None
        instance_type = cls.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
        try:
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId
            # create subnet 1
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet1_id = ret.response.subnet.subnetId
            # run instance
            inst = cls.a1_r1.fcu.RunInstances(ImageId=cls.a1_r1.config.region._conf[constants.CENTOS7], MaxCount='1', MinCount='1',
                                              InstanceType=instance_type, SubnetId=cls.subnet1_id)
            # get instance ID
            cls.inst_id = inst.response.instancesSet[0].instanceId
            # wait instance to become ready
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst_id], state='ready')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_id:
                # delete resources account 1
                # stop instance 1
                cls.a1_r1.fcu.TerminateInstances(InstanceId=[cls.inst_id])
                # replace by wait function
                wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.inst_id], state='terminated')
            delete_subnet(cls.a1_r1, cls.subnet1_id)
            cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)
        finally:
            super(Test_DetachNetworkInterface, cls).teardown_class()

    def test_T283_without_param(self):
        try:
            self.a1_r1.fcu.DetachNetworkInterface()
            assert False, "error should have been raised"
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: AttachmentID')

    def test_T337_invalid_att_id_foo(self):
        try:
            self.a1_r1.fcu.DetachNetworkInterface(AttachmentId='foo')
            assert False, "Error should have been raised"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidNetworkInterfaceAttachmentID.Malformed', 'Invalid ID received: foo. Expected format: eni-attach-')

    def test_T338_invalid_att_id_wf_not_exist(self):
        try:
            self.a1_r1.fcu.DetachNetworkInterface(AttachmentId='eni-attach-12345678')
            assert False, "Error should have been raised"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAttachmentID.NotFound', "The attachment 'eni-attach-12345678' does not exist.")

    def test_T339_invalid_att_id_wf_partially_exist(self):
        try:
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id)
            fni_id = ret.response.networkInterface.networkInterfaceId
            ret = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.inst_id, NetworkInterfaceId=fni_id)
            fni_asso_addr = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            fni_attach_invalid = '{}xxx{}'.format(fni_asso_addr[:11], fni_asso_addr[-8:])
            self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_attach_invalid)
            assert False, "Error should have been raised"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidNetworkInterfaceAttachmentID.Malformed', 'Invalid ID received: {}'.format(fni_attach_invalid))
        finally:
            time.sleep(10)  # TODO: rm / replace by lspci on instance..
            detach_network_interface(self.a1_r1, fni_id, fni_asso_addr)
            # self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
            self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)

    def test_T340_valid_attachment_id(self):
        fni_asso_addr = None
        fni_id = None
        try:
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id)
            fni_id = ret.response.networkInterface.networkInterfaceId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
            ret = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.inst_id, NetworkInterfaceId=fni_id)
            fni_asso_addr = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            time.sleep(10)  # TODO: rm / replace by lspci on instance..
            # ret = self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
            detach_network_interface(self.a1_r1, fni_id, fni_asso_addr)
        finally:
            if fni_id:
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)

    def test_T341_detach_already_detached(self):
        fni_asso_addr = None
        fni_id = None
        try:
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id)
            fni_id = ret.response.networkInterface.networkInterfaceId
            ret = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.inst_id, NetworkInterfaceId=fni_id)
            fni_asso_addr = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            time.sleep(10)  # TODO: rm / replace by lspci on instance..
            # first detach
            # self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
            detach_network_interface(self.a1_r1, fni_id, fni_asso_addr)
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
            # detach again
            self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
            assert False, "The api was expected to raise an exception"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAttachmentID.NotFound', "The attachment '{}' does not exist.".format(fni_asso_addr))
        finally:
            if fni_id:
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)

    def test_T342_detach_other_account(self):
        fni_asso_addr = None
        fni_id = None
        try:
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id)
            fni_id = ret.response.networkInterface.networkInterfaceId
            ret = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.inst_id, NetworkInterfaceId=fni_id)
            fni_asso_addr = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            time.sleep(10)  # TODO: rm / replace by lspci on instance..
            # first detach
            self.a2_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
            assert False, "The api was expected to raise an exception"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAttachmentID.NotFound', "The attachment '{}' does not exist.".format(fni_asso_addr))
        finally:
            if fni_asso_addr:
                # self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
                detach_network_interface(self.a1_r1, fni_id, fni_asso_addr)
            if fni_id:
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)

    def test_T343_attach_detach_without_delay(self):
        ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id)
        fni_id = ret.response.networkInterface.networkInterfaceId
        ret = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.inst_id, NetworkInterfaceId=fni_id)
        fni_asso_addr = ret.response.attachmentId
        ret = self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
        wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
        self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)

    def test_T3583_attach_fast_detach(self):
        fni_asso_addr = None
        fni_id = None
        try:
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id)
            fni_id = ret.response.networkInterface.networkInterfaceId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
            ret = self.a1_r1.fcu.AttachNetworkInterface(DeviceIndex='1', InstanceId=self.inst_id, NetworkInterfaceId=fni_id)
            fni_asso_addr = ret.response.attachmentId
            self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_asso_addr)
        except OscTestException as error:
            raise error
        except Exception as error:
            assert_error(error, 400, '', '')
        finally:
            if fni_id:
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)
