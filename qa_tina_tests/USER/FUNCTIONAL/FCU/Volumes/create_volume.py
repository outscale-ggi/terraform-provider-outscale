import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import check_volume
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_tina_tools.tools.tina.create_tools import create_volumes, create_instances_old, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_keypair
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


class CreateVolume(OscTestSuite):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(CreateVolume, cls).setup_class()
        unique_id = id_generator()
        cls.sg_name = 'sg_test_T55_{}'.format(unique_id)
        ip_ingress = Configuration.get('cidr', 'allips')

        cls.public_ip_inst = None
        cls.inst_id = None
        cls.volume_id = None
        cls.kp_info = None
        cls.sshclient = None

        try:

            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name)

            sg_id = sg_response.response.groupId

            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=cls.sg_name, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=ip_ingress)

            # create key pair
            cls.kp_info = create_keypair(cls.a1_r1)

            # run instance
            ret, id_list = create_instances_old(cls.a1_r1, security_group_id_list=[sg_id], key_name=cls.kp_info[NAME],
                                                state='ready', inst_type='m4.xlarge')
            cls.inst_id = id_list[0]
            cls.public_ip_inst = ret.response.reservationSet[0].instancesSet[0].ipAddress

            cls.sshclient = SshTools.check_connection_paramiko(cls.public_ip_inst, cls.kp_info[PATH],
                                                               username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))

        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:

            if cls.inst_id:
                # terminate the instance
                delete_instances_old(cls.a1_r1, [cls.inst_id])
            if cls.kp_info:
                delete_keypair(cls.a1_r1, cls.kp_info)

            if cls.sg_name:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupName=cls.sg_name)

        finally:
            super(CreateVolume, cls).teardown_class()

    def create_volume(self, volume_type='standard', iops=None, volume_size=8, perf_iops=False, drive_letter_code='b', no_delete=False):
        try:
            attachement = False
            dev = '/dev/xvd{}'.format(drive_letter_code)
            self.volume_id = None

            _, vol_id_list = create_volumes(self.a1_r1, volume_type=volume_type, size=volume_size, state='available', iops=iops)

            self.volume_id = vol_id_list[0]

            self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_id, VolumeId=self.volume_id, Device=dev)
            attachement = True
            wait_volumes_state(self.a1_r1, [self.volume_id], state='in-use', cleanup=False, threshold=20, wait_time=3)
            check_volume(self.sshclient, dev, volume_size, perf_iops=perf_iops, volume_type=volume_type, iops_io1=iops)
        finally:
            try:

                if not no_delete and self.volume_id:
                    if attachement:
                        self.a1_r1.fcu.DetachVolume(VolumeId=self.volume_id)
                        wait_volumes_state(self.a1_r1, [self.volume_id], state='available', cleanup=False, threshold=20, wait_time=3)
                    self.a1_r1.fcu.DeleteVolume(VolumeId=self.volume_id)

            except Exception as error:
                pytest.fail("An unexpected error happened while cleaning: " + str(error))
