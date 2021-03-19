
import argparse
import datetime
import logging
from multiprocessing import Queue, Process
import ssl
import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_test_tools.error import error_type, load_errors
from qa_test_tools.misc import id_generator


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
# ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG
DEFAULT_VALUE = -1
DEFAULT_TYPE = 't2.nano'


def create_vm(osc_sdk, queue, args):
    result = {'status': 'OK', 'duplicate': False}
    start = time.time()
    errs = load_errors()
    vm_ids = []
    for _ in range(args.num_call_per_process):
        try:
            vm_id = None
            vm_id = osc_sdk.oapi.CreateVms(ImageId=osc_sdk.config.region.get_info(constants.CENTOS7),
                                           VmType='t2.nano', max_retry=0).response.Vms[0].VmId
            vm_ids.append(vm_id)
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == '10001':
                break
            errs.handle_api_exception(error, error_type.Create)
        except Exception as error:
            errs.add_unexpected_error(error)

    end = time.time()
    result['duration'] = end - start
    result['created'] = vm_ids
    result['error'] = errs.get_dict()
    queue.put(result)

def run(args):
    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))
    created = []
    try:

        nb_ok = 0
        nb_ko = 0

        queue = Queue()

        processes = []
        i = 0
        logger.info("Start workers")
        for i in range(args.process_number):
            proc = Process(name="load-{}".format(i), target=create_vm, args=[oscsdk, queue, args])
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
                elif key == 'created':
                    created.extend(res[key])
            logger.debug(res)
        logger.info("OK = %d - KO = %d", nb_ok, nb_ko)
        logger.info("durations = %s", durations)
        logger.info("created = %d", len(created))
        print('duration = {}'.format(end - start))
        errors.print_errors()

        start = datetime.datetime.now()
        while datetime.datetime.now() - start < datetime.timedelta(seconds=60):
            ret = oscsdk.oapi.ReadVms().response.Vms
            states = [vm.State for vm in ret if hasattr(vm, 'State')]
            if not states.count('pending') and not states.count('shutting-down'):
                break
            time.sleep(3)

    finally:
        try:
            ret = oscsdk.oapi.ReadVms().response.Vms
            # vm_ids = [vm.VmId for vm in ret]
            states = [vm.State for vm in ret if hasattr(vm, 'State')]
            ips = [vm.PublicIp for vm in ret if hasattr(vm, 'PublicIp')]
            dups = [ip for ip in ips if ips.count(ip) > 1]
            print('vms = {}'.format(len(ret)))
            print('running = {}'.format(states.count('running')))
            print('pending = {}'.format(states.count('pending')))
            print('stopped = {}'.format(states.count('stopped')))
            print('shutting-down = {}'.format(states.count('shutting-down')))
            print('terminated = {}'.format(states.count('terminated')))
            print('ips({}) = {}'.format(len(ips), ips))
            print('dups({}) = {}'.format(len(dups), dups))
            if dups:
                filename = 'test_create_vms_{}.txt'.format(id_generator())
                print('writing to file {}'.format(filename))
                with open(filename, 'w') as file:
                    file.write('ips = {}\n'.format(ips))
                    file.write('dups = {}\n'.format(dups))
                    file.write('describe = {}'.format(ret.display()))
            # terminate_instances(oscsdk, vm_ids)
        except Exception as error:
            print(error)


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
    args_p.add_argument('-nc', '--num_call', dest='num_call_per_process', action='store',
                        required=False, type=int, default=40, help='number of read calls per process, default 500')
    main_args = args_p.parse_args()

    run(main_args)
