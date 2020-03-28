#!/usr/bin/env python
# -*- coding: utf-8 -*-
# test description
# use user (args.region, args.account) from ~/.osc_credentials
# create key pair
# create security group
# create rule to open ssh
# create volumes (args.vol_number < 26, args.volume_size, args.volume_type)
# create instance (args.instance_type, args.omi --> defaults in region.py)
# attach volumes to instance
# for each volume test snapshot
#    on instance execute
#        mkfs, mkdir, mount
#    repeat operation (args.write_number)
#        write data on disk (args.write_size)
#        snapshot volume

from threading import Thread, current_thread
from multiprocessing import Queue
import time
import argparse
import logging
import ssl

from osc_common.exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.ssh import SshTools
from qa_common_tools.config import config_constants as constants
from qa_common_tools.osc_sdk import OscSdk
from qa_common_tools.config import OscConfig
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, PATH, KEY_PAIR, INSTANCE_SET
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context
LOGGING_LEVEL = logging.DEBUG
OSC_CREDENTIALS = "~/.osc_credentials"
OSC_LIB = "boto"
DEV = '/dev/xvd'
START_DEV_CHAR = 98
MAX_WRITE_ERRORS = 10


def describe_snapshot(oscsdk, queue):
    result = {'status': 'OK'}
    result['time'] = 0
    try:
        tmp = datetime.now()
        ret = oscsdk.fcu.DescribeSnapshots(Owner=[oscsdk.config.account.account_id]).response
        result['ns'] = len(ret.snapshotSet)
        result['time'] = (datetime.now() - tmp).total_seconds()
    except Exception:
        result = {'status': 'KO'}
    queue.put(result)


def delete_snapshot(oscsdk, snap_ids, queue):
    result = {'status': 'OK'}
    result['time'] = 0
    try:
        tmp = datetime.now()
        for snap_id in snap_ids:
            oscsdk.fcu.DeleteSnapshot(SnapshotId=snap_id).response
        result['time'] = (datetime.now() - tmp).total_seconds()
    except Exception:
        result = {'status': 'KO'}
    queue.put(result)


def create_snapshot(oscsdk, kp_info, inst_info, volId, VOLDEVice, args, queue):
    thread_name = current_thread().name
    logger.info("Start test: %s", thread_name)
    result = {'status': 'OK'}
    waitingSnapshots = []
    snap_ids = []

    try:
        # connect to instance
        sshclient = SshTools.check_connection_paramiko(inst_info['ipAddress'], kp_info[PATH],
                                                       username=oscsdk.config.region.get_info(constants.CENTOS_USER))

        # format / mount /write to volume
        cmd = 'sudo mkfs.ext4 -F {}'.format(device)
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko_2(sshclient, cmd)
        cmd = 'sudo mkdir ' + thread_name
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko_2(sshclient, cmd)
        cmd = 'sudo mount ' + device + ' ' + thread_name
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko_2(sshclient, cmd)
        cmd = 'cd  ' + thread_name
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko_2(sshclient, cmd)

        num = 0
        write_errors = 0
        while num < args.write_number:
            try:
                cmd = 'sudo openssl rand -out ' + thread_name + str(num) + '.txt -base64 $((' + str(args.write_size) + ' * 2**20 * 3/4))'
                logger.info("Executing: %s", cmd)
                SshTools.exec_command_paramiko_2(sshclient, cmd)
                write_errors = 0
                logger.info("Snapshot volume")
                try:
                    snap = oscsdk.fcu.CreateSnapshot(VolumeId=volId).response
                    snap_ids.append(snap.snapshotId)
                    num += 1
                    try:
                        wait_snapshots_state(oscsdk, [snap.snapshotId], state='completed')
                    except AssertionError as error:
                        logger.info('Error occurred while waiting snapshot status ... ')
                        logger.info(str(error))
                        waitingSnapshots.append(snap.snapshotId)
                except Exception as error:
                    if hasattr(error, 'error_code') and error.error_code == 'ConcurrentSnapshotLimitExceeded':
                        time.sleep(1)
                    else:
                        logger.info('Error occurred while snapshotting ... ')
                        logger.info(str(error))
                        result['status'] = "KO"

            except Exception as error:
                logger.info('Error occurred while writing ... ')
                write_errors += 1
                if write_errors > MAX_WRITE_ERRORS:
                    break

    except Exception as error:
        logger.info('Error occurred while setting up ... ')
        result['status'] = "KO"

    # snapshot volume (delay 200 ms, to be refined)

    result['waiting'] = waitingSnapshots
    result['snap_ids'] = snap_ids
    queue.put(result)


