# pylint: disable=missing-docstring
import base64

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes, create_security_group, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, delete_volumes, \
    delete_security_group, delete_vpc
from qa_tina_tools.tools.tina.info_keys import SUBNETS, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_volumes_state


class Test_ModifyInstanceAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.vol_id_list = None
        cls.sg_id_list = []
        cls.vpc_info = None
        super(Test_ModifyInstanceAttribute, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=1, igw=False)
            cls.vpc_inst_id = cls.vpc_info[SUBNETS][0][INSTANCE_ID_LIST][0]
            cls.a1_r1.fcu.StopInstances(InstanceId=cls.vpc_inst_id)
            cls.inst_info = create_instances(cls.a1_r1, 2)
            cls.stopped_id = cls.inst_info[INSTANCE_ID_LIST][0]
            cls.running_id = cls.inst_info[INSTANCE_ID_LIST][1]
            cls.a1_r1.fcu.StopInstances(InstanceId=[cls.stopped_id])
            _, cls.vol_id_list = create_volumes(cls.a1_r1, count=2)
            wait_volumes_state(cls.a1_r1, cls.vol_id_list, 'available')
            cls.a1_r1.fcu.AttachVolume(Device="/dev/xvdb", InstanceId=cls.running_id, VolumeId=cls.vol_id_list[0])
            cls.a1_r1.fcu.AttachVolume(Device="/dev/xvdc", InstanceId=cls.running_id, VolumeId=cls.vol_id_list[1])
            wait_volumes_state(cls.a1_r1, cls.vol_id_list, 'in-use')
            for _ in range(2):
                cls.sg_id_list.append(create_security_group(cls.a1_r1))
            wait_instances_state(osc_sdk=cls.a1_r1, instance_id_list=[cls.stopped_id, cls.vpc_inst_id], state='stopped')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vol_id_list:
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.vol_id_list[0])
                cls.a1_r1.fcu.DetachVolume(VolumeId=cls.vol_id_list[1])
                wait_volumes_state(cls.a1_r1, cls.vol_id_list, 'available')
                delete_volumes(cls.a1_r1, cls.vol_id_list)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.sg_id_list:
                for sg_id in cls.sg_id_list:
                    delete_security_group(cls.a1_r1, sg_id)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_ModifyInstanceAttribute, cls).teardown_class()

    def test_T1803_missing_instance_id(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(DisableApiTermination={'Value': 'false'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: InstanceID')

    def test_T1804_incorrect_instance_id(self):
        inst_id = 'toto'
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=inst_id, DisableApiTermination={'Value': 'false'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.Malformed', 'Invalid ID received: toto. Expected format: i-')

    def test_T1805_unknown_instance_id(self):
        inst_id = 'i-12345678'
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=inst_id, DisableApiTermination={'Value': 'false'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', 'The instance IDs do not exist: i-12345678')

    def test_T1806_unknown_attribute_name(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, Toto={'Value': 'false'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'OWS.Error':
                known_error('TINA-4262', 'Incorrect error message')
            assert_error(error, 400, 'xxx', '')

    def test_T1807_incorrect_type_attribute(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, DisableApiTermination='false')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType', "Value of parameter 'DisableApiTermination' must be of type: dict. Received: false")

    def test_T1808_BlockDeviceMapping(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id,
                                                     BlockDeviceMapping=[{"DeviceName": "/dev/xvdb", "Ebs": {"DeleteOnTermination": False,
                                                                                                             "VolumeId": self.vol_id_list[0]}},
                                                                         {"DeviceName": "/dev/xvdc", "Ebs": {"DeleteOnTermination": True,
                                                                                                             "VolumeId": self.vol_id_list[1]}}])
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.running_id, Attribute='blockDeviceMapping')
        assert ret.response.instanceId == self.running_id
        assert isinstance(ret.response.blockDeviceMapping, list)
        assert len(ret.response.blockDeviceMapping) == 3

    def test_T1770_BlockMappingDevice_missing_device_name(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.stopped_id, BlockDeviceMapping=[{'Ebs': {'DeleteOnTermination': 'false',
                                                                                                            "VolumeId": self.vol_id_list[0]}}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: DeviceName')

    def test_T1809_BlockMappingDevice_missing_dot(self):
        try:
            ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id,
                                                         BlockDeviceMapping=[{"DeviceName": "/dev/xvdb", "Ebs": {"DeleteOnTermination": False,
                                                                                                                 "VolumeId": self.vol_id_list[0]}},
                                                                             {"DeviceName": "/dev/xvdc", "Ebs": {"VolumeId": self.vol_id_list[1]}}])
            assert False, 'Remove known error code'
            assert hasattr(ret.response, 'requestId')
            assert ret.response.osc_return
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.running_id, Attribute='blockDeviceMapping')
            assert ret.response.instanceId == self.running_id
            assert isinstance(ret.response.blockDeviceMapping, list)
            assert len(ret.response.blockDeviceMapping) == 3
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'MissingParameter' and \
                    error.message == 'Parameter cannot be empty: DeleteOnTermination':
                known_error('TINA-4262', 'Incorrect error message')
            raise error

    def test_T1810_DisableApiTermination(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, DisableApiTermination={'Value': 'false'})
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.running_id, Attribute='disableApiTermination')
        assert ret.response.instanceId == self.running_id
        assert ret.response.disableApiTermination.value == 'false'

    def test_T874_modify_ebs_optimized_false(self):
        self.a1_r1.fcu.ModifyInstanceAttribute(EbsOptimized={'Value': 'false'}, InstanceId=self.stopped_id)
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.stopped_id, Attribute='ebsOptimized')
        assert ret.response.ebsOptimized.value == 'false'

    def test_T875_modify_ebs_optimized_true(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(EbsOptimized={'Value': 'true'}, InstanceId=self.stopped_id)
            pytest.fail("ModifyInstanceAttribute should not have succeeded")
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'NotSupported'

    def test_T1811_modify_ebs_optimized_running(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(EbsOptimized={'Value': 'false'}, InstanceId=self.running_id)
            assert False, "ModifyInstanceAttribute should not have succeeded"
        except OscApiException as error:
            assert_error(error, 400, 'IncorrectInstanceState',
                         'Instances are not in a valid state for this operation: {}. State: running'.format(self.running_id))

    def test_T1812_GroupId(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.stopped_id, GroupId=self.sg_id_list)
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.stopped_id, Attribute='groupSet')
        assert ret.response.instanceId == self.stopped_id
        assert isinstance(ret.response.groupSet, list)
        assert len(ret.response.groupSet) == 2

    def test_T2168_GroupId_running(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, GroupId=self.sg_id_list)
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.running_id, Attribute='groupSet')
        assert ret.response.instanceId == self.running_id
        assert isinstance(ret.response.groupSet, list)
        assert len(ret.response.groupSet) == 2

    def test_T1813_IISB(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.stopped_id, InstanceInitiatedShutdownBehavior={'Value': 'stop'})
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.stopped_id, Attribute='instanceInitiatedShutdownBehavior')
        assert ret.response.instanceId == self.stopped_id
        assert ret.response.instanceInitiatedShutdownBehavior.value == 'stop'

    def test_T2169_IISB_running(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, InstanceInitiatedShutdownBehavior={'Value': 'stop'})
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.running_id, Attribute='instanceInitiatedShutdownBehavior')
        assert ret.response.instanceId == self.running_id
        assert ret.response.instanceInitiatedShutdownBehavior.value == 'stop'

    def test_T1814_IISB_unknown_value(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, InstanceInitiatedShutdownBehavior={'Value': 'toto'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value of parameter \'InstanceInitiatedShutdownBehavior\' is not valid: toto. Supported values: restart, stop, terminate")

    def test_T1815_InstanceType(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.stopped_id, InstanceType={'Value': 'tinav2.c4r16p2'})
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.stopped_id, Attribute='instanceType')
        assert ret.response.instanceId == self.stopped_id
        assert ret.response.instanceType.value == 'tinav2.c4r16p2'

    def test_T1816_InstanceType_unknown_value(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.stopped_id, InstanceType={'Value': 'toto'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid value for InstanceType: toto")

    def test_T1817_SourceDestCheck(self):
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.vpc_inst_id, SourceDestCheck={'Value': 'true'})
        assert hasattr(ret.response, 'requestId')
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.vpc_inst_id, Attribute='sourceDestCheck')
        assert ret.response.instanceId == self.vpc_inst_id
        assert ret.response.sourceDestCheck.value == 'true'

    def test_T1818_SourceDestCheck_unknown_value(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.vpc_inst_id, SourceDestCheck={'Value': 'toto'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'OWS.Error', 'Request is not valid.')

    def test_T1819_SourceDestCheck_public_instance(self):
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, SourceDestCheck={'Value': 'true'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination', "This attribute can only be modified for VPC instances: SourceDestCheck")

    def test_T1624_user_data_private_only_true_false(self):
        inst_info = None
        try:
            data_true = base64.encodestring(
                '-----BEGIN OUTSCALE SECTION-----\nprivate_only=true\n-----END OUTSCALE SECTION-----'.encode()).decode().strip()
            data_false = base64.encodestring(
                '-----BEGIN OUTSCALE SECTION-----\nprivate_only=false\n-----END OUTSCALE SECTION-----'.encode()).decode().strip()
            inst_info = create_instances(self.a1_r1, user_data=data_true)
            inst_id = inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_true, 'Incorrect user data value'
            ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id])
            inst = ret.response.reservationSet[0].instancesSet[0]
            assert hasattr(inst, 'privateIpAddress')
            assert not hasattr(inst, 'ipAddress')
            stop_instances(self.a1_r1, instance_id_list=[inst_id])
            self.a1_r1.fcu.ModifyInstanceAttribute(UserData={'Value': data_false}, InstanceId=inst_id)
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_false, 'Incorrect user data value'
            self.a1_r1.fcu.StartInstances(InstanceId=[inst_id])
            wait_instances_state(self.a1_r1, instance_id_list=[inst_id], state='running')
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_false, 'Incorrect user data value'
            ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id])
            inst = ret.response.reservationSet[0].instancesSet[0]
            assert hasattr(inst, 'privateIpAddress')
            if not hasattr(inst, 'ipAddress'):
                known_error('TINA-6134', 'incorrect ip allocation')
            assert False, 'Remove know error code'
            assert hasattr(inst, 'ipAddress')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T1625_user_data_private_only_false_true(self):
        inst_info = None
        try:
            data_true = base64.encodestring(
                '-----BEGIN OUTSCALE SECTION-----\nprivate_only=true\n-----END OUTSCALE SECTION-----'.encode()).decode().strip()
            data_false = base64.encodestring(
                '-----BEGIN OUTSCALE SECTION-----\nprivate_only=false\n-----END OUTSCALE SECTION-----'.encode()).decode().strip()
            inst_info = create_instances(self.a1_r1, user_data=data_false)
            inst_id = inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_false, 'Incorrect user data value'
            ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id])
            inst = ret.response.reservationSet[0].instancesSet[0]
            assert hasattr(inst, 'privateIpAddress')
            assert hasattr(inst, 'ipAddress')
            stop_instances(self.a1_r1, instance_id_list=[inst_id])
            self.a1_r1.fcu.ModifyInstanceAttribute(UserData={'Value': data_true}, InstanceId=inst_id)
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_true, 'Incorrect user data value'
            self.a1_r1.fcu.StartInstances(InstanceId=[inst_id])
            wait_instances_state(self.a1_r1, instance_id_list=[inst_id], state='running')
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_true, 'Incorrect user data value'
            ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id])
            inst = ret.response.reservationSet[0].instancesSet[0]
            assert hasattr(inst, 'privateIpAddress')
            if hasattr(inst, 'ipAddress'):
                known_error('TINA-6134', 'incorrect ip allocation')
            assert False, 'Remove know error code'
            assert not hasattr(inst, 'ipAddress')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T3987_incorrect_userdata_value(self):
        user_data = base64.encodestring('private_only=True'.encode()).decode().strip()
        try:
            self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=self.running_id, UserData=user_data)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterType", "Value of parameter 'UserData' must be of type: dict. Received: {}".format(user_data))

    def test_T5127_with_other_account(self):
        try:
            self.a2_r1.fcu.ModifyInstanceAttribute(InstanceId=self.stopped_id, InstanceType={'Value': 'tinav2.c4r16p2'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidInstanceID.NotFound", "The instance IDs do not exist: {}".format(self.stopped_id))
