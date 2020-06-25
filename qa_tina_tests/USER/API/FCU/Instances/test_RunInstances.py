import base64
import uuid

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances_old, create_instances, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_instances, delete_vpc, terminate_instances
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET
from qa_test_tools.misc import assert_error
from qa_test_tools.config import config_constants as constants
import pytest


class Test_RunInstances(OscTestSuite):

    @classmethod
    def setup_class(cls):
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
                         "Value of parameter \'InstanceInitiatedShutdownBehavior\' is not valid: shutdown. Supported values: restart, stop, terminate")
        if inst_id:
            self.a1_r1.fcu.StopInstances(InstanceId=[inst_id])
            if value is None or value == 'stop':
                wait_instances_state(self.a1_r1, [inst_id], 'stopped')
                self.a1_r1.fcu.TerminateInstances(InstanceId=[inst_id])
            elif value == 'restart':
                wait_instances_state(self.a1_r1, [inst_id], 'running')
                self.a1_r1.fcu.TerminateInstances(InstanceId=[inst_id])
            wait_instances_state(self.a1_r1, [inst_id], 'terminated')

    def test_T924_without_instance_shutdown_behavior(self):
        self.run_with_instance_initiated_shutdown_behavior(value_to_check='stop')

    def test_T925_with_instance_shutdown_behavior_stop(self):
        self.run_with_instance_initiated_shutdown_behavior(value='stop')

    def test_T926_with_instance_shutdown_behavior_terminate(self):
        self.run_with_instance_initiated_shutdown_behavior(value='terminate')

    def test_T927_with_instance_shutdown_behavior_restart(self):
        self.run_with_instance_initiated_shutdown_behavior(value='restart')

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
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7), MinCount=1, MaxCount=1,
                                              BlockDeviceMapping=[{'DeviceName': '/dev/xvdb',
                                                                   'Ebs': {'VolumeSize': 600,
                                                                           'VolumeType': 'io1',
                                                                           'DeleteOnTermination': True,
                                                                           'Iops': 20000}}])
        except OscApiException as err:
            assert_error(err, 400, 'InvalidParameterValue', 'Invalid IOPS, min_iops: 100, max_iops: 13000')
        finally:
            if ret:
                self.a1_r1.fcu.TerminateInstances(ret.response.instancesSet[0].instanceID)

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
    def test_T3014_with_insufficient_quotas(self):
        inst_info = None
        self.QUOTAS = {'gpu_limit': 2}
        try:
            ret = self.a1_r1.icu.ReadQuotas()
            MaxQuotaValue = ret.response.ReferenceQuota[0].Quotas[4].MaxQuotaValue
            for quota in self.QUOTAS:
                self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={quota: self.QUOTAS[quota]})
            inst_info = create_instances(self.a1_r1, inst_type='g3.8xlarge')
        except OscApiException as err:
            assert_error(err, 500, 'InsufficientInstanceCapacity', 'Insufficient Capacity')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
            self.QUOTAS = {'gpu_limit': MaxQuotaValue}
            for quota in self.QUOTAS:
                self.a1_r1.intel.user.update(username=self.a1_r1.config.account.account_id, fields={quota: self.QUOTAS[quota]})

    def test_T3048_with_invalid_private_address(self):
        vpc_info = None
        try:
            vpc_info = create_vpc(self.a1_r1, igw=False)
            ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7), MaxCount=1, MinCount=1,
                                              cidr_prefix="10.0", PrivateIpAddress='21.22.23.24')
            instanceIds = [inst.instanceId for inst in ret.response.instancesSet]
            terminate_instances(self.a1_r1, instanceIds)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination',
                         'Specifying an IP address is only valid for VPC instances and thus requires a subnet in which to launch')
        finally:
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)

    def test_T5029_with_the_same_token(self):
        token = str(uuid.uuid4())
        ret = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                          InstanceType='t2.nano', MaxCount=1, MinCount=1,
                                          ClientToken=token)
        ret1 = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                           InstanceType='t2.nano', MaxCount=1, MinCount=1,
                                           ClientToken=token)

        responses_describe = self.a1_r1.fcu.DescribeInstances(InstanceId=[ret.response.instancesSet[0].instanceId, ret1.response.instancesSet[0].instanceId])
        assert len(responses_describe.response.reservationSet) == 1
        terminate_instances(self.a1_r1, [ret.response.instancesSet[0].instanceId])

    def test_T5031_with_invalid_type_token(self):
        try:
            token = ['151475']
            self.a1_r1.fcu.RunInstances(ClientToken=token, ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                        MaxCount=1, MinCount=1)
            assert False, 'Cal should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType', "Value of parameter \'Token\' must be of type: str. Received: {\'1\': \'151475\'}")
