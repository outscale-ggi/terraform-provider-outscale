from multiprocessing import Queue, Process

import argparse
import logging


import ssl
from qa_test_tools.config import config_constants as constants
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_sdk_pub.osc_api import disable_throttling
import time
from random import randint
from qa_test_tools.misc import id_generator
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_security_groups

ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def create_SG_rule(osc_sdk, queue, group_id, num_sg_rules_per_process):
    result = {'status': 'OK'}
    disable_throttling()
    start = time.time()
    ports = set([])
    for _ in range(num_sg_rules_per_process):
        try:
            port = randint(1000,65000)
            osc_sdk.fcu.AuthorizeSecurityGroupIngress(GroupId=group_id, IpProtocol='tcp', FromPort=port, ToPort=port)
            ports.add(port)
        except:
            pass

    end = time.time()
    result['ports'] = len(ports)
    result['duration'] = end - start
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
                        required=False, type=int, default=50, help='number of processes, default 50')
    args_p.add_argument('-nr', '--num_rules', dest='num_sg_rules_per_process', action='store',
                        required=False, type=int, default=100, help='number of read calls per process, default 20')
    args = args_p.parse_args()

    logger.info("Initialize environment")
    config = OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE)
    oscsdk = OscSdk(config=config)
    ret = oscsdk.icu.ReadQuotas()
    sg_rule_limit = ret.response.ReferenceQuota[1].Quotas[0].MaxQuotaValue
    oscsdk.intel.user.update(username=config.account.account_id, 
                      fields={'sg_rule_limit': args.process_number * args.num_sg_rules_per_process + 3})
    group_id = oscsdk.fcu.CreateSecurityGroup(GroupName=id_generator(prefix="test_SGload_"), GroupDescription='Description').response.groupId
    try:

        NB_OK = 0
        NB_KO = 0

        QUEUE = Queue()
        processes = []
        i = 0
        logger.info("Start workers")
        for i in range(args.process_number):
            p = Process(name="load-{}".format(i), target=create_SG_rule, args=[oscsdk, QUEUE, group_id, args.num_sg_rules_per_process])
            processes.append(p)

        start = time.time()
        for i in range(len(processes)):
            processes[i].start()

        logger.info("Wait workers")
        for i in range(len(processes)):
            processes[i].join()
        end = time.time()

        durations = []

        logger.info("Get results")
        while not QUEUE.empty():
            res = QUEUE.get()
            for key in res.keys():
                if key == "status":
                    if res[key] == "OK":
                        NB_OK += 1
                    else:
                        NB_KO += 1
                elif key == 'duration':
                    durations.append(res[key])
            logger.debug(res)
        logger.info("OK = {} - KO = {}".format(NB_OK, NB_KO))
        logger.info("durations = {}".format(durations))
        print('duration = {}'.format(end - start))

    finally:
        pass
    oscsdk.intel.user.update(username=config.account.account_id, fields={'sg_rule_limit': sg_rule_limit})
    cleanup_security_groups(oscsdk, security_group_id_list=[group_id])
