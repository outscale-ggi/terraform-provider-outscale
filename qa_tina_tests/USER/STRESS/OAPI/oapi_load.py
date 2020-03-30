from multiprocessing import Queue, Process
import argparse
import logging
import ssl
from qa_test_tools.config import config_constants as constants
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub.osc_api import disable_throttling
import time
from qa_common_tools.error import error_type, load_errors

ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def test_Create_Read_Delete(osc_sdk, queue, args):
    result = {'status': 'OK'}
    disable_throttling()
    start = time.time()
    call_number = 0
    errs = load_errors()
    for _ in range(args.num_read_per_process):
        net_id = None
        try:
            call_number += 1
            ret = osc_sdk.oapi.CreateInternetService(max_retry=0, DryRun=args.dry_run)
            if args.dry_run:
                net_id = 'igw-12345678'
            else:
                net_id = ret.response.InternetService.InternetServiceId
        except OscApiException as error:
            errs.handle_api_exception(error, error_type.Create)
        except Exception as error:
            errs.add_unexpected_error(error)
        if net_id:
            try:
                call_number += 1
                ret = osc_sdk.oapi.ReadInternetServices(Filters={'InternetServiceIds': [net_id]}, max_retry=0, DryRun=args.dry_run)
                if not args.dry_run:
                    ret = ret.response.InternetServices
                if not ret:
                    net_id = None
            except OscApiException as error:
                errs.handle_api_exception(error, error_type.Read)
            except Exception as error:
                errs.add_unexpected_error(error)
        if net_id:
            try:
                call_number += 1
                osc_sdk.oapi.DeleteInternetService(InternetServiceId=net_id, max_retry=0, DryRun=args.dry_run)
                net_id = None
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
                        required=False, type=int, default=80, help='number of processes, default 10')
    args_p.add_argument('-nr', '--num_read', dest='num_read_per_process', action='store',
                        required=False, type=int, default=200, help='number of read calls per process, default 500')
    args_p.add_argument('-dr', '--dry_run', dest='dry_run', action='store',
                        required=False, type=bool, default=False, help='uses the dry run mode if set')
    args = args_p.parse_args()

    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))
    try:

        NB_OK = 0
        NB_KO = 0

        QUEUE = Queue()
        processes = []
        i = 0
        logger.info("Start workers")
        for i in range(args.process_number):
            p = Process(name="load-{}".format(i), target=test_Create_Read_Delete, args=[oscsdk, QUEUE, args])
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
