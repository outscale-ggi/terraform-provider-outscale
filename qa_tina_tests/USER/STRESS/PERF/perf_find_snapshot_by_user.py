#!/usr/bin/env python

from __future__ import division

import argparse
from datetime import datetime
import logging
from multiprocessing import Queue
import ssl
from threading import Thread, current_thread
import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.ssh import SshTools
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, PATH, KEY_PAIR, INSTANCE_SET
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
# ssl._create_default_https_context = ssl._create_unverified_context

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


def create_snapshot(oscsdk, kp_info, inst_info, vol_id, device, args, queue):
    thread_name = current_thread().name
    logger.info("Start test: %s", thread_name)
    result = {'status': 'OK'}
    waiting_snapshots = []

    try:
        # connect to instance
        sshclient = SshTools.check_connection_paramiko(inst_info['ipAddress'], kp_info[PATH],
                                                       username=oscsdk.config.region.get_info(constants.CENTOS_USER))

        # format / mount /write to volume
        cmd = 'sudo mkfs.ext4 -F {}'.format(device)
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko(sshclient, cmd)
        cmd = 'sudo mkdir ' + thread_name
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko(sshclient, cmd)
        cmd = 'sudo mount ' + device + ' ' + thread_name
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko(sshclient, cmd)
        cmd = 'cd  ' + thread_name
        logger.info("Executing: %s", cmd)
        SshTools.exec_command_paramiko(sshclient, cmd)

        num = 0
        write_errors = 0
        while num < args.write_number:
            try:
                cmd = 'sudo openssl rand -out ' + thread_name + str(num) + '.txt -base64 $((' + str(args.write_size) + ' * 2**20 * 3/4))'
                logger.info("Executing: %s", cmd)
                SshTools.exec_command_paramiko(sshclient, cmd)
                write_errors = 0
                logger.info("Snapshot volume")
                try:
                    snap = oscsdk.fcu.CreateSnapshot(VolumeId=vol_id).response
                    num += 1
                    try:
                        wait_snapshots_state(oscsdk, [snap.snapshotId], state='completed')
                    except AssertionError as error:
                        logger.info('Error occurred while waiting snapshot status ... ')
                        logger.info(str(error))
                        waiting_snapshots.append(snap.snapshotId)
                except OscApiException as error:
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

    result['waiting'] = waiting_snapshots
    queue.put(result)


def run(args):

    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))

#     if not args.omi:
#         logger.debug("OMI not specified, select default OMI")
#         omi = oscsdk.config.region.get_info("default_ami")
#     else:
#         omi = args.omi
#
#     if not args.instance_type:
#         logger.debug("Instance type not specified, select default instance type")
#         inst_type = oscsdk.config.region.get_info("default_instance_type")
#     else:
#         inst_type = args.instance_type

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
            print('Could not describe snapshot')

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

            # thread_name = 'tss'
            volume_ids = []
            vol_device = {}

            try:
                logger.debug("Create instance")
                inst_info = create_instances(oscsdk, nb=args.volume_number)

                logger.debug("Create volumes")
                _, volume_ids = create_volumes(oscsdk, count=args.volume_number, state='available')

                logger.debug("Attach volume(s)")
                for i in range(args.volume_number):
                    device = DEV + chr(START_DEV_CHAR + i)
                    oscsdk.fcu.AttachVolume(Device=device, InstanceId=inst_info[INSTANCE_ID_LIST][i], VolumeId=volume_ids[i])
                    vol_device[volume_ids[i]] = device

                logger.debug("Wait volume attachement")
                wait_volumes_state(oscsdk, volume_ids, state='in-use', cleanup=False)

            except Exception as error:
                logger.info("Error occurred while initializing test setup")
                init_error = error

            logger.info("Stop initializing test setup")

            nb_ok = 0
            nb_ko = 0

            if not init_error:

                queue = Queue()
                threads = []
                i = 0
                logger.info("Start workers")
                for i in range(args.volume_number):
                    # def test_snapshot(conn, keyPath, ipAddress, volId, device, args, queue):
                    proc = Thread(name="pfsbu-{}".format(i), target=create_snapshot, args=[oscsdk, inst_info[KEY_PAIR], inst_info[INSTANCE_SET][i],
                                                                                           volume_ids[i], vol_device[volume_ids[i]], args, queue])
                    threads.append(proc)
                    proc.start()

                logger.info("Wait workers")
                for proc in threads:
                    proc.join()

                waiting_snapshots = []

                logger.info("Get results")
                while not queue.empty():
                    res = queue.get()
                    for key in res.keys():
                        if key == "status":
                            if res[key] == "OK":
                                nb_ok += 1
                            else:
                                nb_ko += 1
                        elif key == 'waiting':
                            waiting_snapshots.append(res[key])
                    logger.debug(res)
                logger.info("OK = %d - KO = %d", nb_ok, nb_ko)
                logger.info("nb waitingSnapshots = %d", waiting_snapshots)

        logger.info("Start deleting test setup")
        try:
            if volume_ids:
                for vol_id in volume_ids:
                    oscsdk.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(oscsdk, volume_ids, state='available')
                delete_volumes(oscsdk, volume_ids)
            if inst_info:
                delete_instances(oscsdk, inst_info)
        except Exception as error:
            logger.info('Error occurred while deleting test setup')
        logger.info("End deleting test setup")

    if not init_error:
        logger.info("Start testing describe snapshot")
        queue = Queue()
        threads = []
        logger.info("Start workers")
        for i in range(args.desc_snap):
            # def test_snapshot(conn, keyPath, ipAddress, volId, device, args, queue):
            proc = Thread(name="pfsbu-{}".format(i + 1), target=describe_snapshot, args=[oscsdk, queue])
            threads.append(proc)
            proc.start()

        logger.info("Wait workers")
        for proc in threads:
            proc.join()

        logger.info("Get results")
        errors = 0
        sucess = 0
        nb_ok = 0
        nb_ko = 0
        total_time = 0
        while not queue.empty():
            res = queue.get()
            for key in res.keys():
                if key == "status":
                    if res[key] == "OK":
                        nb_ok += 1
                    else:
                        nb_ko += 1
                elif key == 'ns':
                    pass
                elif key == 'time':
                    if res[key] == 0:
                        errors += 1
                    else:
                        sucess += 1
                        total_time += res[key]
            logger.debug(res)

        logger.info("OK = %d - KO = %d", nb_ok, nb_ko)
        logger.info("Tries = %d - Errors = %d", sucess, errors)
        logger.info("total_time = %f - Mean = %f", total_time, total_time / args.desc_snap)


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
                        required=False, type=int, default=20, help='number of volumes, default 20')
    args_p.add_argument('-vs', '--volume_size', dest='volume_size', action='store',
                        required=False, type=int, default=10, help='Size of volumes in Go, default 10')
    args_p.add_argument('-vt', '--volume_type', dest='volume_type', action='store',
                        required=False, type=str, default='standard', help='Type of volumes, standard')
    args_p.add_argument('-sn', '--snap_num', dest='snap_number', action='store',
                        required=False, type=int, default=20000, help='Number of write iteration, default 20000')
    args_p.add_argument('-ws', '--write_size', dest='write_size', action='store',
                        required=False, type=int, default=10, help='Size of data written in Mo, default 10')
    args_p.add_argument('-ds', '--desc_snap', dest='desc_snap', action='store',
                        required=False, type=int, default=1, help='Number of concurrent describes, default 10')
    args_p.add_argument('-ni', '--no_init', dest='no_init', action='store_true',
                        required=False, help='No snapshots will be created')
    main_args = args_p.parse_args()

    run(main_args)