if __name__ == '__main__':

    logger = logging.getLogger('perf')

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter('[%(asctime)s] ' +
                          '[%(levelname)8s]' +
                          '[%(threadName)s] ' +
                          '[%(module)s.%(funcName)s():%(lineno)d]: ' +
                          '%(message)s', '%m/%d/%Y %H:%M:%S'))

    logger.setLevel(level=LOGGING_LEVEL)
    logger.addHandler(log_handler)

    logging.getLogger('tools').addHandler(log_handler)
    logging.getLogger('tools').setLevel(level=LOGGING_LEVEL)

    args_p = argparse.ArgumentParser(description="Test platform performances",
                                     formatter_class=argparse.RawTextHelpFormatter)

    args_p.add_argument('-r', '--region-az', dest='az', action='store',
                        required=True, type=str,
                        help='Selected Outscale region AZ for the test')
    args_p.add_argument('-a', '--account', dest='account', action='store',
                        required=True, type=str, help='Set account used for the test')
    args_p.add_argument('-o', '--omi', dest='omi', action='store',
                        required=False, type=str, help='OMI for the test')
    args_p.add_argument('-i', '--instance_type', dest='instance_type', action='store',
                        required=False, type=str, help='Instance type for the test')
    args_p.add_argument('-vn', '--volume_number', dest='volume_number', action='store',
                        required=False, type=int, default=10, help='number of volumes, default 20')
    args_p.add_argument('-vs', '--volume_size', dest='volume_size', action='store',
                        required=False, type=int, default=10, help='Size of volumes in Go, default 10')
    args_p.add_argument('-vt', '--volume_type', dest='volume_type', action='store',
                        required=False, type=str, default='standard', help='Type of volumes, standard')
    args_p.add_argument('-sn', '--snap_num', dest='snap_number', action='store',
                        required=False, type=int, default=500, help='Number of write iteration, default 20000')
    args_p.add_argument('-ws', '--write_size', dest='write_size', action='store',
                        required=False, type=int, default=10, help='Size of data written in Mo, default 10')
    args_p.add_argument('-ds', '--desc_snap', dest='desc_snap', action='store',
                        required=False, type=int, default=1, help='Number of concurrent describes, default 10')
    args_p.add_argument('-ni', '--no_init', dest='no_init', action='store_true',
                        required=False, help='No snapshots will be created')
    args_p.add_argument('-gc', '--snap_gc', dest='snap_gc', action='store',
                        required=False, type=bool, default=1, help='execute snapshot gc or no')
    args = args_p.parse_args()

    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))

    if not args.omi:
        logger.debug("OMI not specified, select default OMI")
        OMI = oscsdk.config.region.get_info(constants.DEFAULT_AMI)
    else:
        OMI = args.omi

    if not args.instance_type:
        logger.debug("Instance type not specified, select default instance type")
        INST_TYPE = oscsdk.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
    else:
        INST_TYPE = args.instance_type

    # logger.info("Clean all remaining resources")
    # CONN.tools.cleanupInstances()
    # CONN.tools.cleanupSnapshots()
    # CONN.tools.cleanupVolumes()
    # CONN.tools.cleanupSecurityGroups()
    # CONN.tools.cleanupKeyPairs()
    # logger.info("Stop cleanup")

    init_error = None
    if not args.no_init:
        logger.info("check_existing resources")
        snap_number = 0
        try:
            ret = oscsdk.fcu.DescribeSnapshots(Owner=[oscsdk.config.account.account_id]).response
            snap_number = len(ret.snapshotSet)
        except Exception as error:
            pass

        inst_info = None

        if snap_number < args.snap_number:
            diff = args.snap_number - snap_number
            if diff < args.volume_number:
                setattr(args, 'volume_number', diff)
                setattr(args, 'write_number', 1)
            else:
                setattr(args, 'write_number', diff // args.volume_number)

            logger.info("Start initializing test setup")

            # result = {'status': 'OK'}

            thread_name = 'tss'
            VOLUME_IDS = []
            VOLDEV = {}

            try:
                logger.debug("Create instance")
                inst_info = create_instances(oscsdk, nb=args.volume_number)

                logger.debug("Create volumes")
                _, VOLUME_IDS = create_volumes(oscsdk, count=args.volume_number, state='available')

                logger.debug("Attach volume(s)")
                for i in range(args.volume_number):
                    device = DEV + chr(START_DEV_CHAR + i)
                    oscsdk.fcu.AttachVolume(Device=device, InstanceId=inst_info[INSTANCE_ID_LIST][i], VolumeId=VOLUME_IDS[i])
                    VOLDEV[VOLUME_IDS[i]] = device

                logger.debug("Wait volume attachement")
                wait_volumes_state(oscsdk, VOLUME_IDS, state='in-use', cleanup=False)

            except Exception as error:
                logger.info("Error occurred while initializing test setup")
                init_error = error

            logger.info("Stop initializing test setup")

            NB_OK = 0
            NB_KO = 0

            if not init_error:
                QUEUE = Queue()
                threads = []
                i = 0
                logger.info("Start workers")
                for i in range(args.volume_number):
                    # def test_snapshot(conn, keyPath, ipAddress, volId, device, args, queue):
                    t = Thread(name="pfsbu-{}".format(i), target=create_snapshot, args=[oscsdk, inst_info[KEY_PAIR], inst_info[INSTANCE_SET][i],
                                                                                        VOLUME_IDS[i], VOLDEV[VOLUME_IDS[i]], args, QUEUE])
                    threads.append(t)
                    t.start()

                logger.info("Wait workers")
                for i in range(len(threads)):
                    threads[i].join()

                waitingSnapshots = []
                Snapshot_ids = []

                logger.info("Get results")
                while not QUEUE.empty():
                    res = QUEUE.get()
                    for key in res.keys():
                        if key == "status":
                            if res[key] == "OK":
                                NB_OK += 1
                            else:
                                NB_KO += 1
                        elif key == 'waiting':
                            waitingSnapshots.append(res[key])
                        elif key == 'snap_ids':
                            Snapshot_ids.append(res[key])
                    logger.debug(res)
                logger.info("OK = {} - KO = {}".format(NB_OK, NB_KO))
                logger.info("nb waitingSnapshots = {}".format(waitingSnapshots))

        logger.info("Start deleting test setup")
        try:
            if VOLUME_IDS:
                for volId in VOLUME_IDS:
                    oscsdk.fcu.DetachVolume(VolumeId=volId)
                wait_volumes_state(oscsdk, VOLUME_IDS, state='available')
                delete_volumes(oscsdk, VOLUME_IDS)
            if inst_info:
                delete_instances(oscsdk, inst_info)
        except Exception as error:
            logger.info('Error occurred while deleting test setup')
        logger.info("End deleting test setup")

        if not init_error:
            QUEUE = Queue()
            threads = []
            i = 0
            logger.info("Start workers")
            for ids in Snapshot_ids:
                # def test_snapshot(conn, keyPath, ipAddress, volId, device, args, queue):
                t = Thread(name="pfsbu-{}".format(i), target=delete_snapshot, args=[oscsdk, ids, QUEUE])
                i = i+1
                threads.append(t)
                t.start()

            logger.info("Wait workers")
            for i in range(len(threads)):
                threads[i].join()
            if args.snap_gc:
                for _ in range(10):
                    try:
                        oscsdk.intel.snapshot.gc()
                    except OscApiException as error:
                        print(error)
                        assert_error(error, 200, 0, 'locked')

            logger.info("Get results")
            while not QUEUE.empty():
                res = QUEUE.get()
                for key in res.keys():
                    if key == "status":
                        if res[key] == "OK":
                            NB_OK += 1
                        else:
                            NB_KO += 1
                logger.debug(res)
            logger.info("OK = {} - KO = {}".format(NB_OK, NB_KO))
