

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_snapshots_state, wait_volumes_state
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import get_data_file_chain, get_md5sum, write_and_snap


# Snapshots creation:
# $ python  qa_tina/ADMIN/FUNCTIONAL/streaming/base.py -r <az> -a <account>
# StreaminBase v2
class StreamingBase(OscTestSuite):

    w_size = 10
    v_size = 10
    qemu_version = '2.12'
    rebase_enabled = True
    snap_attached = True
    inst_type = 'c4.large'
    inst_az = 'a'
    vol_type = 'standard'
    iops = None
    base_snap_id = 10
    new_snap_count = 1  # > 1
    branch_id = None  # [0, new_snap_count-1]
    fio = False
    ref_account_id = '412911315810'  # qa+streaming@outscale.com on IN2
    inst_running = False
    inst_stopped = False
    check_data = False

    #
    # SETUP:
    #
    #  snap_S(base_snap_id)_from_vol_(v_size)G_with_write_(w_size)M --> ref_snap_id from ref account
    #                   /           x = base_snap_id + branch_id
    #                  /              /           y = n + new_snap_count
    #                 /              /              /
    # S0 --- ... --- Sn --- ... --- Sx --- ... --- Sy --- V1
    #                                 `--- ... ___ Sz ___ V2
    #

    @classmethod
    def setup_class(cls):
        cls.sshclient = None
        cls.inst_info = None
        cls.ref_snap_id = None
        cls.vol_1_id = None
        cls.vol_2_id = None
        cls.vol_1_snap_list = []
        cls.vol_2_snap_list = []
        cls.vol_1_df_list = []
        cls.vol_2_df_list = []
        cls.inst_running_info = None
        cls.inst_stopped_info = None
        cls.attached = False
        cls.md5sum_before = None
        super(StreamingBase, cls).setup_class()
        if cls.a1_r1.config.region.name == 'in-west-1':
            cls.ref_account_id = '785704195831'  # qa+streaming@outscale.com on IN1
        if cls.a1_r1.config.region.name == 'in-west-2':
            cls.ref_account_id = '412911315810'  # qa+streaming@outscale.com on IN2
        try:
            # if cls.a1_r1.config.region.name == 'in-west-2':
            #    cls.rebase_enabled = True
            # elif cls.a1_r1.config.region.name == 'in-west-1':
            #    cls.rebase_enabled = False
            # create inst
            if cls.qemu_version == '2.12':
                cls.inst_info = create_instances(
                    cls.a1_r1, state='running', inst_type=cls.inst_type, az='{}{}'.format(cls.a1_r1.config.region.name, cls.inst_az)
                )
            else:
                cls.inst_info = create_instances(
                    cls.a1_r1, state='running', inst_type=cls.inst_type, dedicated=True, az='{}{}'.format(cls.a1_r1.config.region.name, cls.inst_az)
                )

            if cls.inst_running:
                cls.inst_running_info = create_instances(
                    cls.a1_r1, state='running', inst_type=cls.inst_type, az='{}{}'.format(cls.a1_r1.config.region.name, cls.inst_az)
                )
            if cls.inst_stopped:
                cls.inst_stopped_info = create_instances(
                    cls.a1_r1, state=None, inst_type=cls.inst_type, az='{}{}'.format(cls.a1_r1.config.region.name, cls.inst_az)
                )

            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.inst_info[INSTANCE_ID_LIST], state='ready')

            cls.sshclient = SshTools.check_connection_paramiko(
                cls.inst_info[INSTANCE_SET][0]['ipAddress'],
                cls.inst_info[KEY_PAIR][PATH],
                username=cls.a1_r1.config.region.get_info(constants.CENTOS_USER),
            )

            if cls.fio:
                cmd = 'sudo yum install -y epel-release'
                SshTools.exec_command_paramiko(cls.sshclient, cmd)
                cmd = 'sudo yum install -y fio'
                SshTools.exec_command_paramiko(cls.sshclient, cmd)
            ret = cls.a1_r1.intel.snapshot.find(
                owner=[cls.ref_account_id], description='snap_S{}_from_vol_{}G_with_write_{}M'.format(cls.base_snap_id - 1, cls.v_size, cls.w_size)
            )
            if ret.response.result and len(ret.response.result) == 1:
                cls.ref_snap_id = ret.response.result[0].id
            else:
                assert False, "Ref snapshot not found"
            # share snap
            cls.a1_r1.intel.snapshot.add_permissions(owner=cls.ref_account_id, snapshot=cls.ref_snap_id, users=[cls.a1_r1.config.account.account_id])

            if cls.inst_stopped:
                wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.inst_stopped_info[INSTANCE_ID_LIST], state='running')
                cls.a1_r1.fcu.StopInstances(InstanceId=cls.inst_stopped_info[INSTANCE_ID_LIST], Force=True)
                wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=cls.inst_stopped_info[INSTANCE_ID_LIST], state='stopped')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            # unshare snap
            cls.a1_r1.intel.snapshot.remove_permissions(
                owner=cls.ref_account_id, snapshot=cls.ref_snap_id, users=[cls.a1_r1.config.account.account_id]
            )
            # delete inst
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.inst_running_info:
                delete_instances(cls.a1_r1, cls.inst_running_info)
            if cls.inst_stopped_info:
                delete_instances(cls.a1_r1, cls.inst_stopped_info)
        finally:
            super(StreamingBase, cls).teardown_class()

    def setup_method(self, method):
        super(StreamingBase, self).setup_method(method)
        self.vol_1_id = None
        self.vol_2_id = None
        self.vol_1_snap_list = []
        self.vol_2_snap_list = []
        self.vol_1_df_list = []
        self.vol_2_df_list = []
        self.attached = False
        self.md5sum_before = None
        try:
            # create vol v1
            _, [self.vol_1_id] = create_volumes(
                self.a1_r1,
                snapshot_id=self.ref_snap_id,
                size=self.v_size,
                volume_type=self.vol_type,
                iops=self.iops,
                availability_zone='{}{}'.format(self.a1_r1.config.region.name, self.inst_az),
            )
            wait_volumes_state(self.a1_r1, [self.vol_1_id], 'available')
            for i in range(self.new_snap_count):
                snap_id = write_and_snap(
                    osc_sdk=self.a1_r1,
                    sshclient=self.sshclient,
                    inst_id=self.inst_info[INSTANCE_ID_LIST][0],
                    vol_id=self.vol_1_id,
                    f_num=i + self.base_snap_id,
                    w_size=self.w_size,
                    snap_attached=self.snap_attached,
                )
                self.vol_1_snap_list.append(snap_id)
                if self.branch_id:
                    if i == self.branch_id:
                        # create v2 from last v1 snap
                        _, [self.vol_2_id] = create_volumes(
                            self.a1_r1,
                            snapshot_id=self.vol_1_snap_list[-1],
                            size=self.v_size,
                            volume_type=self.vol_type,
                            iops=self.iops,
                            availability_zone='{}{}'.format(self.a1_r1.config.region.name, self.inst_az),
                        )
                    elif i > self.branch_id:
                        snap_id = write_and_snap(
                            osc_sdk=self.a1_r1,
                            sshclient=self.sshclient,
                            inst_id=self.inst_info[INSTANCE_ID_LIST][0],
                            vol_id=self.vol_2_id,
                            f_num=i + self.base_snap_id,
                            w_size=self.w_size,
                            snap_name="S{}_from_V2".format(i),
                            snap_attached=self.snap_attached,
                        )
                        self.vol_2_snap_list.append(snap_id)
            self.vol_1_df_list = get_data_file_chain(self.a1_r1, self.vol_1_id)
            self.logger.debug(self.vol_1_df_list)
            if self.branch_id:
                self.vol_2_df_list = get_data_file_chain(self.a1_r1, self.vol_2_id)
            if self.check_data:
                self.md5sum_before = get_md5sum(
                    osc_sdk=self.a1_r1, sshclient=self.sshclient, inst_id=self.inst_info[INSTANCE_ID_LIST][0], vol_id=self.vol_1_id
                )
                self.logger.debug("md5sum before: %s", self.md5sum_before)
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.check_data and self.md5sum_before:
                md5sum_after = get_md5sum(
                    osc_sdk=self.a1_r1, sshclient=self.sshclient, inst_id=self.inst_info[INSTANCE_ID_LIST][0], vol_id=self.vol_1_id
                )
                self.logger.debug("md5sum after: %s", md5sum_after)
                assert self.md5sum_before == md5sum_after
            # delete snap*
            for snap_id in self.vol_1_snap_list:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
            for snap_id in self.vol_2_snap_list:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
                wait_snapshots_state(osc_sdk=self.a1_r1, cleanup=True, snapshot_id_list=[snap_id])
            # delete v1
            if self.vol_1_id:
                delete_volumes(self.a1_r1, [self.vol_1_id])
            # delete v2
            if self.vol_2_id:
                delete_volumes(self.a1_r1, [self.vol_2_id])
        finally:
            super(StreamingBase, self).teardown_method(method)

    def check_no_stream(self):
        data_file_after = get_data_file_chain(self.a1_r1, res_id=self.vol_1_id)
        self.logger.debug(data_file_after)
        self.logger.debug(self.vol_1_df_list)
        assert len(data_file_after) == len(self.vol_1_df_list)
        assert data_file_after == self.vol_1_df_list

    def check_stream_full(self, nb_new_snap=0, mode="HOT"):
        data_file_after = get_data_file_chain(self.a1_r1, res_id=self.vol_1_id)
        self.logger.debug(data_file_after)
        self.logger.debug(self.vol_1_df_list)
        self.logger.debug(len(data_file_after))
        self.logger.debug(2 + nb_new_snap)
        if self.rebase_enabled and mode != "HOT":
            assert len(data_file_after) == 3 + nb_new_snap
            assert data_file_after[0 + nb_new_snap] == self.vol_1_df_list[0]
            assert data_file_after[1 + nb_new_snap] == self.vol_1_df_list[1]
            assert data_file_after[2 + nb_new_snap] == self.vol_1_df_list[-1]
        else:
            assert len(data_file_after) == 2 + nb_new_snap
            assert data_file_after[0 + nb_new_snap] == self.vol_1_df_list[0]
            assert data_file_after[1 + nb_new_snap] == self.vol_1_df_list[1]

    def check_stream_inter(self, nb_new_snap=0):
        data_file_after = get_data_file_chain(self.a1_r1, res_id=self.vol_1_id)
        self.logger.debug(data_file_after)
        self.logger.debug(self.vol_1_df_list)
        assert len(data_file_after) == 5 + nb_new_snap
        assert data_file_after[0 + nb_new_snap] == self.vol_1_df_list[0]
        assert data_file_after[1 + nb_new_snap] == self.vol_1_df_list[1]
        assert data_file_after[2 + nb_new_snap] == self.vol_1_df_list[-3]
        assert data_file_after[3 + nb_new_snap] == self.vol_1_df_list[-2]
        assert data_file_after[4 + nb_new_snap] == self.vol_1_df_list[-1]
