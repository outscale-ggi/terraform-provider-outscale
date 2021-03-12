from datetime import datetime
from threading import current_thread
import time

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_volumes_state, \
    wait_keypairs_state, wait_security_groups_state, wait_snapshots_state
from qa_tina_tests.USER.PERF.perf_common import log_error


MAX_WAIT_TIME = 1800

DEV = '/dev/xvdb'


def perf_snapshot(oscsdk, logger, queue, args):

    thread_name = current_thread().name

    # element names
    inst_name = 'psnap_inst_{}'.format(thread_name)
    kp_name = 'psnap_kp_{}_{}_{}'.format(args.account, args.az[:-1], thread_name)
    sg_name = 'psnap_sg_{}'.format(thread_name)
    vol_name = 'psnap_vol_{}'.format(thread_name)
    volume_id_list = []

    if not args.omi:
        logger.debug("OMI not specified, select default OMI")
        omi = oscsdk.config.region.get_info(constants.CENTOS7)
    else:
        omi = args.omi

    if not args.inst_type:
        logger.debug("Instance type not specified, select default instance type")
        inst_type = oscsdk.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
    else:
        inst_type = args.inst_type

    result = {'status': 'OK'}

    # check key pair
    kp = False
    if result['status'] != "KO":
        logger.debug("Describe Keypair")
        try:
            ret = oscsdk.fcu.DescribeKeyPairs(Filter=[{'Name': 'key-name', 'Value': kp_name}])
            kp = ret.response.keySet and len(ret.response.keySet) == 1
        except Exception as error:
            log_error(logger, error, "Unexpected error while checking key pair", result)

    # check security group
    sg = None
    if result['status'] != "KO":
        logger.debug("Describe Security Group")
        try:
            ret = oscsdk.fcu.DescribeSecurityGroups(Filter=[{'Name': 'group-name', 'Value': sg_name}]).response.securityGroupInfo
            if ret:
                sg = ret[0].groupId
        except Exception as error:
            log_error(logger, error, "Unexpected error while checking security group", result)

    vol = None
    # check volume
    if result['status'] != "KO":
        logger.debug("Describe Volume")
        try:
            ret = oscsdk.fcu.DescribeVolumes(Filter=[{'Name': 'tag:Name', 'Value': vol_name}]).response.volumeSet
            if ret:
                vol = ret[0].volumeId
        except Exception as error:
            log_error(logger, error, "Unexpected error while checking volume", result)

    # check instance
    inst = None
    if result['status'] != "KO":
        logger.debug("Describe Instance")
        try:
            ret = oscsdk.fcu.DescribeInstances(Filter=[{'Name': 'tag:Name', 'Value': inst_name}])
            if ret.response.reservationSet:
                for res in ret.response.reservationSet:
                    for i in res.instancesSet:
                        if i.instanceState.name == 'running':
                            inst = i
                            break
                        if i.instanceState.name == 'stopped':
                            oscsdk.fcu.StartInstances(InstanceId=[i.instanceId])
                            wait_instances_state(oscsdk, [i.instanceId], state='ready')
                            inst = i
                            break
                if inst:
                    for volumes in inst.blockDeviceMapping:
                        volume_id_list.append(volumes.ebs.volumeId)

        except Exception as error:
            log_error(logger, error, "Unexpected error while checking test instance", result)

    if not kp and result['status'] != "KO":
        try:
            create_keypair(oscsdk, name=kp_name)
            wait_keypairs_state(oscsdk, [kp_name])
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating key pair", result)

    if not sg and result['status'] != "KO":
        try:
            sg = oscsdk.fcu.CreateSecurityGroup(GroupName=sg_name,
                                                GroupDescription='Security_Group_For_{}'.format(thread_name)).response.groupId
            wait_security_groups_state(oscsdk, [sg])

            logger.debug("Allow SSH in SG")
            oscsdk.fcu.AuthorizeSecurityGroupIngress(GroupId=sg, FromPort='22', ToPort='22', IpProtocol='tcp',
                                                     CidrIp=Configuration.get('cidr', 'allips'))
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating security group", result)

    if not vol and result['status'] != "KO":
        try:
            vol = oscsdk.fcu.CreateVolume(AvailabilityZone=args.az, Size=args.volume_size, VolumeType=args.volume_type).response.volumeId
            wait_volumes_state(oscsdk, [vol], state='available')
            oscsdk.fcu.CreateTags(ResourceId=vol, Tag=[{'Key': 'Name', 'Value': vol_name}])
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating volume", result)

    if not inst and result['status'] != "KO":

        logger.debug("Run instance")
        try:
            inst = oscsdk.fcu.RunInstances(ImageId=omi, MinCount=1, MaxCount=1, InstanceType=inst_type,
                                           SecurityGroup=[sg], KeyName=kp_name, Placement={'AvailabilityZone':args.az}).response.instancesSet[0]
            wait_instances_state(oscsdk, [inst.instanceId], state='ready')
            oscsdk.fcu.CreateTags(ResourceId=inst.instanceId, Tag=[{'Key': 'Name', 'Value': inst_name}])

        except Exception as error:
            log_error(logger, error, "Unexpected error while creating test instance", result)

        if result['status'] != "KO":
            try:
                oscsdk.fcu.AttachVolume(Device=DEV, InstanceId=inst.instanceId, VolumeId=vol)
                wait_volumes_state(oscsdk, [vol], state='in-use')
                ret = oscsdk.fcu.DescribeInstances(Filter=[{'Name': 'tag:Name', 'Value': inst_name},
                                                           {'Name': 'instance-state-name', 'Value': 'running'}])
                for volumes in ret.response.reservationSet[0].instancesSet[0].blockDeviceMapping:
                    volume_id_list.append(volumes.ebs.volumeId)
                inst = ret.response.reservationSet[0].instancesSet[0]
                sshclient = SshTools.check_connection_paramiko(inst.ipAddress, '/tmp/{}.pem'.format(kp_name),
                                                               username=oscsdk.config.region.get_info(constants.CENTOS_USER))
                cmd = 'sudo mkfs.xfs -f {}'.format(DEV)
                SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=600, retry=1)
            except Exception as error:
                log_error(logger, error, "Unexpected error while doing volume handling", result)

    if result['status'] != "KO":

        #print(inst.display())
        sshclient = SshTools.check_connection_paramiko(inst.ipAddress, '/tmp/{}.pem'.format(kp_name),
                                                       username=oscsdk.config.region.get_info(constants.CENTOS_USER))
        cmd = 'sudo mount -o nouuid {} /mnt'.format(DEV)
        SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
        cmd = 'sudo openssl rand -out /mnt/data_xxx.txt -base64 $(({} * 2**20 * 3/4))'.format(100)
        SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)
        cmd = 'sudo umount /mnt'
        SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=300)

        # get snapshot list
        snap_list = []
        ret = oscsdk.fcu.DescribeSnapshots(Filter=[{'Name': 'volume-id', 'Value': volume_id_list}])
        if ret.response.snapshotSet:
            snap_list = [s.snapshotId for s in ret.response.snapshotSet]

        for i, volume_id in enumerate(volume_id_list):

            logger.info("Snapshot volume")
            try:
                snap_id = None
                start_status_snapshot = datetime.now()
                ret = oscsdk.fcu.CreateSnapshot(VolumeId=volume_id)
                time_snap = (datetime.now() - start_status_snapshot).total_seconds()
                result['snap_call_%s' % (i)] = time_snap
                snap_id = ret.response.snapshotId
                ret = oscsdk.fcu.DescribeSnapshots(Filter=[{'Name': 'snapshot-id', 'Value': snap_id}])
                prev_state = ret.response.snapshotSet[0].status
                logger.debug("*** INIT STATUS: %s", prev_state)
                stop_states = ['completed', 'error']
                while (datetime.now() - start_status_snapshot).total_seconds() < MAX_WAIT_TIME:
                    ret = oscsdk.fcu.DescribeSnapshots(Filter=[{'Name': 'snapshot-id', 'Value': snap_id}])
                    status_snap = ret.response.snapshotSet[0].status
                    logger.debug("*** ACTUAL STATUS: %s", status_snap)
                    if status_snap != prev_state:
                        time_snap = (datetime.now() - start_status_snapshot).total_seconds()
                        result['snap_%s_%s' % (prev_state, i)] = time_snap
                    if status_snap in stop_states:
                        break
                    prev_state = status_snap
                    time.sleep(0.75)
                #if snapId:
                #    logger.debug("Terminate snapshot")

                #    start_status_snapshot = datetime.now()
                #    ret = oscsdk.fcu.DeleteSnapshot(SnapshotId=snapId)
                #    wait_snapshots_state(osc_sdk=oscsdk, snapshot_id_list=[snapId], cleanup=True)
                #    time_snap = (datetime.now() - start_status_snapshot).total_seconds()
                #    result['snap_delete_%s' % (i)] = time_snap
            except Exception as error:
                log_error(logger, error, "Error occurred while snapshotting ...", result)

        for snap in snap_list:
            ret = oscsdk.fcu.DeleteSnapshot(SnapshotId=snap)
            wait_snapshots_state(osc_sdk=oscsdk, snapshot_id_list=[snap], cleanup=True)

    queue.put(result.copy())
