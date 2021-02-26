import time

from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state


def snap_exist(osc_sdk, snap_name):
    ret = osc_sdk.fcu.DescribeSnapshots(Filter=[{'Name': 'description', 'Value': [snap_name]}])
    if ret.response.snapshotSet:
        if len(ret.response.snapshotSet) == 1:
            return True
        if len(ret.response.snapshotSet) > 1:
            return True  # TODO: raise an exception
    return False


def write_data(sshclient, f_num, device='/dev/xvdc', folder='/mnt', w_size=10, fio=False):
    cmd = 'sudo mount -o nouuid {} {}'.format(device, folder)
    SshTools.exec_command_paramiko(sshclient, cmd)

    cmd = 'sudo openssl rand -out {}/data_{}.txt -base64 $(({} * 2**20 * 3/4))'.format(folder, f_num, w_size)
    SshTools.exec_command_paramiko(sshclient, cmd)
    cmd = 'sudo openssl rand -out {}/data_xxx.txt -base64 $(({} * 2**20 * 3/4))'.format(folder, w_size)
    SshTools.exec_command_paramiko(sshclient, cmd)

    if fio:
        cmd = (
            'sudo fio --filename={folder}/fio_{f_num} --name test_fio_{f_num} --direct=1 --rw=randwrite --bs=16k --size=10G --numjobs=16 '
            '--time_based --runtime=300 --group_reporting --norandommap'.format(folder=folder, f_num=f_num)
        )
        SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=330)

    cmd = 'sudo umount {}'.format(folder)
    SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)


def write_and_snap(
    osc_sdk, sshclient, inst_id, vol_id, f_num, device='/dev/xvdc', folder='/mnt', w_size=10, fio=False, snap_name=None, snap_attached=True
):

    if not snap_name:
        snap_name = "snap_S{}_with_write_{}".format(f_num, w_size)

    osc_sdk.fcu.AttachVolume(InstanceId=inst_id, VolumeId=vol_id, Device=device)
    wait_volumes_state(osc_sdk, [vol_id], state='in-use')

    write_data(sshclient, f_num, device, folder, w_size, fio)

    if not snap_attached:
        osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
        try:
            wait_volumes_state(osc_sdk, [vol_id], 'available')
        except AssertionError:
            osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
            wait_volumes_state(osc_sdk, [vol_id], 'available')

    if snap_exist(osc_sdk, snap_name):
        return None
    snap_id = osc_sdk.fcu.CreateSnapshot(VolumeId=vol_id, Description=snap_name).response.snapshotId
    wait_snapshots_state(osc_sdk=osc_sdk, state='completed', snapshot_id_list=[snap_id])

    if snap_attached:
        osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
        try:
            wait_volumes_state(osc_sdk, [vol_id], 'available')
        except AssertionError:
            osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
            wait_volumes_state(osc_sdk, [vol_id], 'available')

    return snap_id


def get_md5sum(osc_sdk, sshclient, inst_id, vol_id, device='/dev/xvdc', folder='/mnt'):
    # md5sum = None
    osc_sdk.fcu.AttachVolume(InstanceId=inst_id, VolumeId=vol_id, Device=device)
    wait_volumes_state(osc_sdk, [vol_id], state='in-use')

    cmd = 'sudo mount -o nouuid {} {}'.format(device, folder)
    SshTools.exec_command_paramiko(sshclient, cmd)

    cmd = 'sudo cat {}/data_*.txt | md5sum'.format(folder)
    out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
    md5sum = out.split(' ')[0]

    cmd = 'sudo umount {}'.format(folder)
    SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)

    osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
    try:
        wait_volumes_state(osc_sdk, [vol_id], 'available')
    except AssertionError:
        osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
        wait_volumes_state(osc_sdk, [vol_id], 'available')

    return md5sum


def get_data_file_chain(osc_sdk, res_id):
    if res_id.startswith('vol-'):
        ret = osc_sdk.intel.volume.find(id=res_id)
    elif res_id.startswith('snap-'):
        ret = osc_sdk.intel.snapshot.find(id=res_id)
    ret = osc_sdk.intel.storage.get_data_file_chain(file_id=ret.response.result[0].data_file)
    return [i.id for i in ret.response.result]


