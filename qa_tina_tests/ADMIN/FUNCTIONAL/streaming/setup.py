import argparse
import logging

import urllib3

from qa_common_tools.ssh import SshTools
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_all
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state
from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import snap_exist, write_and_snap


DEFAULT_SNAP_CFG = [
    # nb_snap, vol_size, w_size, fio
    # (10, 10, 100, False),
    # (45, 10, 10, False),
    (45, 10, 20, False),
    # (20, 1000, 200, False)
]
INST_TYPE = 'c4.xlarge'


def setup_streaming_ressources(osc_sdk):
    inst_info = None
    vol_id = None
    try:
        for snap_cfg in DEFAULT_SNAP_CFG:
            snap_name = 'snap_S{}_from_vol_{}G_with_write_{}M'.format(snap_cfg[0] - 1, snap_cfg[1], snap_cfg[2])
            if snap_exist(osc_sdk, snap_name):
                continue
            logger.debug('Init snapshots creation...')
            if not inst_info:
                inst_info = create_instances(osc_sdk, state='ready', inst_type=INST_TYPE)
            _, [vol_id] = create_volumes(osc_sdk, size=snap_cfg[1])
            wait_volumes_state(osc_sdk, [vol_id], 'available')
            sshclient = SshTools.check_connection_paramiko(
                inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH], username=osc_sdk.config.region.get_info(constants.CENTOS_USER)
            )
            osc_sdk.fcu.AttachVolume(InstanceId=inst_info[INSTANCE_ID_LIST][0], VolumeId=vol_id, Device='/dev/xvdc')
            wait_volumes_state(osc_sdk, [vol_id], state='in-use')
            sshclient = SshTools.check_connection_paramiko(
                inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH], username=osc_sdk.config.region.get_info(constants.CENTOS_USER)
            )
            if snap_cfg[3]:
                cmd = 'sudo yum install -y epel-release'
                SshTools.exec_command_paramiko(sshclient, cmd)
                cmd = 'sudo yum install -y fio'
                SshTools.exec_command_paramiko(sshclient, cmd)
            cmd = 'sudo mkfs.xfs -f /dev/xvdc'
            SshTools.exec_command_paramiko(sshclient, cmd, eof_time_out=120)

            osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
            try:
                wait_volumes_state(osc_sdk, [vol_id], 'available')
            except AssertionError:
                logger.debug('Retry detach...')
                osc_sdk.fcu.DetachVolume(VolumeId=vol_id)
                wait_volumes_state(osc_sdk, [vol_id], 'available')

            for i in range(snap_cfg[0]):
                snap_name = 'snap_S{}_from_vol_{}G_with_write_{}M'.format(i, snap_cfg[1], snap_cfg[2])
                write_and_snap(
                    osc_sdk=osc_sdk,
                    sshclient=sshclient,
                    inst_id=inst_info[INSTANCE_ID_LIST][0],
                    vol_id=vol_id,
                    f_num=i,
                    w_size=snap_cfg[2],
                    fio=snap_cfg[3],
                    snap_name=snap_name,
                    snap_attached=bool((i % 2) == 0),
                )
            # delete_vol
            delete_volumes(osc_sdk, [vol_id])
            vol_id = None
    finally:
        if vol_id:
            delete_volumes(osc_sdk, [vol_id])
        if inst_info:
            delete_instances(osc_sdk, inst_info)


if __name__ == '__main__':
    logger = logging.getLogger('stream_setup')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter('[%(asctime)s] ' + '[%(levelname)8s]' + '[%(module)s.%(funcName)s():%(lineno)d]: ' + '%(message)s', '%m/%d/%Y %H:%M:%S')
    )

    logger.setLevel(level=logging.DEBUG)
    logger.addHandler(log_handler)
    logger.propagate = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    args_p = argparse.ArgumentParser(description="Setup ressources for streaming tests", formatter_class=argparse.RawTextHelpFormatter)

    args_p.add_argument('-r', '--region-az', dest='az', action='store', required=True, type=str, help='Selected Outscale region')
    args_p.add_argument('-a', '--account', dest='account', action='store', required=True, type=str, help='Set account used')
    args_p.add_argument('-c', '--clean', dest='clean', action='store_true', help='Clean Account ressources')

    args = args_p.parse_args()

    sdk = OscSdk(config=OscConfig.get(az_name=args.az, account_name=args.account))

    if args.clean:
        logger.info("Clean all remaining resources")
        cleanup_all(sdk)
        logger.info("Stop cleanup")

    setup_streaming_ressources(sdk)
