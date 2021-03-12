

import time

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import format_mount_volume, umount_volume
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes, delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, PATH, KEY_PAIR
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_instances_state


NB_VOL = 10
CMD = 'ls -lsa /dev/x*'


class Test_attach_detach(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.vol_ids = []
        super(Test_attach_detach, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1)
            _, cls.vol_ids = create_volumes(cls.a1_r1, state='available', count=NB_VOL)
            ret_desc = wait_instances_state(cls.a1_r1, cls.inst_info[INSTANCE_ID_LIST], state='ready')
            cls.sshclient = SshTools.check_connection_paramiko(ret_desc.response.reservationSet[0].instancesSet[0].ipAddress,
                                                               cls.inst_info[KEY_PAIR][PATH],
                                                               username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER))
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vol_ids:
                delete_volumes(cls.a1_r1, cls.vol_ids)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_attach_detach, cls).teardown_class()

    def test_T3185_multiple_attach_detach(self):
        # check volumes are available
        wait_volumes_state(self.a1_r1, self.vol_ids, state='available')
        for i in range(NB_VOL):
            letter = chr(98 + i)
            device = '/dev/xvd{}'.format(letter)
            vol_mount = '/mnt/mnt' + letter
            ret_attach = None
            try:
                ret_attach = self.a1_r1.fcu.AttachVolume(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], VolumeId=self.vol_ids[i], Device=device)
                wait_volumes_state(self.a1_r1, [self.vol_ids[i]], state='in-use')

                out, status, err = SshTools.exec_command_paramiko(self.sshclient, CMD)
                print('out = {} '.format(out))
                print('status = {} '.format(status))
                print('err = {} '.format(err))
                assert status == 0
                assert device in out

                format_mount_volume(self.sshclient, device, vol_mount, True)
                time.sleep(2)
                umount_volume(self.sshclient, vol_mount)

            finally:
                if ret_attach:
                    self.a1_r1.fcu.DetachVolume(VolumeId=self.vol_ids[i])
                    wait_volumes_state(self.a1_r1, [self.vol_ids[i]], state='available')

                    out, status, err = SshTools.exec_command_paramiko(self.sshclient, CMD, expected_status=2)
                    print('out = {} '.format(out))
                    print('status = {} '.format(status))
                    print('err = {} '.format(err))
                    assert status != 0
