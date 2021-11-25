import base64
import time
from datetime import datetime

import socket
import paramiko
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException

from qa_test_tools.config import config_constants
from qa_tina_tools.tina import info_keys, oapi, wait
from qa_tina_tests.USER.PERF.perf_common import log_error

def perf_inst_vpc(oscsdk, logger, queue, args):
    print(args)
    omi = None
    inst_type = None
    kp_info = None
    net_info = None
    sg_info = None
    ip_info = None
    vm_info = None
    ip_link_info = None
    max_wait_time = 300
    result = {'status': 'OK'}

    try:
        if not args.omi:
            logger.debug("OMI not specified, select default OMI")
            omi = oscsdk.config.region.get_info(config_constants.CENTOS_LATEST)
        else:
            omi = args.omi
        if not args.inst_type:
            logger.debug("Instance type not specified, select default instance type")
            inst_type = oscsdk.config.region.get_info(config_constants.DEFAULT_INSTANCE_TYPE)
        else:
            inst_type = args.inst_type
        kp_info = oapi.create_Keypair(oscsdk)
        net_info = oapi.create_Net(oscsdk, nb_vm=0)
        sg_info = oapi.create_SecurityGroup(oscsdk, net_id=net_info[info_keys.NET_ID])
        ip_info = oscsdk.oapi.CreatePublicIp().response
        #logger.debug(ip_info.display())
        wait.wait_PublicIps_state(oscsdk, [ip_info.PublicIp.PublicIp], state='available')

        logger.debug("Run instances")
        start_run_inst_time = datetime.now()
        vm_info = oscsdk.oapi.CreateVms(ImageId=omi, MaxVmsCount=1, MinVmsCount=1, VmType=inst_type, KeypairName=kp_info[info_keys.NAME],
                                        SecurityGroupIds=[sg_info], SubnetId=net_info[info_keys.SUBNETS][0][info_keys.SUBNET_ID]).response.Vms[0]
        run_inst_time = (datetime.now() - start_run_inst_time).total_seconds()
        result['inst_vpc_create'] = run_inst_time
        #logger.debug(vm_info.display())
        ip_link_info = oscsdk.oapi.LinkPublicIp(PublicIpId=ip_info.PublicIp.PublicIpId, VmId=vm_info.VmId).response
        #logger.debug(ip_link_info.display())

        logger.debug("Wait instance initialization")
        wait.wait_Vms_state(oscsdk, [vm_info.VmId], state='running')
        running_inst_time = (datetime.now() - start_run_inst_time).total_seconds()
        result['inst_vpc_running'] = running_inst_time

        logger.debug("wait prompt")
        #    client = None
        #    if opsys != 'windows':
        private_key = paramiko.RSAKey.from_private_key_file(kp_info[info_keys.PATH])
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        inst_ssh_time = None
        prompt_inst_time = None
        #    start_ssh = datetime.now()
        #    ret = oscsdk.fcu.DescribeInstances(InstanceId=[inst_list[0].instanceId])
        #    inst = ret.response.reservationSet[0].instancesSet[0]
        while (not inst_ssh_time or not prompt_inst_time) and (datetime.now() - start_run_inst_time).total_seconds() < max_wait_time:
            if not inst_ssh_time:
                try:
                    client.connect(ip_info.PublicIp.PublicIp, 22, pkey=private_key,
                                   username=oscsdk.config.region.get_info(config_constants.CENTOS_USER))
                    inst_ssh_time = (datetime.now() - start_run_inst_time).total_seconds()
                    result['inst_vpc_ssh'] = inst_ssh_time
                except (BadHostKeyException, AuthenticationException, paramiko.SSHException, socket.error):
                    pass
                    #print('Could not connect')
            if not prompt_inst_time:
                resp = oscsdk.oapi.ReadConsoleOutput(VmId=vm_info.VmId).response
                output = resp.ConsoleOutput
                if output:
                    output = base64.b64decode(output).decode("utf-8")
                if output and 'login' in output:
                    prompt_inst_time = (datetime.now() - start_run_inst_time).total_seconds()
                    result['inst_vpc_ready'] = prompt_inst_time
            time.sleep(0.75)

    except Exception as error:
        log_error(logger, error, "Unexpected error while terminating instances", result)
    finally:
        if ip_link_info:
            oscsdk.oapi.UnlinkPublicIp(LinkPublicIpId=ip_link_info.LinkPublicIpId)
        if vm_info:
            oscsdk.oapi.DeleteVms(VmIds=[vm_info.VmId])
            wait.wait_Vms_state(oscsdk, [vm_info.VmId], state='terminated')
        if ip_info:
            oscsdk.oapi.DeletePublicIp(PublicIpId=ip_info.PublicIp.PublicIpId)
            wait.wait_PublicIps_state(oscsdk, [ip_info.PublicIp.PublicIp], cleanup=True)
        if sg_info:
            oapi.delete_SecurityGroup(oscsdk, sg_info)
            time.sleep(15)  # erase when TINA-6014 is solved 2.5.22
        if net_info:
            oapi.delete_Net(oscsdk, net_info)
        if kp_info:
            oapi.delete_Keypair(oscsdk, kp_info)
    queue.put(result.copy())
