
from multiprocessing import Queue, Process

import argparse
import logging


import ssl
from qa_common_tools import constants
from qa_common_tools.osc_sdk import OscSdk
from qa_common_tools.config import OscConfig
from osc_common.exceptions.osc_exceptions import OscApiException
import time
from qa_common_tools.error import error_type, load_errors
from qa_tina_tools.tools.tina.delete_tools import terminate_instances
from qa_common_tools.misc import id_generator
import datetime

ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG
DEFAULT_VALUE = -1
DEFAULT_TYPE = 't2.nano'


def test_Create_Vm(osc_sdk, queue, args):
    result = {'status': 'OK', 'duplicate': False}
    start = time.time()
    errs = load_errors()
    vm_ids = []
    for _ in range(args.num_call_per_process):
        try:
            vm_id = None
            vm_id = osc_sdk.oapi.CreateVms(ImageId=osc_sdk.config.region.get_info(constants.CENTOS7), VmType='t2.nano', max_retry=0).response.Vms[0].VmId
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
    args = args_p.parse_args()

    logger.info("Initialize environment")
    oscsdk = OscSdk(config=OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE))
    created = []
    try:

        NB_OK = 0
        NB_KO = 0

        QUEUE = Queue()

        processes = []
        i = 0
        logger.info("Start workers")
        for i in range(args.process_number):
            p = Process(name="load-{}".format(i), target=test_Create_Vm, args=[oscsdk, QUEUE, args])
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
                elif key == 'created':
                    created.extend(res[key])
            logger.debug(res)
        logger.info("OK = {} - KO = {}".format(NB_OK, NB_KO))
        logger.info("durations = {}".format(durations))
        logger.info("created = {}".format(len(created)))
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
            vm_ids = [vm.VmId for vm in ret]
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
                filename = '/tmp/test_create_vms_{}.txt'.format(id_generator())
                print('writing to file {}'.format(filename))
                with open(filename, 'w') as f:
                    f.write('ips = {}\n'.format(ips))
                    f.write('dups = {}\n'.format(dups))
                    f.write('describe = {}'.format(ret.display()))
            # terminate_instances(oscsdk, vm_ids)
        except:
            pass
