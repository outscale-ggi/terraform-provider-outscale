import argparse
import datetime
import logging
from pprint import pprint
import ssl

from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs, cleanup_instances
from qa_tina_tools.tools.tina.create_tools import create_instances, create_vpc
from qa_tina_tools.tools.tina.delete_tools import stop_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, SUBNETS, SUBNET_ID, NONE
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
# ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG
TYPE = 'Type'
DEDICATED = 'Dedicated'
FNI = 'Fni'
EPHEMERAL = 'Ephemeral'
STATE = 'State'
NUM = 'Num'
FGPU = 'Fgpu'
RUNNING = 'running'
STOPPED = 'stopped'
DEFAULT_MODEL_NAME = "nvidia-k2"

CREATE_INFOS = [
    # c4: check simple start or stop/start
    {STATE: 'running', TYPE: 'c4.large', FNI: False, DEDICATED: True, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    {STATE: 'running', TYPE: 'c4.large', FNI: True, DEDICATED: False, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    {STATE: 'stopped', TYPE: 'c4.large', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    {STATE: 'running', TYPE: 'c4.large', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    # m4: check simple start or stop/start
    {STATE: 'running', TYPE: 'm4.large', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    {STATE: 'stopped', TYPE: 'm4.large', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    {STATE: 'running', TYPE: 'm4.large', FNI: False, DEDICATED: True, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    {STATE: 'running', TYPE: 'm4.large', FNI: True, DEDICATED: False, EPHEMERAL: 0, NUM: 1, FGPU: 0},
    # m3: check simple start or stop/start --> 4 inst pour retest en cas de bug...
    {STATE: 'running', TYPE: 'm3.large', FNI: False, DEDICATED: False, EPHEMERAL: 1, NUM: 4, FGPU: 0},
    {STATE: 'stopped', TYPE: 'm3.large', FNI: False, DEDICATED: False, EPHEMERAL: 1, NUM: 4, FGPU: 0},
    # mv3: check simple start or stop/start --> 2 inst pour retest en cas de bug... on prend tous les GPU dispo
    {STATE: 'running', TYPE: 'mv3.large', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 'mv3.large', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    # t2: par defaut 2 inst pour retest en cas de bug et simple start or stop/start
    {STATE: 'running', TYPE: 't2.nano', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 't2.nano', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 't2.nano', FNI: False, DEDICATED: True, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 't2.micro', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 4, FGPU: 0}, # 2*(start/stop) + 2*(reboot/stop/start)
    {STATE: 'stopped', TYPE: 't2.micro', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 4, FGPU: 0}, # 2*(start) + 2*(updateType/start)
    {STATE: 'running', TYPE: 't2.micro', FNI: False, DEDICATED: True, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 't2.small', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 't2.small', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 't2.small', FNI: False, DEDICATED: True, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    ####
    # TODO: add 2 inst t2.micro running avec ShutdownBehavior = restart pour check migration sur simple stop
    ####
    # tinacxry: par defaut 2 inst pour retest en cas de bug et simple start or stop/start
    # TODO: si pb de capa, basculer sur AZ B pour les dernières instances...
    {STATE: 'running', TYPE: 'tinav2.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 'tinav2.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 'tinav3.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 'tinav3.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 'tinav3.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 1, NUM: 2, FGPU: 0}, # TODO; check ephemeral aftre runInstance
    {STATE: 'running', TYPE: 'tinav4.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 4, FGPU: 0}, # 2*(start/stop) + 2*(reboot/stop/start)
    {STATE: 'stopped', TYPE: 'tinav4.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 4, FGPU: 0}, # 2*(start) + 2*(updateType/start)
    {STATE: 'running', TYPE: 'tinav4.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 1},
    {STATE: 'running', TYPE: 'tinav5.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 'tinav5.c1r2', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    # deprecated: check simple start or stop/start
    {STATE: 'running', TYPE: 'c1.medium', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 'c1.medium', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 'm1.medium', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 'm1.medium', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'running', TYPE: 't1.micro', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0},
    {STATE: 'stopped', TYPE: 't1.micro', FNI: False, DEDICATED: False, EPHEMERAL: 0, NUM: 2, FGPU: 0}
    ]


def run(args):
    config = OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE)
    osc_sdk = OscSdk(config)

    infos = []
    try:
        cleanup_vpcs(osc_sdk)
        cleanup_instances(osc_sdk)
        start = datetime.datetime.now()
        vpc_info = create_vpc(osc_sdk, igw=False)
        inst_ids = []
        for info in CREATE_INFOS:
            subnet_id = None
            if info[FNI] is True:
                subnet_id = vpc_info[SUBNETS][0][SUBNET_ID]

            ret = create_instances(osc_sdk, key_name=args.key_name, inst_type=info[TYPE], subnet_id=subnet_id, sg_id_list=NONE, nb=info[NUM],
                                   dedicated=info[DEDICATED], nb_ephemeral=info[EPHEMERAL], state=None)
            values = [TYPE, info[TYPE], STATE, info[STATE]]
            if info[FNI] is True:
                values.append(FNI)
            if info[DEDICATED] is True:
                values.append(DEDICATED)
            if info[EPHEMERAL] is True:
                values.append(EPHEMERAL)
            if info[FGPU] > 0:
                values.append(FGPU)
            tag_value = '__'.join(values)
            osc_sdk.fcu.CreateTags(ResourceId=ret[INSTANCE_ID_LIST][0:1], Tag=[{'Key': 'SPECS', 'Value': tag_value}])
            inst_ids.append(ret[INSTANCE_ID_LIST][0])
            infos.append({'InstanceIds': ret[INSTANCE_ID_LIST], 'Infos': info})

        wait_instances_state(osc_sdk, inst_ids, state='running')

        for i, _ in enumerate(CREATE_INFOS):
            if CREATE_INFOS[i][STATE] == STOPPED:
                stop_instances(osc_sdk, inst_ids[i:i+1])
            if CREATE_INFOS[i][FNI] is True:
                ret_ni = osc_sdk.fcu.CreateNetworkInterface(SubnetId=vpc_info[SUBNETS][0][SUBNET_ID])
                osc_sdk.fcu.AttachNetworkInterface(DeviceIndex=1, InstanceId=inst_ids[i],
                                                   NetworkInterfaceId=ret_ni.response.networkInterface.networkInterfaceId)
            if CREATE_INFOS[i][FGPU] > 0:
                fg_id = osc_sdk.oapi.CreateFlexibleGpu(ModelName=DEFAULT_MODEL_NAME,
                                                       SubregionName=osc_sdk.config.region.az_name).response.FlexibleGpu.FlexibleGpuId
                osc_sdk.oapi.LinkFlexibleGpu(FlexibleGpuId=fg_id, VmId=ret[INSTANCE_ID_LIST][0])
        print("Instances creation took -> {}".format(datetime.datetime.now() - start))

    except Exception as error:
        print(error)

    pprint(infos)


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
    main_args = args_p.parse_args()

    run(main_args)
