
from qa_test_tools.config import config_constants as constants

from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import SUBNETS, INSTANCE_SET, SUBNET_ID, KEY_PAIR, PATH, SECURITY_GROUP_ID
from qa_common_tools.ssh import SshTools, OscSshError
from qa_tina_tools.tools.tina.wait_tools import wait_network_interfaces_state


class Test_fni(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_fni, cls).setup_class()
        cls.info = None
        cls.vpc_info = None
        cls.vpc_eip1 = None
        cls.vpc_eip2 = None
        cls.vpc_inst1 = None
        cls.vpc_inst2 = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=2, no_eip=True, omi_id='')
            cls.vpc_inst1 = cls.vpc_info[SUBNETS][0][INSTANCE_SET][0]
            cls.vpc_inst2 = cls.vpc_info[SUBNETS][0][INSTANCE_SET][1]
            # allocate vpc_eip1
            cls.vpc_eip1 = cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response
            # allocate vpc_eip2
            cls.vpc_eip2 = cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_eip1:
                cls.a1_r1.fcu.ReleaseAddress(AllocationId=cls.vpc_eip1.allocationId)
            if cls.vpc_eip2:
                cls.a1_r1.fcu.ReleaseAddress(AllocationId=cls.vpc_eip2.allocationId)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_fni, cls).teardown_class()

    def test_T213_create_attach_private(self):
        inst_assoc_id = None
        fni_id = None
        fni_assoc_id = None
        fni_att_id = None
        try:
            # associate eip1 to instance1
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.vpc_eip1.allocationId, InstanceId=self.vpc_inst1['instanceId'])
            inst_assoc_id = ret.response.associationId
            # create fni
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID],
                                                        SecurityGroupId=self.vpc_info[SUBNETS][0][SECURITY_GROUP_ID])
            fni_id = ret.response.networkInterface.networkInterfaceId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
            # associate eip2 to fni
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.vpc_eip2.allocationId, NetworkInterfaceId=fni_id)
            fni_assoc_id = ret.response.associationId
            # attach fni to instance1
            ret = self.a1_r1.fcu.AttachNetworkInterface(NetworkInterfaceId=fni_id, InstanceId=self.vpc_inst1['instanceId'], DeviceIndex=1)
            fni_att_id = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            # connect to instance via eip1
            SshTools.check_connection_paramiko(self.vpc_eip1.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                               username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # connect to instance via eip2
            try:
                SshTools.check_connection_paramiko(self.vpc_eip2.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                                   username=self.a1_r1.config.region.get_info(constants.CENTOS_USER), retry=3)
            except OscSshError:
                known_error('NO TICKET', 'Could not connect to instance through fni, rpm not on default omi')
            assert False, 'Remove known error code'
        finally:
            # detach and delete fni
            if fni_att_id:
                self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_att_id)
            if fni_assoc_id:
                # for now as association id is incorrect
                # self.a1_r1.fcu.DisassociateAddress(AssociationId=fni_assoc_id)
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eip2.publicIp)
            if fni_id:
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)
            if inst_assoc_id:
                # for now as association id is incorrect
                # self.a1_r1.fcu.DisassociateAddress(AssociationId=inst_assoc_id)
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eip1.publicIp)

    def test_T221_create_attach_detach(self):
        inst_assoc_id = None
        fni_id = None
        fni_assoc_id = None
        fni_att_id = None
        try:
            # associate eip1 to instance1
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.vpc_eip1.allocationId, InstanceId=self.vpc_inst1['instanceId'])
            inst_assoc_id = ret.response.associationId
            # create fni
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID],
                                                        SecurityGroupId=self.vpc_info[SUBNETS][0][SECURITY_GROUP_ID])
            fni_id = ret.response.networkInterface.networkInterfaceId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
            # associate eip2 to fni
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.vpc_eip2.allocationId, NetworkInterfaceId=fni_id)
            fni_assoc_id = ret.response.associationId
            # attach fni to instance1
            ret = self.a1_r1.fcu.AttachNetworkInterface(NetworkInterfaceId=fni_id, InstanceId=self.vpc_inst1['instanceId'], DeviceIndex=1)
            fni_att_id = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            # connect to instance1 via eip1
            SshTools.check_connection_paramiko(self.vpc_eip1.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                               username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # connect to instance1 via eip2
            try:
                SshTools.check_connection_paramiko(self.vpc_eip2.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                                   username=self.a1_r1.config.region.get_info(constants.CENTOS_USER), retry=3)
            except OscSshError:
                known_error('NO TICKET', 'Could not connect to instance through fni, rpm not on default omi')
            assert False, 'Remove known error code'
            # detach fni from instance1
            self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_att_id)
            fni_att_id = None
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
            # attch fni to instance2
            ret = self.a1_r1.fcu.AttachNetworkInterface(NetworkInterfaceId=fni_id, InstanceId=self.vpc_inst2['instanceId'], DeviceIndex=1)
            fni_att_id = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            # connect to instance2 via eip2
            SshTools.check_connection_paramiko(self.vpc_eip2.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                               username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        finally:
            # detach and delete fni
            if fni_att_id:
                self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_att_id)
            if fni_assoc_id:
                # for now as association id is incorrect
                # self.a1_r1.fcu.DisassociateAddress(AssociationId=fni_assoc_id)
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eip2.publicIp)
            if fni_id:
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)
            if inst_assoc_id:
                # for now as association id is incorrect
                # self.a1_r1.fcu.DisassociateAddress(AssociationId=inst_assoc_id)
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eip1.publicIp)

    def test_T222_create_attach_multiple(self):
        fni_id = None
        fni_assoc_id = None
        fni_att_id = None
        inst_assoc_id = None
        try:
            # associate eip1 to instance1
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.vpc_eip1.allocationId, InstanceId=self.vpc_inst1['instanceId'])
            inst_assoc_id = ret.response.associationId
            # create fni
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID],
                                                        SecurityGroupId=self.vpc_info[SUBNETS][0][SECURITY_GROUP_ID])
            fni_id = ret.response.networkInterface.networkInterfaceId
            # associate eip2 to fni
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.vpc_eip2.allocationId, NetworkInterfaceId=fni_id)
            fni_assoc_id = ret.response.associationId
            # attach fni to instance1
            ret = self.a1_r1.fcu.AttachNetworkInterface(NetworkInterfaceId=fni_id, InstanceId=self.vpc_inst2['instanceId'], DeviceIndex=1)
            fni_att_id = ret.response.attachmentId
            wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='in-use')
            # connect to instance1 via eip1
            SshTools.check_connection_paramiko(self.vpc_eip1.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                               username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # connect to instance1 via eip2
            try:
                SshTools.check_connection_paramiko(self.vpc_eip2.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                                   username=self.a1_r1.config.region.get_info(constants.CENTOS_USER), retry=3)
            except OscSshError as error:
                known_error('NO TICKET', 'Could not connect to instance through fni, rpm not on default omi')
            assert False, 'Remove known error code'
            self.a1_r1.fcu.AssignPrivateIpAddresses(NetworkInterfaceId=fni_id, SecondaryPrivateIpAddressCount=1)
            ret = self.a1_r1.fcu.DescribeNetworkInterfaces(NetworkInterfaceId=[fni_id])
            private_addresses = ret.response.networkInterfaceSet[0].privateIpAddressesSet
            # copy ssh key on instance1
            sshclient = SshTools.check_connection_paramiko(self.vpc_eip1.publicIp, self.vpc_info[KEY_PAIR][PATH],
                                                           username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # read file and save it on distant machine
            with open(self.vpc_info[KEY_PAIR][PATH], 'r') as content_file:
                content = content_file.read()

            cmd = "sudo echo '" + content + "' > " + self.vpc_info[KEY_PAIR][PATH]
            out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            self.logger.info(out)
            # put file
            # SshTools.transfer_file_sftp(sshclient, self.vpc_info[KEY_PAIR][PATH], self.vpc_info[KEY_PAIR][PATH])

            for private_address in private_addresses:
                sshclient_jhost = SshTools.check_connection_paramiko_nested(sshclient=sshclient,
                                                                            ip_address=self.vpc_eip2.response.publicIp,
                                                                            ssh_key=self.vpc_info[KEY_PAIR][PATH],
                                                                            local_private_addr=self.vpc_eip1.publicIp,
                                                                            dest_private_addr=private_address,
                                                                            username=self.a1_r1.config.region.get_info(constants.CENTOS_USER),
                                                                            retry=4, timeout=10)
                cmd = "sudo ls"
                out, _, _ = SshTools.exec_command_paramiko(sshclient_jhost, cmd)
                self.logger.vpc_info(out)

        # for debug purposes
        except Exception as error:
            raise error
        finally:
            # detach and delete fni
            if fni_att_id:
                self.a1_r1.fcu.DetachNetworkInterface(AttachmentId=fni_att_id)
            if fni_assoc_id:
                # for now as association id is incorrect
                # self.a1_r1.fcu.DisassociateAddress(AssociationId=fni_assoc_id)
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eip2.publicIp)
            if fni_id:
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[fni_id], state='available')
                self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)
            if inst_assoc_id:
                # for now as association id is incorrect
                # self.a1_r1.fcu.DisassociateAddress(AssociationId=inst_assoc_id)
                self.a1_r1.fcu.DisassociateAddress(PublicIp=self.vpc_eip1.publicIp)
