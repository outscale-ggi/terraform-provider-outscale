import string
from multiprocessing import Queue, Process
import argparse
import logging
import ssl
from osc_sdk_as import OscSdkAs
from osc_sdk_priv import OscPrivApi
from qa_common_tools.config import config_constants as constants
from qa_common_tools.osc_sdk import OscSdk
from qa_common_tools.config import OscConfig
from osc_common.exceptions.osc_exceptions import OscApiException
from osc_sdk_pub.osc_api import disable_throttling
import time
from qa_common_tools import misc
from qa_common_tools.error import error_type, load_errors
from qa_tina_tools.specs.oapi import OAPI_SPEC, COMPONENTS, SCHEMAS
from qa_common_tools.account_tools import create_account


ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def read_function_loop(osc_sdk, queue, args, api_read, throtting_account=False):
    result = {'status': 'OK'}
    disable_throttling()
    start = time.time()
    success_time = []
    call_number = 0
    nb_throttling_error = 0
    errs = load_errors()
    for i in range(args.num_read_per_process):
        if not throtting_account:
            read_request = api_read[0]
        else:
            read_request = api_read[i % len(api_read)]
        try:
            call_number += 1
            getattr(osc_sdk.oapi, read_request)(max_retry=0)
        except OscApiException as error:
            if error.status_code == 503:
                nb_throttling_error += 1
            else:
                errs.handle_api_exception(error, error_type.Create)

        except Exception as error:
            errs.add_unexpected_error(error)

    end = time.time()
    result['num'] = call_number
    result['duration'] = end - start
    result['error'] = errs.get_dict()
    result['nb_throttling_error'] = nb_throttling_error
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
                        required=False, type=str, help='Set account used for the test')
    args_p.add_argument('-cr', '--create_account', dest='create_account', action='store',
                        required=False, type=str, help='Set account used for the test')
    args_p.add_argument('-np', '--proc_num', dest='process_number', action='store',
                        required=False, type=int, default=1, help='number of processes, default 10')
    args_p.add_argument('-nr', '--num_read', dest='num_read_per_process', action='store',
                        required=False, type=int, default=50, help='number of read calls per process, default 500')
    args_p.add_argument('-dr', '--dry_run', dest='dry_run', action='store',
                        required=False, type=bool, default=False, help='uses the dry run mode if set')
    args = args_p.parse_args()

    logger.info("Initialize environment")
    config = OscConfig.get(account_name=args.account, az_name=args.az,
                           credentials=constants.CREDENTIALS_CONFIG_FILE)
    xsub = OscPrivApi(service='xsub', config=config)
    intel = OscPrivApi(service='intel', config=config)
    osc_sdk_as = OscSdkAs(config.region.get_info(constants.AS_IDAUTH_ID), config.region.name)
    account_sdk = None

    OAPI_SCHEMAS = OAPI_SPEC[COMPONENTS][SCHEMAS]
    api_read = []
    pids = []
    for i, j in OAPI_SCHEMAS.items():
        if i.startswith('Read') and 'required' not in j and i.endswith('Request') and not i.startswith('ReadApiLogs'):
            api_read.append(i[:-7])
    NB_OK = 0
    NB_KO = 0
    QUEUE = Queue()
    processes = []
    for i in range(args.process_number):
        if args.account:
            if not account_sdk:
                account_sdk = OscSdk(config=config)
            osc_sdk_i = account_sdk
        else:
            email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='test_throttling_read').lower())
            password = misc.id_generator(size=8, chars=string.digits)
            account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                            'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                            'password': password, 'zipcode': '92210'}
            pid = create_account(OscSdk(config=config), account_info=account_info)
            pids.append(pid)
            ret = intel.accesskey.find_by_user(owner=pid)
            keys = ret.response.result[0]
            osc_sdk_i = OscSdk(config=OscConfig.get_with_keys(az_name=args.az, ak=keys.name, sk=keys.secret, account_id=pid,
                                                              login=email, password=password))

        p = Process(name="load-{}".format(i), target=read_function_loop, args=[osc_sdk_i, QUEUE, args, api_read])
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
    nb_throttling = []

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
            elif key == 'nb_throttling_error':
                nb_throttling.append(res[key])
        logger.debug(res)
    logger.info("OK = {} - KO = {}".format(NB_OK, NB_KO))
    logger.info("nb_throttling_error = {}".format(nb_throttling))
    logger.info("durations = {}".format(durations))
    logger.info("nums = {}".format(nums))
    print('duration = {}'.format(end - start))
    print('calls number = {}'.format(sum(nums)))
    print('throttling error number = {}'.format(sum(nb_throttling)))
    errors.print_errors()

    # for user in pids:
    #     try:
    #         xsub.terminate_account(pid=user)
    #     except OscException as error:
    #         logger.error("Error occurred while terminating user {} : {}".format(user, str(error)))
    #     try:
    #         intel.user.delete(username=user)
    #         intel.user.gc(username=user)
    #         osc_sdk_as.identauth.IdauthAccountAdmin.deleteAccount(principal={"accountPid": user}, forceRemoval="true")
    #     except OscException as error:
    #         logger.error("Error occurred while deleting user {} : {}".format(user, str(error)))

