import argparse
import logging
import ssl
import uuid
from multiprocessing import Queue, Process

from qa_sdk_pub.osc_api import disable_throttling
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tools.tina.delete_tools import terminate_instances

ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG
DEFAULT_VALUE = -1
DEFAULT_TYPE = 't2.nano'


def test_Create_Vm(osc_sdk, queue, token):
    result = {}
    disable_throttling()
    ret = osc_sdk.fcu.RunInstances(ImageId=osc_sdk.config.region.get_info(constants.CENTOS7),
                                   InstanceType='t2.nano', MaxCount=1, MinCount=1,
                                   ClientToken=token)

    result['inst_ids'] = ret.response.instancesSet[0].instanceId
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
    args_p.add_argument('-np', '--proc_num', dest='process_number', action='store',
                        required=False, type=int, default=10, help='number of processes, default 10')
    args_p.add_argument('-nc', '--num_case', dest='num_case', action='store',
                        required=False, type=int, default=4, help='number of read calls per process, default 500')
    args_p.add_argument('-st', '--same_token', dest='same_token', action='store',
                        required=False, type=bool, default=False, help='Set the bool')
    args = args_p.parse_args()

    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))
    created = []
    try:
        inst_ids = set()
        i = 0
        logger.info("Start workers")

        processes = []
        queue = Queue()
        token = str(uuid.uuid4())
        for i in range(args.process_number):
            if args.same_token:
                token = token
            else:
                token = str(uuid.uuid4())
            p = Process(name="load-{}".format(i), target=test_Create_Vm, args=[oscsdk, queue, token])
            processes.append(p)
        print("kaka")
        for i in range(len(processes)):
            processes[i].start()

        logger.info("Wait workers")
        for i in range(len(processes)):
            processes[i].join()

        while not queue.empty():
            res = queue.get()
            inst_ids.add(res["inst_ids"])
        if args.same_token:
            assert len(inst_ids) == 1
        else:
            assert len(inst_ids) == args.process_number - 1

    finally:
        for inst_id in inst_ids:
            terminate_instances(oscsdk, [inst_id])
