import base64
import uuid

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances_old, create_instances, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_instances, delete_vpc, \
    terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_RunInstances(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'memory_limit': 300, 'core_limit': 40}
        super(Test_RunInstances, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_RunInstances, cls).teardown_class()

    def run_with_instance_initiated_shutdown_behavior(self, value=None, value_to_check=None, status_code=200, error_code=None):
        inst_id = None
        if value and not value_to_check:
            value_to_check = value
        try:
            _, inst_id_list = create_instances_old(self.a1_r1, iisb=value, state='running')
            inst_id = inst_id_list[0]
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceInitiatedShutdownBehavior', InstanceId=inst_id)
            assert ret.response.instanceInitiatedShutdownBehavior.value == value_to_check
            assert ret.status_code == status_code
        except OscApiException as error:
            assert_error(error, status_code, error_code,
                         "Value of parameter \'InstanceInitiatedShutdownBehavior\' is not valid: " + \
                         "shutdown. Supported values: restart, stop, terminate")
        if inst_id:
            self.a1_r1.fcu.StopInstances(InstanceId=[inst_id])
            if value is None or value == 'stop':
                wait_instances_state(self.a1_r1, [inst_id], 'stopped')
                self.a1_r1.fcu.TerminateInstances(InstanceId=[inst_id])
            elif value == 'restart':
                wait_instances_state(self.a1_r1, [inst_id], 'running')
                self.a1_r1.fcu.TerminateInstances(InstanceId=[inst_id])
            wait_instances_state(self.a1_r1, [inst_id], 'terminated')
            ret = self.a1_r1.intel.instance.get(owner=self.a1_r1.config.account.account_id, id=inst_id)
            assert ret.response.result.state == 'terminated'
            assert ret.response.result.ustate == 'terminated'

    @pytest.mark.region_admin
    def test_T924_without_instance_shutdown_behavior(self):
        self.run_with_instance_initiated_shutdown_behavior(value_to_check='stop')

    @pytest.mark.region_admin
    def test_T925_with_instance_shutdown_behavior_stop(self):
        self.run_with_instance_initiated_shutdown_behavior(value='stop')

    @pytest.mark.region_admin
    def test_T926_with_instance_shutdown_behavior_terminate(self):
        self.run_with_instance_initiated_shutdown_behavior(value='terminate')

    @pytest.mark.region_admin
    def test_T927_with_instance_shutdown_behavior_restart(self):
        self.run_with_instance_initiated_shutdown_behavior(value='restart')

    @pytest.mark.region_admin
    def test_T928_with_instance_shutdown_behavior_invalid(self):
        self.run_with_instance_initiated_shutdown_behavior(value='shutdown', error_code='InvalidParameterValue', status_code=400)

    def test_T1454_with_userdata_private_only(self):
        userdata = """-----BEGIN OUTSCALE SECTION-----
private_only=true
-----END OUTSCALE SECTION-----"""
        ret, inst_id_list = create_instances_old(self.a1_r1, user_data=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'), state='running')
        assert not hasattr(ret.response.reservationSet[0].instancesSet[0], 'ipAddress')
        delete_instances_old(self.a1_r1, inst_id_list)

    def test_T2150_with_ephemeral_and_unsupported_instance_type(self):
        inst_info = create_instances(osc_sdk=self.a1_r1, inst_type='t2.small', nb_ephemeral=1)
        assert len(inst_info[INSTANCE_SET][0]['blockDeviceMapping']) == 1  # no ephemeral created, just a bootdisk
        delete_instances(self.a1_r1, inst_info)

    def test_T2277_with_incorrect_iops_in_bdm(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST), MinCount=1, MaxCount=1,
                                              BlockDeviceMapping=[{'DeviceName': '/dev/xvdb',
                                                                   'Ebs': {'VolumeSize': 600,
                                                                           'VolumeType': 'io1',
                                                                           'DeleteOnTermination': True,
                                                                           'Iops': 20000}}])
        except OscApiException as err:
            assert_error(err, 400, 'InvalidParameterValue', 'Invalid IOPS: 20000 Min: 100 Max: 13000')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    @pytest.mark.region_gpu
    def test_T3013_with_insufficient_capacity(self):
        inst_info = None
        try:
            inst_info = create_instances(self.a1_r1, inst_type='g3.8xlarge')
        except OscApiException as err:
            assert_error(err, 400, 'GpuLimitExceeded', 'The limit has exceeded: 0. Resource: g3.8xlarge.')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    @pytest.mark.region_admin
    @pytest.mark.region_gpu
    def test_T3014_with_insufficient_quotas(self):
        inst_info = None
        quotas = {'gpu_limit': 2}
        max_quota_value = None
        try:
            ret = self.a1_r1.intel.quota.find_for_account(owner=self.a1_r1.config.account.account_id, quota_names=['gpu_limit'])
            max_quota_value = ret.response.result.used.osc_global[0].max_quota_value
            for quota in quotas:
                self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={quota: quotas[quota]})
            inst_info = create_instances(self.a1_r1, inst_type='g3.8xlarge')
        except OscApiException as err:
            assert_error(err, 500, 'InsufficientInstanceCapacity', 'Insufficient Capacity')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
            if max_quota_value:
                quotas = {'gpu_limit': max_quota_value}
                for quota in quotas:
                    self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={quota: quotas[quota]})

    def test_T3048_with_invalid_private_address(self):
        vpc_info = None
        try:
            vpc_info = create_vpc(self.a1_r1, igw=False)
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST), MaxCount=1, MinCount=1,
                                              cidr_prefix="10.0", PrivateIpAddress='21.22.23.24')
            instance_ids = [inst.instanceId for inst in ret.response.instancesSet]
            terminate_instances(self.a1_r1, instance_ids)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination',
                         'Specifying an IP address is only valid for VPC instances and thus requires a subnet in which to launch')
        finally:
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)

    def test_T5029_with_the_same_token(self):
        token = str(uuid.uuid4())
        ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                          InstanceType='t2.nano', MaxCount=1, MinCount=1, ClientToken=token)
        ret1 = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                           InstanceType='t2.nano', MaxCount=1, MinCount=1, ClientToken=token)

        responses_describe = self.a1_r1.fcu.DescribeInstances(InstanceId=[ret.response.instancesSet[0].instanceId,
                                                                          ret1.response.instancesSet[0].instanceId])
        assert len(responses_describe.response.reservationSet) == 1
        terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5031_with_invalid_type_token(self):
        try:
            token = ['151475']
            self.a1_r1.fcu.RunInstances(ClientToken=token, ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                        MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType', "Value of parameter \'Token\' must be of type: str. Received: {\'1\': \'151475\'}")

    def test_T5842_with_wrong_instance_type(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='toto', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: toto')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5843_with_missing_cpu_gen(self):
        ret = None
        # Pour le known error TINA 6790.Il est en debut de test pour faire échouer les tests volentairement.
        known_error('TINA-6790', 'Instance type should raise an error')
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tina.c1r1', MaxCount=1, MinCount=1)
            wait_instances_state(self.a1_r1, [ret.response.instancesSet[0].instanceId], 'running')
        except OscApiException as error:
            assert_error(error, 500, 'InternalError', 'Internal Error')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5844_with_missing_cpu_gen_value(self):
        ret = None
        known_error('TINA-6790', 'Instance type should raise an error')
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav.c1r1', MaxCount=1, MinCount=1)
            wait_instances_state(self.a1_r1, [ret.response.instancesSet[0].instanceId], 'running')
        except OscApiException as error:
            assert_error(error, 500, 'InternalError', 'Internal Error')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5845_with_cpu_gen_value_set_at_zero(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav0.c1r1', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav0.c1r1')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5846_with_missing_perf_flag_value(self):
        ret = None
        known_error('TINA-6790', 'Instance type should raise an error')
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav1.c1r1p', MaxCount=1, MinCount=1)
            wait_instances_state(self.a1_r1, [ret.response.instancesSet[0].instanceId], 'running')
        except OscApiException as error:
            assert_error(error, 500, 'InternalError', 'Internal Error')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5847_with_perf_flag_set_at_zero(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav1.c1r1p0', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav1.c1r1p0')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5848_with_perf_flag_set_at_four(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav1.c1r1p4', MaxCount=1, MinCount=1)
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav1.c1r1p4')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5849_with_missing_core_value(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav1.cr1', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav1.cr1')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5850_with_core_value_set_at_zero(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav1.c0r1', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav1.c0r1')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5851_with_missing_memory_value(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav1.c1r', MaxCount=1, MinCount=1)

        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav1.c1r')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5852_with_memory_value_set_at_zero(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav1.c1r0', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav1.c1r0')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5853_with_override_max_value(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav5.c79r181', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if self.a1_r1.config.region.name == "in-west-2":
                if error.error_code in ["InsufficientInstanceCapacity","MemoryLimitExceeded"]:
                    known_error('OPS-14329', 'NEW IN2: configure instance type properties')
                assert False, 'Remove known error'
            else:
                assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav5.c39r181')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5868_with_empty_instance_type(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: ')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5919_with_cpu_gen_value_set_at_six(self):
        ret = None
        known_error('TINA-6790', 'Instance type should raise an error')
        try:
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST),
                                              InstanceType='tinav6.c1r1', MaxCount=1, MinCount=1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Invalid value for InstanceType: tinav6.c1r1')
        finally:
            if ret:
                terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])
