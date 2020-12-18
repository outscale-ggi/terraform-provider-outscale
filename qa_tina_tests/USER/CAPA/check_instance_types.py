# -*- coding: utf-8 -*-

import argparse
import datetime
import json
import os

from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdks.osc_sdk import OscSdk
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, KEY_PAIR, PATH
from qa_common_tools.ssh import SshTools
from json2html.jsonconv import json2html


INDEX = './index'
INSTANCES_CFG = './qa_tina/USER/CAPA/instance_type_list.json'
RESULT = 'result.json'
HTML = 'result.html'


def get_instance():

    # load instance type configuration
    json_file = open(INSTANCES_CFG)
    json_data = json_file.read()
    data = json.loads(json_data)
    json_file.close()

    # read index
    index = 0
    if os.path.isfile(INDEX):
        index_file = open(INDEX, 'r')
        index = int(index_file.read())
        index_file.close()
    else:
        open(INDEX, 'a').close()

    # incremente index
    index_file = open(INDEX, 'r+')
    index_file.seek(0)
    index_file.write(str((index+1)%len(data)))
    index_file.truncate()
    index_file.close()

    # return tested instance type
    return (sorted(data)[index], data[sorted(data)[index]])


def save_result(instance_type, status, comment):

    # Load results
    result = {}
    if os.path.isfile(RESULT):
        result_file = open(RESULT, 'r')
        result_data = result_file.read()
        result = json.loads(result_data)
        result_file.close()
    else:
        open(RESULT, 'a').close()
    result_file = open(RESULT, 'r+')

    # append current result
    if instance_type not in result:
        result[instance_type] = {}
    result[instance_type]['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result[instance_type]['status'] = status
    result[instance_type]['comment'] = comment

    # Save results
    result_file = open(RESULT, 'r+')
    result_file.seek(0)
    json.dump(result, result_file)
    result_file.truncate()
    result_file.close()

    # Convert results to html
    html_file = open(HTML, 'w')
    html_file.write(json2html.convert(json=result))
    html_file.close()


def exec_test(osc_sdk):

    instance_type, instance_type_cfg = get_instance()

    status = "TODO"
    comment = ""

    # Try to make test on all AZ
    for az in osc_sdk.config.region.get_info(constants.ZONE):
        info = None
        try:
            # Init default status
            status = "Ok"
            comment = ""

            info = create_instances(osc_sdk, az=az, inst_type=instance_type, state='ready')

            sshclient = SshTools.check_connection_paramiko(info[INSTANCE_SET][0]['ipAddress'], info[KEY_PAIR][PATH],
                                                           username=osc_sdk.config.region.get_info(constants.CENTOS_USER))

            cmd = "cat /proc/cpuinfo | grep -c proc"
            out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            if int(out) != instance_type_cfg['cpu']:
                status = "Ko"
                comment += "Wrong number of CPU ({} instead of {}) ".format(out, instance_type_cfg['cpu'])
            # TODO: check cpu generation ?

            cmd = """sudo dmidecode | grep "Maximum Capa" | sed 's/.*: //g'"""
            out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            out = out.strip().split(" ")
            if out[1] == 'MB':
                current = int(out[0])
                expected = instance_type_cfg['ram'] * 1024
            else:
                current = int(out[0])
                expected = instance_type_cfg['ram']
            if current != expected:
                status = "Ko"
                comment += "Wrong number of RAM ({} instead of {}) ".format(current, expected)

            cmd = "sudo yum install -y pciutils 2>&1 > /dev/null; /usr/sbin/lspci | grep -i -c nvidia"
            out, _, _ = SshTools.exec_command_paramiko(sshclient, cmd, expected_status=-1)
            if int(out) != instance_type_cfg['gpu']:
                status = "Ko"
                comment += "Wrong number of GPU ({} instead of {}) ".format(out, instance_type_cfg['gpu'])

        except OscApiException as error:
            status = error.error_code
            comment = error.message
            if error.error_code == "InsufficientInstanceCapacity":
                status = "Skip"
                continue
        except Exception as error:
            status = "Error"
            comment = str(error)
        finally:
            if info:
                delete_instances(osc_sdk, info)
        break

    save_result(instance_type, status, comment)


if __name__ == '__main__':

    ARGS_P = argparse.ArgumentParser(description="Check capacity for all instances types",
                                     formatter_class=argparse.RawTextHelpFormatter)

    ARGS_P.add_argument('-r', '--region-az', dest='az', action='store',
                        required=True, type=str,
                        help='Outscale region AZ used for the test')
    ARGS_P.add_argument('-a', '--account', dest='account', action='store',
                        required=True, type=str, help='Account used for the test')
    ARGS = ARGS_P.parse_args()

    OSC_SDK = OscSdk(config=OscConfig.get(az_name=ARGS.az, account_name=ARGS.account))

    exec_test(OSC_SDK)
