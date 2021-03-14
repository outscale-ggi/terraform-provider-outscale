
import argparse
import logging
from multiprocessing import Queue, Process
import ssl
import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub.osc_api import disable_throttling
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_test_tools.error import error_type, load_errors


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
# ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def test_health_check(osc_sdk, queue, args):
    result = {'status': 'OK'}
    disable_throttling()
    start = time.time()
    call_number = 0
    errs = load_errors()
    for _ in range(args.num_calls_per_process):
        try:
            call_number += 1
            osc_sdk.identauth.IdauthAccount.healthCheck(verb='GET')
        except OscApiException as error:
            errs.handle_api_exception(error, error_type.Create)
        except Exception as error:
            errs.add_unexpected_error(error)

    end = time.time()
    result['num'] = call_number
    result['duration'] = end - start
    result['error'] = errs.get_dict()
    queue.put(result)


def run(args):

    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))

    nb_ok = 0
    nb_ko = 0

    queue = Queue()
    processes = []
    i = 0
    logger.info("Start workers")
    for i in range(args.process_number):
        proc = Process(name="load-{}".format(i), target=test_health_check, args=[oscsdk, queue, args])
        processes.append(proc)

    start = time.time()
    for proc in processes:
        proc.start()

    logger.info("Wait workers")
    for proc in processes:
        proc.join()
    end = time.time()

    durations = []
    errors = load_errors()
    nums = []

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
            elif key == 'error':
                errors.add(res[key])
            elif key == 'num':
                nums.append(res[key])
        logger.debug(res)
    logger.info("OK = %d - KO = %d", nb_ok, nb_ko)
    logger.info("durations = %s", durations)
    logger.info("nums = %d", nums)
    print('duration = {}'.format(end - start))
    print('calls number = {}'.format(sum(nums)))
    errors.print_errors()


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
                        required=False, type=int, default=50, help='number of processes, default 10')
    args_p.add_argument('-nc', '--num_read', dest='num_calls_per_process', action='store',
                        required=False, type=int, default=600, help='number of read calls per process, default 500')
    main_args = args_p.parse_args()

    run(main_args)
