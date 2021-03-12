
import argparse
import logging
from multiprocessing import Queue, Process
from random import randint
import ssl
import time

from qa_sdk_pub.osc_api import disable_throttling
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_security_groups


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
# ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def create_sg_rule(osc_sdk, queue, group_id, num_sg_rules_per_process):
    result = {'status': 'OK'}
    disable_throttling()
    start = time.time()
    ports = set([])
    for _ in range(num_sg_rules_per_process):
        try:
            port = randint(1000, 8000)
            osc_sdk.fcu.AuthorizeSecurityGroupIngress(GroupId=group_id, IpProtocol='tcp', FromPort=port, ToPort=port)
            ports.add(port)
        except Exception:
            print('Could not create rule')

    end = time.time()
    result['ports'] = ports
    result['duration'] = end - start
    queue.put(result)


def run(args):

    logger.info("Initialize environment")
    config = OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE)
    oscsdk = OscSdk(config=config)
    ret = oscsdk.icu.ReadQuotas()
    sg_rule_limit = ret.response.ReferenceQuota[1].Quotas[0].MaxQuotaValue
    oscsdk.intel.user.update(username=config.account.account_id,
                             fields={'sg_rule_limit': args.process_number * args.num_sg_rules_per_process + 3})
    group_id = oscsdk.fcu.CreateSecurityGroup(GroupName=id_generator(prefix="test_SGload_"), GroupDescription='Description').response.groupId

    nb_ok = 0
    nb_ko = 0

    queue = Queue()
    processes = []
    i = 0
    logger.info("Start workers")
    for i in range(args.process_number):
        proc = Process(name="load-{}".format(i), target=create_sg_rule, args=[oscsdk, queue, group_id, args.num_sg_rules_per_process])
        processes.append(proc)

    start = time.time()
    for proc in processes:
        proc.start()

    logger.info("Wait workers")
    for proc in processes:
        proc.join()
    end = time.time()

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
            elif key == 'duration':
                durations.append(res[key])
        logger.debug(res)
    logger.info("OK = %d - KO = %d", nb_ok, nb_ko)
    logger.info("durations = %s", durations)
    print('duration = {}'.format(end - start))

    oscsdk.intel.user.update(username=config.account.account_id, fields={'sg_rule_limit': sg_rule_limit})
    cleanup_security_groups(oscsdk, security_group_id_list=[group_id])


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
    args_p.add_argument('-nr', '--num_rules', dest='num_sg_rules_per_process', action='store',
                        required=False, type=int, default=20, help='number of read calls per process, default 20')
    main_args = args_p.parse_args()

    run(main_args)
