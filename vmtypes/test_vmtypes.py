import argparse
import logging
import ssl
from qa_common_tools import constants
from qa_common_tools.config import OscConfig
from qa_common_tools.osc_sdk import OscSdk
from qa_tina_tools.tools.tina.create_tools import create_instances, create_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, SUBNETS, SUBNET_ID, NONE, INSTANCE_SET, KEY_PAIR, PATH
from pprint import pprint
from qa_tina_tools.tools.tina.delete_tools import stop_instances, delete_instances, delete_vpc
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs, cleanup_instances
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
import datetime
from osc_common.exceptions.osc_exceptions import OscApiException, OscTestException
from qa_common_tools.misc import assert_error
from qa_common_tools.ssh import SshTools
from qa_common_tools.constants import CENTOS_USER
from vmtypes import INST_TYPE_MATRIX
from osc_common.objects.osc_objects import OscObjectDict

ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def check_instance(osc_sdk, type_info, inst_info, key_path, ip_address=None):
    tina_type = INST_TYPE_MATRIX[type_info.name]
    parts = tina_type[0].split('.')
    family = parts[0]
    core = int(parts[1].split('r')[0][1:])
    ram = int(parts[1].split('r')[1].split('p')[0][0:])
    perf = int(parts[1].split('r')[1].split('p')[1][0:])
    gpu_model = None
    gpu_number = 0
    if tina_type[1]:
        gpu_model = tina_type[1][0]
        gpu_number = tina_type[1][1]

    inst_id = inst_info[INSTANCE_ID_LIST][0]
    inst = osc_sdk.intel.instance.find(id=inst_id).response.result[0]

    assert inst.tina_type == tina_type[0], 'Types do not correspond'
    # do some test depending on type (ephemeral/gpu)
    if ip_address is None:
        ip_address = inst_info[INSTANCE_SET][0]['ipAddress']

    sshclient = SshTools.check_connection_paramiko(ip_address, key_path,
                                                   username=osc_sdk.config.region.get_info(CENTOS_USER))

    cmd = 'sudo nproc'
    out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
    assert not status, "SSH command was not executed correctly on the remote host"
    out, _, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
    assert len(set([int(out), core, inst.specs.core])) == 1, "Core values are not all equal, {} {} {}".format(int(out), core, inst.specs.core)

    # TODO: check cpu generation ?

    cmd = "sudo dmidecode -t 16 | grep 'Maximum Capacity' | awk -v OFS=' ' '{print $3, $4}'"
    out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
    assert not status, "SSH command was not executed correctly on the remote host"
    out, _, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
    out = out.strip().split(" ")
    if out[1] == 'MB':
        expected = int(out[0]) / 1024
    else:
        expected = int(out[0])
    assert len(set([expected, ram, int(inst.specs.memory / (1024*1024*1024))])) == 1, "Ram values are not all equal, {} {} {}".format(expected, ram, int(inst.specs.memory / (1024*1024*1024)))

    cmd = "sudo lshw -C display | grep -c '*-display'"
    out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd, expected_status=-1)
    displays = out.split()[-1:][0].strip()
    assert int(displays) - 1 == gpu_number, "Gpu number values are not all equal, {} {}".format(displays - 1, gpu_number)
    if gpu_number > 0:
        assert gpu_number == inst.required_pci.gpu, "Gpu number values are not all equal, {} {}".format(inst.required_pci.gpu, gpu_number)

    if type_info.storage_number > 0:
        for i in range(type_info.storage_number):
            cmd = "sudo fdisk -l /dev/xvd{} | grep /dev/xvd{}".format(chr(98 + i), chr(98 + i))
            out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
            assert not status, "SSH command was not executed correctly on the remote host"
            assert type_info.storage_size * 1024 * 1024 == int(out.strip().split()[4]), "Ephemeral storage size are not equal, {} {}".format(type_info.storage_size * 1024 * 1024, out.strip().split()[4])

    if type_info.max_nics > 1:
            cmd = 'sudo yum install pciutils -y'
            out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd, eof_time_out=300)
            assert not status, "SSH command was not executed correctly on the remote host"
            cmd = 'sudo lspci | grep -c Ethernet '
            out, status, _ = SshTools.exec_command_paramiko_2(sshclient, cmd)
            assert not status, "SSH command was not executed correctly on the remote host"
            assert int(out.strip()) == type_info.max_nics, 'Nic number are not equal, {} {}'.format(int(out.strip()), type_info.max_nics)


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

    args_p = argparse.ArgumentParser(description="Test vm types",
                                     formatter_class=argparse.RawTextHelpFormatter)

    args_p.add_argument('-r', '--region-az', dest='az', action='store',
                        required=True, type=str, help='Selected Outscale region AZ for the test')
    args_p.add_argument('-a', '--account', dest='account', action='store',
                        required=True, type=str, help='Set account used for the test')
    args_p.add_argument('-kn', '--key_name', dest='key_name', action='store',
                        required=True, type=str, help='Private key name')
    args_p.add_argument('-kp', '--key_path', dest='key_path', action='store',
                        required=True, type=str, help='Private key location')
    args = args_p.parse_args()

    config = OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE)
    osc_sdk = OscSdk(config)

    vpc_info = None
    eip = None
    families = {}
    insuficient_capacity = []
    unexpected_errors = {}
    fni_ids = []
    infos = []
    try:
        vpc_info = create_vpc(osc_sdk)
        eip = osc_sdk.fcu.AllocateAddress(Domain='vpc').response
        ret = osc_sdk.intel.instance.get_available_types().response.result
        for attr in ret.__dict__:
            if not type(getattr(ret, attr)) is OscObjectDict:
                continue
            type_info = getattr(ret, attr)
            parts = type_info.name.split('.')
            if not parts[0] in families:
                families[parts[0]] = []
            families[parts[0]].append(type_info)
        for family in families:
            continue
            for type_info in families[family]:
                inst_info = None
                try:
                    if type_info.name not in INST_TYPE_MATRIX:
                        raise OscTestException('Could not find type {} in matrix'.format(type_info.name))
                    infos.append('Create instance with type {}'.format(type_info.name))
                    try:
                        inst_info = create_instances(osc_sdk, inst_type=type_info.name, key_name=args.key_name, state='ready',
                                                     nb_ephemeral=len(type_info.storage), wait_time=5, threshold=24,
                                                     subnet_id=(vpc_info[SUBNETS][0][SUBNET_ID] if type_info.max_nics > 1 else None))
                    except AssertionError as error:
                        if 'stopped' in str(error):
                            raise OscTestException("Could not start instance -> stopped")
                        raise error
                    if type_info.max_nics > 1:
                        osc_sdk.fcu.AssociateAddress(AllocationId=eip.allocationId, InstanceId=inst_info[INSTANCE_ID_LIST][0])
                        for i in range(type_info.max_nics - 1):
                            fni_id = osc_sdk.fcu.CreateNetworkInterface(SubnetId=vpc_info[SUBNETS][0][SUBNET_ID]).response.networkInterface.networkInterfaceId
                            fni_ids.append(fni_id)
                            osc_sdk.fcu.AttachNetworkInterface(DeviceIndex=1+i, InstanceId=inst_info[INSTANCE_ID_LIST][0], NetworkInterfaceId=fni_id)
                    infos.append('Check instance with type {}'.format(type_info.name))
                    check_instance(osc_sdk, type_info, inst_info, args.key_path, ip_address=(eip.publicIp if type_info.max_nics > 2 else None))
                except OscApiException as error:
                    if error.status_code == 500 and error.error_code == 'InsuficientCapacity':
                        insuficient_capacity.append(type_info.name)
                    else:
                        unexpected_errors[type_info.name] = error
                except Exception as error:
                    unexpected_errors[type_info.name] = error
                finally:
                    try:
                        if inst_info:
                            delete_instances(osc_sdk, inst_info)
                        for fni_id in fni_ids:
                            osc_sdk.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)
                    except:
                        pass
    except Exception as error:
        unexpected_errors[None] = error
    finally:
        if eip:
            osc_sdk.fcu.ReleaseAddress(AllocationId=eip.allocationId)
        if vpc_info:
            delete_vpc(osc_sdk, vpc_info)

    print("insufficient capa")
    pprint(insuficient_capacity)
    print("unexpected errors")
    pprint(unexpected_errors)
    print("insufficient infos")
    pprint(infos)
