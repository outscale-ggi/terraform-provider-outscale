import argparse
from datetime import datetime
import logging
from multiprocessing import Queue, Process
import ssl

from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, SUBNETS, SUBNET_ID
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
# ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def start_windows(osc_sdk, args, subnet_id, queue):
    result = {'status': 'OK'}
    inst_info = None
    try:
        start = datetime.now()
        inst_info = create_instances(osc_sdk, omi_id=args.omi, state=None, subnet_id=subnet_id)
        try:
            wait_instances_state(osc_sdk, inst_info[INSTANCE_ID_LIST], state='ready', threshold=100, wait_time=10)
            result['time'] = (datetime.now() - start).total_seconds()
        except:
            result['status'] = 'KO'
    finally:
        if inst_info:
            try:
                delete_instances(osc_sdk, inst_info)
            except:
                print('Could not delete instances')
    queue.put(result)


def run(args):
    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))

#     if not args.omi:
#         logger.debug("OMI not specified, select default OMI")
#         omi = oscsdk.config.region.get_info(constants.WINDOWS_LATEST)
#     else:
#         omi = args.omi
#
#     if not args.instance_type:
#         logger.debug("Instance type not specified, select default instance type")
#         inst_type = 'm4.large'
#     else:
#         inst_type = args.instance_type

    vpc_info = None
    try:
        vpc_info = create_vpc(oscsdk)

        nb_ok = 0
        nb_ko = 0

        queue = Queue()
        processes = []
        i = 0
        logger.info("Start workers")
        for i in range(args.vm_number):
            # def test_snapshot(conn, keyPath, ipAddress, volId, device, args, queue):
            proc = Process(name="pfsbu-{}".format(i), target=start_windows, args=[oscsdk, args, vpc_info[SUBNETS][0][SUBNET_ID], queue])
            processes.append(proc)
            proc.start()

        logger.info("Wait workers")
        for proc in processes:
            proc.join()

        durations = []

        logger.info("Get results")
        while not queue.empty():
            res = queue.get()
            for key in res.keys():
                if key == "status":
                    if res[key] == "OK":
                        nb_ok += 1
                    else:
                        nb_ko += 1
                elif key == 'time':
                    durations.append(res[key])
            logger.debug(res)
        logger.info("OK = %d - KO = %d", nb_ok, nb_ko)
        logger.info("durations = %s", durations)

    finally:
        if vpc_info:
            try:
                delete_vpc(oscsdk, vpc_info)
            except:
                print('Could not delete vpc')


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
    args_p.add_argument('-n', '--vm_num', dest='vm_number', action='store',
                        required=False, type=int, default=1, help='number of instances, default 20')
    main_args = args_p.parse_args()

    run(main_args)
