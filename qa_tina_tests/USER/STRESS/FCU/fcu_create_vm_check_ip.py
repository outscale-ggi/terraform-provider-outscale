# pylint: disable=exception-escape

import argparse
import logging
from multiprocessing import Queue, Process
import multiprocessing
import ssl
import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_test_tools.error import error_type, load_errors
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import id_generator
from qa_tina_tools.tools.tina.delete_tools import terminate_instances


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
#ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG
DEFAULT_VALUE = -1
DEFAULT_TYPE = 't2.nano'


def make_read_file(osc_sdk, index, num_call):
    values = list(shared_vm_ips)
    print('{}-{} --- values({}) = {}'.format(index, num_call, len(values), values))
    print('{}-{} --- empty({})'.format(index, num_call, values.count(DEFAULT_VALUE)))
    try:
        ret = osc_sdk.oapi.ReadVms().response.Vms
        states = [vm.State for vm in ret if hasattr(vm, 'State')]
        ips = [vm.PublicIp for vm in ret if hasattr(vm, 'PublicIp')]
        dups = [ip for ip in ips if ips.count(ip) > 1]
        print('{}-{} --- vms = {}'.format(index, num_call, len(ret)))
        print('{}-{} --- running = {}'.format(index, num_call, states.count('running')))
        print('{}-{} --- pending = {}'.format(index, num_call, states.count('pending')))
        print('{}-{} --- stopped = {}'.format(index, num_call, states.count('stopped')))
        print('{}-{} --- shutting-down = {}'.format(index, num_call, states.count('shutting-down')))
        print('{}-{} --- terminated = {}'.format(index, num_call, states.count('terminated')))
        print('{}-{} --- ips({}) = {}'.format(index, num_call, len(ips), ips))
        print('{}-{} --- dups({}) = {}'.format(index, num_call, len(dups), dups))
        filename = '/tmp/test_create_vms_{}.txt'.format(id_generator())
        print('{}-{} --- writing to file {}'.format(index, num_call, filename))
        with open(filename, 'w') as file:
            file.write('ips = {}\n'.format(ips))
            file.write('dups = {}\n'.format(dups))
            file.write('describe = {}'.format(ret.display()))
    except:
        print('error occurred in make_read_file')


def wait_vm_ip_address(osc_sdk, vm_id, max_wait=60, sleep_duration=2):
    start = time.time()
    while time.time() - start < max_wait:
        ret = osc_sdk.oapi.ReadVms(Filters={'VmIds': [vm_id]}).response.Vms[0]
        if ret.State in ['stopped', 'terminated']:
            break
        if hasattr(ret, 'PublicIp') and ret.State not in ['pending', 'shutting-down']:
            ip_parts = ret.PublicIp.split('.')
            return (int(ip_parts[2]) << 8) + int(ip_parts[3])
        time.sleep(sleep_duration)
    raise OscTestException('Could not find vm public ip.')


def create_vm(osc_sdk, queue, args, index):
    result = {'status': 'OK', 'duplicate': False}
    start = time.time()
    errs = load_errors()
    vm_ids = []
    num_created = 0
    for num_call in range(args.num_call_per_process):
        try:
            vm_id = None
            vm_id = osc_sdk.oapi.CreateVms(ImageId=osc_sdk.config.region.get_info(constants.CENTOS7), VmType='t2.nano',
                                           exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.Vms[0].VmId
            num_created += 1
            try:
                encoded_ip = wait_vm_ip_address(osc_sdk, vm_id)
            except Exception as error:
                vm_id = None
                errs.handle_api_exception(error, error_type.Create)
                terminate_instances(osc_sdk, [vm_id], wait=False)
            if vm_id:
                vm_ids.append(vm_id)
                if encoded_ip in shared_vm_ips:
                    print('{}-{} --- found used ip --> {}'.format(index, num_call, encoded_ip))
                    make_read_file(osc_sdk, index, num_call)
                shared_vm_ips[index * args.num_call_per_process + len(vm_ids) - 1] = encoded_ip
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'InsufficientCapacity':
                if not vm_ids:
                    break
                try:
                    max_index = len(vm_ids) // 2
                    for smi in range(max_index):
                        tmp = shared_vm_ips[index * args.num_call_per_process + smi + max_index]
                        shared_vm_ips[index * args.num_call_per_process + smi + max_index] = -1
                        shared_vm_ips[index * args.num_call_per_process + smi] = tmp
                    print("process {} terminating {} instances".format(index, max_index))
                    terminate_instances(osc_sdk, vm_ids[0:max_index])
                    vm_ids = vm_ids[max_index:]
                except Exception as error:
                    errs.add_unexpected_error(error)
                    break
            errs.handle_api_exception(error, error_type.Create)
        except Exception as error:
            errs.add_unexpected_error(error)

    print("process {} cleaning {} instances".format(index, len(vm_ids)))
    if vm_ids:
        for smi in range(len(vm_ids)):
            shared_vm_ips[index * args.num_call_per_process + smi] = -1
        try:
            terminate_instances(osc_sdk, vm_ids)
        except Exception as error:
            errs.add_unexpected_error(error)

    end = time.time()
    result['duration'] = end - start
    result['created'] = num_created
    result['error'] = errs.get_dict()
    queue.put(result)


def run(args):
    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))

    nb_ok = 0
    nb_ko = 0

    queue = Queue()
    for smi in range(args.process_number * args.num_call_per_process):
        shared_vm_ips[smi] = DEFAULT_VALUE

    processes = []
    i = 0
    logger.info("Start workers")
    for i in range(args.process_number):
        proc = Process(name="load-{}".format(i), target=create_vm, args=[oscsdk, queue, args, i])
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
    created = 0

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
                created += res[key]
        logger.debug(res)
    logger.info("OK = %d - KO = %d", nb_ok, nb_ko)
    logger.info("durations = %s", durations)
    logger.info("created = %d", created)
    print('duration = {}'.format(end - start))
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
                        required=False, type=int, default=10, help='number of processes, default 10')
    args_p.add_argument('-nc', '--num_call', dest='num_call_per_process', action='store',
                        required=False, type=int, default=40, help='number of read calls per process, default 500')
    main_args = args_p.parse_args()

    shared_vm_ips = multiprocessing.Array('i', main_args.process_number * main_args.num_call_per_process)

    run(main_args)
