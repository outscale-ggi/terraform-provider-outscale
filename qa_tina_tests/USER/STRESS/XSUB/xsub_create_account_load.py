from multiprocessing import Queue, Process
import argparse
import logging
import ssl
from qa_common_tools import constants
from qa_common_tools.config import OscConfig
from osc_common.exceptions.osc_exceptions import OscApiException
from osc_sdk_pub.osc_api import disable_throttling
import time
from qa_common_tools.error import error_type, load_errors
from qa_common_tools import misc
import string
from osc_sdk_priv.osc_api.osc_priv_api import OscPrivApi
from osc_sdk_as.osc_sdk_as import OscSdkAs
from qa_common_tools.osc_sdk import OscSdk

ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def create_account(config, queue, args):
    result = {'status': 'OK'}
    disable_throttling()
    start = time.time()
    call_number = 0
    errs = load_errors()
    xsub = OscPrivApi(service='xsub', config=config)
    intel = OscPrivApi(service='intel', config=config)
    osc_sdk_as = OscSdkAs(config.region.get_info(constants.AS_IDAUTH_ID), config.region.name)

    for _ in range(args.num_create_per_process):
        pid = None
        try:
            call_number += 1
            email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='test_xsub_create_account_').lower())
            password = misc.id_generator(size=8, chars=string.digits)
            account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                            'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                            'password': password, 'zipcode': '92210'}
            pid = create_account(OscSdk(config=config), account_info=account_info)
        except OscApiException as error:
            errs.handle_api_exception(error, error_type.Create)
        except Exception as error:
            errs.add_unexpected_error(error)
        if pid:
            try:
                call_number += 1
                xsub.terminate_account(pid=pid)
                intel.user.delete(username=pid)
                intel.user.gc(username=pid)
                osc_sdk_as.identauth.IdauthAccountAdmin.deleteAccount(principal={"accountPid": pid}, forceRemoval="true")
            except OscApiException as error:
                errs.handle_api_exception(error, error_type.Delete)
            except Exception as error:
                errs.add_unexpected_error(error)

    end = time.time()
    result['num'] = call_number
    result['duration'] = end - start
    result['error'] = errs.get_dict()
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
                        required=False, type=int, default=40, help='number of processes, default 10')
    args_p.add_argument('-nc', '--num_create', dest='num_create_per_process', action='store',
                        required=False, type=int, default=100, help='number of read calls per process, default 500')
    args = args_p.parse_args()

    logger.info("Initialize environment")
    config = OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE)
    try:

        NB_OK = 0
        NB_KO = 0

        QUEUE = Queue()
        processes = []
        i = 0
        logger.info("Start workers")
        for i in range(args.process_number):
            p = Process(name="load-{}".format(i), target=create_account, args=[config, QUEUE, args])
            processes.append(p)

        start = time.time()
        for i in range(len(processes)):
            processes[i].start()

        logger.info("Wait workers")
        for i in range(len(processes)):
            processes[i].join()
        end = time.time()

        durations = []
        errors = load_errors()
        nums = []

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
                elif key == 'error':
                    errors.add(res[key])
                elif key == 'num':
                    nums.append(res[key])
            logger.debug(res)
        logger.info("OK = {} - KO = {}".format(NB_OK, NB_KO))
        logger.info("durations = {}".format(durations))
        logger.info("nums = {}".format(nums))
        print('duration = {}'.format(end - start))
        print('calls number = {}'.format(sum(nums)))
        errors.print_errors()

    finally:
        pass
