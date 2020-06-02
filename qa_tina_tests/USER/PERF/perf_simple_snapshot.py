from datetime import datetime
from threading import current_thread
import time

from qa_test_tools.config.configuration import Configuration
from qa_test_tools.config import config_constants as constants
from qa_tina_tests.USER.PERF.perf_common import log_error
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_volumes_state,\
    wait_keypairs_state, wait_security_groups_state, wait_snapshots_state


MAX_WAIT_TIME = 1800

DEV = '/dev/xvdb'


def perf_simple_snapshot(oscsdk, logger, queue, args):

    thread_name = current_thread().name

    # element names
    inst_name = 'p_simple_snap_inst_{}'.format(thread_name)
    kp_name = 'p_simple_snap_kp_{}_{}'.format(args.az[:-1], thread_name)
    sg_name = 'p_simple_snap_sg_{}'.format(thread_name)

    if not args.omi:
        logger.debug("OMI not specified, select default OMI")
        OMI = oscsdk.config.region.get_info(constants.CENTOS7)
    else:
        OMI = args.omi

    if not args.inst_type:
        logger.debug("Instance type not specified, select default instance type")
        INST_TYPE = oscsdk.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
    else:
        INST_TYPE = args.inst_type

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
                        elif i.instanceState.name == 'stopped':
                            oscsdk.fcu.StartInstances(InstanceId=[i.instanceId])
                            wait_instances_state(oscsdk, [i.instanceId], state='ready')
                            inst = i
                            break

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

    if not inst and result['status'] != "KO":

        logger.debug("Run instance")
        try:
            inst = oscsdk.fcu.RunInstances(ImageId=OMI, MinCount=1, MaxCount=1, InstanceType=INST_TYPE,
                                           SecurityGroup=[sg], KeyName=kp_name).response.instancesSet[0]
            wait_instances_state(oscsdk, [inst.instanceId], state='ready')
            oscsdk.fcu.CreateTags(ResourceId=inst.instanceId, Tag=[{'Key': 'Name', 'Value': inst_name}])

        except Exception as error:
            log_error(logger, error, "Unexpected error while creating test instance", result)

    if result['status'] != "KO":
        vol = None
        attached = False
        snapId = None
        try:
            vol = oscsdk.fcu.CreateVolume(AvailabilityZone=args.az, Size=args.volume_size, VolumeType=args.volume_type).response.volumeId
            wait_volumes_state(oscsdk, [vol], state='available', nb_check=5)
            oscsdk.fcu.AttachVolume(Device=DEV, InstanceId=inst.instanceId, VolumeId=vol)
            wait_volumes_state(oscsdk, [vol], state='in-use', nb_check=5)
            attached = True
            logger.info("Snapshot volume")
            start_status_snapshot = datetime.now()
            ret = oscsdk.fcu.CreateSnapshot(VolumeId=vol)
            time_snap = (datetime.now() - start_status_snapshot).total_seconds()
            result['simple_snap_call'] = time_snap
            snapId = ret.response.snapshotId
            ret = oscsdk.fcu.DescribeSnapshots(Filter=[{'Name': 'snapshot-id', 'Value': snapId}])
            prev_state = ret.response.snapshotSet[0].status
            stop_states = ['completed', 'error']
            while (datetime.now() - start_status_snapshot).total_seconds() < MAX_WAIT_TIME:
                ret = oscsdk.fcu.DescribeSnapshots(Filter=[{'Name': 'snapshot-id', 'Value': snapId}])
                status_snap = ret.response.snapshotSet[0].status
                if status_snap != prev_state:
                    time_snap = (datetime.now() - start_status_snapshot).total_seconds()
                    result['simple_snap_%s' % (prev_state)] = time_snap
                if status_snap in stop_states:
                    break
                prev_state = status_snap
                time.sleep(0.5)
        except Exception as error:
            log_error(logger, error, "Error occurred while snapshotting ...", result)
        finally:
            if snapId:
                logger.debug("Terminate snapshot")
                start_status_snapshot = datetime.now()
                ret = oscsdk.fcu.DeleteSnapshot(SnapshotId=snapId)
                wait_snapshots_state(osc_sdk=oscsdk, snapshot_id_list=[snapId], cleanup=True)
                time_snap = (datetime.now() - start_status_snapshot).total_seconds()
                result['simple_snap_delete'] = time_snap
            if attached:
                oscsdk.fcu.DetachVolume(VolumeId=vol)
                wait_volumes_state(oscsdk, [vol], 'available', nb_check=5)
            if vol:
                oscsdk.fcu.DeleteVolume(VolumeId=vol)
                wait_volumes_state(osc_sdk=oscsdk, cleanup=True, volume_id_list=[vol])

    queue.put(result.copy())