def write_on_device(sshclient, device, folder, f_num, size, with_md5sum, with_fio):
    """
        mount device
        write 2 files
        compute device md5sum
        unmount device
        return md5sum
    """
    # mount volume
    cmd = 'sudo mount -o nouuid {} {}'.format(device, folder)
    SshTools.exec_command_paramiko(sshclient, cmd)
    # write file
    cmd = 'sudo openssl rand -out {}/data_{}.txt -base64 $(({} * 2**20 * 3/4))'.format(folder, f_num, size)
    SshTools.exec_command_paramiko(sshclient, cmd)
    cmd = 'sudo openssl rand -out {}/data_xxx.txt -base64 $(({} * 2**20 * 3/4))'.format(folder, size)
    SshTools.exec_command_paramiko(sshclient, cmd)
    if with_fio and f_num in [1, 2, 3, 10]:
        cmd = (
            'sudo fio --filename={folder}/fio_{f_num} --name test_fio_{f_num} --direct=1 --rw=randwrite --bs=16k --size=10G --numjobs=16 '
            '--time_based --runtime=300 --group_reporting --norandommap'.format(folder=folder, f_num=f_num)
        )
        SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=330)
    # get md5sum
    if with_md5sum:
        cmd = 'sudo cat {}/data_*.txt | md5sum'.format(folder)
        out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
        md5sum = out.split(' ')[0]
    else:
        md5sum = None

    # unmount volume
    cmd = 'sudo umount {}'.format(folder)
    SshTools.exec_command_paramiko(sshclient, cmd)
    return md5sum


def read_on_device(sshclient, device, folder, with_md5sum):
    """
        mount device
        compute device md5sum
        unmount device
        return md5sum
    """
    # mount volume
    cmd = 'sudo mount -o nouuid {} {}'.format(device, folder)
    SshTools.exec_command_paramiko(sshclient, cmd)
    # get md5sum
    if with_md5sum:
        cmd = 'sudo cat {}/data_*.txt | md5sum'.format(folder)
        out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
        md5sum = out.split(' ')[0]
    else:
        md5sum = None
    # unmount volume
    cmd = 'sudo umount {}'.format(folder)
    SshTools.exec_command_paramiko(sshclient, cmd)
    return md5sum


def get_streaming_operation(osc_sdk, res_id, logger=None):
    if res_id.startswith('vol-'):
        ret = osc_sdk.intel.streaming.find_operations(volume=[res_id])
    elif res_id.startswith('snap-'):
        ret = osc_sdk.intel.streaming.find_operations(snapshot=[res_id])
    else:
        assert False, "Incorrect resource id, should be volume or snapshot"
    if logger:
        logger.debug(ret.response.display())
    return ret


def assert_streaming_state(osc_sdk, res_id, state, logger=None):
    ret = get_streaming_operation(osc_sdk=osc_sdk, res_id=res_id, logger=logger)
    assert ret.response.result, 'could not find streaming operation {}'.format(res_id)
    assert len(ret.response.result) == 1, 'could not find streaming operation {}'.format(res_id)
    assert ret.response.result[0].state == state, "{} == {} ?".format(ret.response.result[0].state, state)


def wait_streaming_state(osc_sdk, res_id, state='started', cleanup=False, sleep=5, max_it=100, logger=None):
    """
        wait until streaming operation completion
    """
    start_time = time.time()
    it = 0
    if res_id is None:
        assert False, "Missing value for resource id"
    while it < max_it:
        it += 1
        ret = get_streaming_operation(osc_sdk, res_id, logger)
        if not ret.response.result:
            if cleanup:
                elapsed_time = time.time() - start_time
                logger.debug("Wait streaming cleanup: %s", elapsed_time)
                return
            assert False, "Streaming operation not found"
        else:
            if len(ret.response.result) == 1:
                if not cleanup and ret.response.result[0].state == state:
                    elapsed_time = time.time() - start_time
                    logger.debug("Wait streaming %s: %s", state, elapsed_time)
                    return
                if cleanup and ret.response.result[0].state != 'started':
                    assert False, "Streaming operation not started"
            else:
                assert False, "Multiple streaming operation on same resource !!!"
        time.sleep(sleep)
    assert False, "Threshold reached for streaming operation"
