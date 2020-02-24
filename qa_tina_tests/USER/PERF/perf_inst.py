import base64
from datetime import datetime
import socket
from threading import current_thread
import time

from paramiko import SSHClient
from paramiko import SSHException
import paramiko
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException

from qa_common_tools.config.configuration import Configuration
from qa_common_tools.config import config_constants as constants
from qa_tina_tests.USER.PERF.perf_common import log_error
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tina.info_keys import NAME, PATH
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_keypairs_state, wait_security_groups_state


def perf_inst(oscsdk, logger, queue, args):
    perf_inst_exec(oscsdk, logger, queue, args, '')

def perf_inst_exec(oscsdk, logger, queue, args, os):

    MAX_WAIT_TIME = 180
    if os == 'windows':
        MAX_WAIT_TIME = 1800

    thread_name = current_thread().name
    # element names
    kp_name = 'pinst_kp_{}_{}'.format(args.az[:-1], thread_name)
    sg_name = 'pinst_sg_{}'.format(thread_name)

    time.sleep(int(thread_name.split('-')[-1]) * 60)

    if not args.omi:
        logger.debug("OMI not specified, select default OMI")
        if os == 'windows':
            OMI = oscsdk.config.region.get_info(constants.WINDOWS_2016)
        else:
            OMI = oscsdk.config.region.get_info(constants.CENTOS7)
    else:
        OMI = args.omi

    if not args.inst_type:
        logger.debug("Instance type not specified, select default instance type")
        if os == 'windows':
            INST_TYPE = 'c4.xlarge'
        else:
            INST_TYPE = oscsdk.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
    else:
        INST_TYPE = args.inst_type

    result = {'status': 'OK'}

    # check key pair
    kp_info = None
    if result['status'] != "KO":
        logger.debug("Describe Key Pair")
        try:
            ret = oscsdk.fcu.DescribeKeyPairs(Filter=[{'Name': 'key-name', 'Value': kp_name}])
            if ret.response.keySet:
                kp_info = {}
                kp_info[NAME] = kp_name
                kp_info[PATH] = "/tmp/{}.pem".format(kp_name)
                private_key = paramiko.RSAKey.from_private_key_file(kp_info[PATH])
        except Exception as error:
            log_error(logger, error, "Unexpected error while checking security group", result)

    # check security group
    sg = None
    if result['status'] != "KO":
        logger.debug("Describe Security Group")
        try:
            ret = oscsdk.fcu.DescribeSecurityGroups(Filter=[{'Name': 'group-name', 'Value': sg_name}]).response.securityGroupInfo
            if ret:
                sg = ret[0].groupId
        except Exception as error:
            log_error(logger, error, "Unexpected error while checking security group", result)

    if not kp_info and result['status'] != "KO":
        try:
            kp_info = create_keypair(oscsdk, name=kp_name)
            wait_keypairs_state(oscsdk, [kp_name])
            private_key = paramiko.RSAKey.from_private_key_file(kp_info[PATH])
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating key pair", result)

    if not sg and result['status'] != "KO":
        try:
            sg = oscsdk.fcu.CreateSecurityGroup(GroupName=sg_name,
                                                GroupDescription='Security_Group_For_{}'.format(thread_name)).response.groupId
            wait_security_groups_state(oscsdk, [sg])

            logger.debug("Allow SSH in SG")
            oscsdk.fcu.AuthorizeSecurityGroupIngress(GroupId=sg, FromPort='22', ToPort='22', IpProtocol='tcp',
                                                     CidrIp=Configuration.get('cidr', 'allips'))
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating security group", result)

    inst_list = []
    if result['status'] != "KO":
        logger.debug("Run instances")
        try:
            start_run_inst_time = datetime.now()
            ret = oscsdk.fcu.RunInstances(ImageId=OMI, MinCount=3, MaxCount=3, InstanceType=INST_TYPE,
                                          KeyName=kp_info[NAME], SecurityGroup=[sg])
            run_inst_time = (datetime.now() - start_run_inst_time).total_seconds()
            result['inst_create'] = run_inst_time
            for instance in ret.response.instancesSet:
                inst_list.append(instance)

            logger.debug("Wait instance initialization")
            wait_instances_state(oscsdk, [i.instanceId for i in inst_list], state='running')
            running_inst_time = (datetime.now() - start_run_inst_time).total_seconds()
            result['inst_running'] = running_inst_time

            logger.debug("wait prompt")
            client = None
            if os != 'windows':
                client = SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            inst_ssh_time = None
            prompt_inst_time = None
            start_ssh = datetime.now()
            ret = oscsdk.fcu.DescribeInstances(InstanceId=[inst_list[0].instanceId])
            inst = ret.response.reservationSet[0].instancesSet[0]
            while (not inst_ssh_time or not prompt_inst_time) and (datetime.now() - start_ssh).total_seconds() < MAX_WAIT_TIME:
                if os != 'windows' and not inst_ssh_time:
                    try:
                        client.connect(inst.ipAddress, 22, pkey=private_key, username=oscsdk.config.region.get_info(constants.CENTOS_USER))
                        inst_ssh_time = (datetime.now() - start_run_inst_time).total_seconds()
                        result['inst_ssh'] = inst_ssh_time
                    except (BadHostKeyException, AuthenticationException, SSHException, socket.error):
                        pass
                if not prompt_inst_time:
                    ret = oscsdk.fcu.GetConsoleOutput(InstanceId=inst_list[0].instanceId)
                    output = ret.response.output
                    if output:
                        output = base64.b64decode(output).decode("utf-8")
                    if os == 'windows':
                        if output and '<Password>' in output:
                            prompt_inst_time = (datetime.now() - start_run_inst_time).total_seconds()
                            inst_ssh_time = prompt_inst_time
                            result['inst_ready'] = prompt_inst_time
                    else:
                        if output and 'login' in output:
                            prompt_inst_time = (datetime.now() - start_run_inst_time).total_seconds()
                            result['inst_ready'] = prompt_inst_time
                time.sleep(0.5)
            wait_instances_state(oscsdk, [inst_list[1].instanceId, inst_list[2].instanceId], state='ready', threshold=60, wait_time=10)
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating test instance", result)

    if result['status'] != "KO":
        logger.debug("Stop instance")
        try:
            logger.debug("Stop Instance 1")
            start_inst_stop = datetime.now()
            oscsdk.fcu.StopInstances(InstanceId=[inst_list[0].instanceId])
            inst_stop_call = (datetime.now() - start_inst_stop).total_seconds()
            result['inst_stop_exec'] = inst_stop_call
            wait_instances_state(oscsdk, [inst_list[0].instanceId], state='stopped')
            inst_stop = (datetime.now() - start_inst_stop).total_seconds()
            result['inst_stop'] = inst_stop

            logger.debug("Force stop Instance 2")
            start_inst_stop = datetime.now()
            oscsdk.fcu.StopInstances(InstanceId=[inst_list[1].instanceId], Force=True)
            inst_stop_call = (datetime.now() - start_inst_stop).total_seconds()
            result['inst_stop_force_exec'] = inst_stop_call
            wait_instances_state(oscsdk, [inst_list[1].instanceId], state='stopped')
            inst_stop = (datetime.now() - start_inst_stop).total_seconds()
            result['inst_stop_force'] = inst_stop
        except Exception as error:
            log_error(logger, error, "Unexpected error while stopping instance", result)

    if result['status'] != "KO":
        try:
            logger.debug("Terminate instance Stop")
            start_inst_term = datetime.now()
            inst = inst_list[0]
            oscsdk.fcu.TerminateInstances(InstanceId=[inst.instanceId])
            inst_list.remove(inst)
            inst_term = (datetime.now() - start_inst_term).total_seconds()
            result['inst_stop_terminate_exec'] = inst_term
            wait_instances_state(oscsdk, [inst.instanceId], state='terminated')
            time_inst_stop = (datetime.now() - start_inst_term).total_seconds()
            result['inst_stop_terminated'] = time_inst_stop

            inst = inst_list[0]
            oscsdk.fcu.TerminateInstances(InstanceId=[inst.instanceId])
            inst_list.remove(inst)
            wait_instances_state(oscsdk, [inst.instanceId], state='terminated')

            logger.debug("Terminate instance Ready")
            start_inst_term = datetime.now()
            inst = inst_list[0]
            oscsdk.fcu.TerminateInstances(InstanceId=[inst.instanceId])
            inst_list.remove(inst)
            inst_term = (datetime.now() - start_inst_term).total_seconds()
            result['inst_ready_terminate_exec'] = inst_term
            wait_instances_state(oscsdk, [inst.instanceId], state='terminated')
            time_inst_stop = (datetime.now() - start_inst_term).total_seconds()
            result['inst_ready_terminated'] = time_inst_stop
        except Exception as error:
            log_error(logger, error, "Unexpected error while terminating instance", result)

    if inst_list:
        try:
            oscsdk.fcu.TerminateInstances(InstanceId=[inst.instanceId for inst in inst_list])
        except Exception as error:
            log_error(logger, error, "Unexpected error while terminating instances", result)

    if os == 'windows':
        tmp = result.copy()
        result = {}
        for key, value in list(tmp.items()):
            if key.startswith('inst_'):
                result['win_{}'.format(key)] = value
            else:
                result[key] = value

    queue.put(result.copy())
