from datetime import datetime
from threading import current_thread

from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tools.tina import create_tools
from qa_tina_tools.tools.tina import wait_tools
from qa_tina_tests.USER.PERF.perf_common import log_error


VOL_DEVICE = "/dev/xvdd"


def perf_volume(oscsdk, logger, queue, args):

    thread_name = current_thread().name
    # element names
    inst_name = 'pvol_inst_{}_{}'.format(args.az[:-1], thread_name)
    kp_name = 'pvol_kp_{}_{}'.format(args.az[:-1], thread_name)

    if not args.omi:
        logger.debug("OMI not specified, select default OMI")
        omi = oscsdk.config.region.get_info(constants.CENTOS_LATEST)
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

    # check instance
    inst = None
    if result['status'] != "KO":
        logger.debug("Describe Instance")
        try:
            ret = oscsdk.fcu.DescribeInstances(Filter=[{'Name': 'tag:Name', 'Value': inst_name}])
            if ret.response.reservationSet:
                for res in ret.response.reservationSet:
                    for i in res.instancesSet:
                        for bdn in i.blockDeviceMapping:
                            if bdn.deviceName == VOL_DEVICE:
                                logger.debug("Detach and Delete Volume")
                                oscsdk.fcu.DetachVolume(VolumeId=bdn.ebs.volumeId)
                                wait_tools.wait_volumes_state(oscsdk, [bdn.ebs.volumeId], state='available')
                                oscsdk.fcu.DeleteVolume(VolumeId=bdn.ebs.volumeId)
                        if i.instanceState.name == 'running':
                            inst = i.instanceId
                            break
                        if i.instanceState.name == 'stopped':
                            oscsdk.fcu.StartInstances(InstanceId=[i.instanceId])
                            wait_tools.wait_instances_state(oscsdk, [i.instanceId], state='ready')
                            inst = i.instanceId
                            break
        except Exception as error:
            log_error(logger, error, "Unexpected error while checking test instance", result)

    if not kp and result['status'] != "KO":
        try:
            create_tools.create_keypair(oscsdk, name=kp_name)
            wait_tools.wait_keypairs_state(oscsdk, [kp_name])
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating key pair", result)

    if not inst and result['status'] != "KO":

        logger.debug("Run instance")
        try:
            inst = oscsdk.fcu.RunInstances(ImageId=omi, MinCount=1, MaxCount=1, InstanceType=inst_type,
                                           KeyName=kp_name).response.instancesSet[0].instanceId
            wait_tools.wait_instances_state(oscsdk, [inst], state='ready')
            oscsdk.fcu.CreateTags(ResourceId=inst, Tag=[{'Key': 'Name', 'Value': inst_name}])

        except Exception as error:
            log_error(logger, error, "Unexpected error while creating test instance", result)

    volume_id = None
    if result['status'] != "KO":
        try:
            logger.debug("Create volume")
            start_create_vol = datetime.now()
            vol = oscsdk.fcu.CreateVolume(AvailabilityZone=args.az, Size=args.volume_size, VolumeType=args.volume_type)
            # time_create_vol = (datetime.now() - start_create_vol).total_seconds()
            volume_id = vol.response.volumeId
            # result['vol_create'] = time_create_vol
            # logger.debug("Volume creation time: %.2f", time_create_vol)
            logger.debug("Wait volume initialization")
            wait_tools.wait_volumes_state(oscsdk, [volume_id], state='available')
            time_vol_init = (datetime.now() - start_create_vol).total_seconds()
            result['vol_create'] = time_vol_init
            logger.debug("Volume initialization time: %.2f", time_vol_init)

        except Exception as error:
            log_error(logger, error, "Unexpected error while creating volume", result)

    if result['status'] != "KO":
        if volume_id:
            try:
                logger.debug("Attach volume")
                start_vol_attach = datetime.now()
                oscsdk.fcu.AttachVolume(Device=VOL_DEVICE, InstanceId=inst, VolumeId=volume_id)
                logger.debug("Wait volume attachement")
                wait_tools.wait_volumes_state(oscsdk, [volume_id], state='in-use')
                time_vol_attach = (datetime.now() - start_vol_attach).total_seconds()
                result['vol_attach'] = time_vol_attach
                logger.debug("Volume attachement time: %.2f", time_vol_attach)

                logger.debug("Detach volume")
                start_vol_detach = datetime.now()
                oscsdk.fcu.DetachVolume(VolumeId=volume_id)
                logger.debug("Wait volume detachement")
                wait_tools.wait_volumes_state(oscsdk, [volume_id], state='available')
                time_vol_detach = (datetime.now() - start_vol_detach).total_seconds()
                result['vol_detach'] = time_vol_detach
                logger.debug("Volume detachement time: %.2f", time_vol_detach)

            except Exception as error:
                log_error(logger, error, "Unexpected error while doing volume handling", result)

    if volume_id:
        try:
            logger.debug("Delete Volume")
            start_vol_deletion_time = datetime.now()
            oscsdk.fcu.DeleteVolume(VolumeId=volume_id)
            wait_tools.wait_volumes_state(oscsdk, [volume_id], cleanup=True)
            vol_deletion_time = (datetime.now() - start_vol_deletion_time).total_seconds()
            result['vol_delete'] = vol_deletion_time
        except Exception as error:
            log_error(logger, error, "Unexpected error while deleting volume", result)

    queue.put(result.copy())
