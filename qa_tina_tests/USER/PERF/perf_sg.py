from datetime import datetime
import subprocess
from subprocess import CalledProcessError
from threading import current_thread

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.wait_tools import wait_security_groups_state, wait_keypairs_state, wait_instances_state
from qa_tina_tests.USER.PERF.perf_common import log_error


MAX_WAIT_TIME = 120


def perf_sg(oscsdk, logger, queue, args):

    thread_name = current_thread().name

    # element names
    inst_name = 'psg_inst_{}'.format(thread_name)
    kp_name = 'psg_kp_{}_{}'.format(args.az[:-1], thread_name)
    sg_name = 'psg_sg_{}'.format(thread_name)

    if not args.omi:
        logger.debug("OMI not specified, select default OMI")
        omi = oscsdk.config.region.get_info(constants.CENTOS7)
    else:
        omi = args.omi

    if not args.inst_type:
        logger.debug("Instance type not specified, select default instance type")
        inst_type = oscsdk.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
    else:
        inst_type = args.inst_type

    result = {'status': 'OK'}

    # check key pair
    kp = False
    if result['status'] != "KO":
        logger.debug("Describe Keypair")
        try:
            ret = oscsdk.fcu.DescribeKeyPairs(Filter=[{'Name': 'key-name', 'Value': kp_name}])
            kp = ret.response.keySet and len(ret.response.keySet) == 1
        except Exception as error:
            log_error(logger, error, "Unexpected error while checking key pair", result)

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

    # check instance
    inst = None
    if result['status'] != "KO":
        logger.debug("Describe Instance")
        try:
            ret = oscsdk.fcu.DescribeInstances(Filter=[{'Name': 'tag:Name', 'Value': inst_name}])
            if ret.response.reservationSet:
                for res in ret.response.reservationSet:
                    for i in res.instancesSet:
                        if i.instanceState.name == 'running':
                            inst = i
                            break
                        if i.instanceState.name == 'stopped':
                            oscsdk.fcu.StartInstances(InstanceId=[i.instanceId])
                            wait_instances_state(oscsdk, [i.instanceId], state='ready')
                            inst = i
                            break

        except Exception as error:
            log_error(logger, error, "Unexpected error while checking test instance", result)

    if not kp and result['status'] != "KO":
        try:
            create_keypair(oscsdk, name=kp_name)
            wait_keypairs_state(oscsdk, [kp_name])
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating key pair", result)

    if not sg and result['status'] != "KO":
        try:
            sg = oscsdk.fcu.CreateSecurityGroup(GroupName=sg_name,
                                                GroupDescription='Security_Group_For_{}'.format(thread_name)).response.groupId
            wait_security_groups_state(oscsdk, [sg])
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating security group", result)

    if not inst and result['status'] != "KO":

        logger.debug("Run instance")
        try:
            ret = oscsdk.fcu.RunInstances(ImageId=omi, MinCount=1, MaxCount=1, InstanceType=inst_type, SecurityGroup=[sg], KeyName=kp_name)
            inst = ret.response.instancesSet[0]
            wait_instances_state(oscsdk, [inst.instanceId], state='ready')
            oscsdk.fcu.CreateTags(ResourceId=inst.instanceId, Tag=[{'Key': 'Name', 'Value': inst_name}])
            ret = oscsdk.fcu.DescribeInstances(Filter=[{'Name': 'tag:Name', 'Value': inst_name},
                                                       {'Name': 'instance-state-name', 'Value': 'running'}])
            inst = ret.response.reservationSet[0].instancesSet[0]
        except Exception as error:
            log_error(logger, error, "Unexpected error while creating test instance", result)

    if result['status'] != "KO":
        logger.debug("Authorize ICMP")
        try:
            start_ping = datetime.now()
            oscsdk.fcu.AuthorizeSecurityGroupIngress(GroupId=sg, FromPort=-1, ToPort=-1, IpProtocol='icmp',
                                                     CidrIp=Configuration.get('cidr', 'allips'))
        except OscApiException as error:
            logger.error("Unexpected error while creating ICMP rule.")
            logger.debug('Error: {}'.format(error))
            if 'Duplicate CIDR' in error.message:
                oscsdk.fcu.RevokeSecurityGroupIngress(GroupId=sg, FromPort=-1, ToPort=-1, IpProtocol='icmp',
                                                      CidrIp=Configuration.get('cidr', 'allips'))
            result['status'] = "KO"

    if result['status'] != "KO":
        logger.debug("Ping instance with ICMP rule")
        try:
            success = False
            while not success and (datetime.now() - start_ping).total_seconds() < MAX_WAIT_TIME:
                args = ["ping", "-c", "5", inst.ipAddress]
                try:
                    subprocess.check_call(args)
                    success = True
                except CalledProcessError:
                    success = False
            if success:
                ping_suceed = (datetime.now() - start_ping).total_seconds()
                result['sg_rule_add'] = ping_suceed
            else:
                result['sg_rule_add'] = MAX_WAIT_TIME
                result['status'] = "KO"
                oscsdk.fcu.RevokeSecurityGroupIngress(GroupId=sg, FromPort=-1, ToPort=-1, IpProtocol='icmp',
                                                      CidrIp=Configuration.get('cidr', 'allips'))
        except Exception as error:
            log_error(logger, error, "Unexpected error while ping instance", result)

    if result['status'] != "KO":
        logger.debug("remove ICMP rule in SG")
        try:
            start_ping = datetime.now()
            ret = oscsdk.fcu.RevokeSecurityGroupIngress(GroupId=sg, FromPort=-1, ToPort=-1, IpProtocol='icmp',
                                                        CidrIp=Configuration.get('cidr', 'allips'))
        except Exception as error:
            log_error(logger, error, "Unexpected error while removing ICMP rule.", result)

    if result['status'] != "KO":
        logger.debug("Ping instance without ICMP rule")
        try:
            success = False
            while not success and (datetime.now() - start_ping).total_seconds() < MAX_WAIT_TIME:
                args = ["ping", "-c", "5", inst.ipAddress]
                try:
                    subprocess.check_call(args)
                    success = False
                except CalledProcessError:
                    success = True
            if success:
                ping_failed = (datetime.now() - start_ping).total_seconds()
                result['sg_rule_del'] = ping_failed
            else:
                result['status'] = "KO"
        except Exception as error:
            log_error(logger, error, "Unexpected error while ping instance without ICMP rule", result)

    queue.put(result.copy())
