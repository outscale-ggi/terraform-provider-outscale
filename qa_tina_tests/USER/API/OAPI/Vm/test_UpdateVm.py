# -*- coding:utf-8 -*-
import base64

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, id_generator, assert_dry_run
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tests.USER.API.OAPI.Vm.Vm import create_vms
from qa_tina_tools.tools.tina.create_tools import create_instances, create_security_group
from qa_tina_tools.tools.tina.delete_tools import stop_instances, delete_instances, \
    terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_instances_state


class Test_UpdateVm(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.info = None
        cls.vol_ids = None
        cls.vm_ids = None
        cls.subnet_id = None
        cls.vpc_id = None
        super(Test_UpdateVm, cls).setup_class()
        try:
            ret = cls.a1_r1.fcu.CreateVpc(CidrBlock='10.0.0.0/16')
            cls.vpc_id = ret.response.vpc.vpcId
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock='10.0.0.0/24', VpcId=cls.vpc_id)
            cls.subnet_id = [ret.response.subnet.subnetId]
            _, cls.vpc_inst_ids = create_vms(cls.a1_r1, state='pending', SubnetId=cls.subnet_id[0])
            _, cls.vm_ids = create_vms(ocs_sdk=cls.a1_r1, MaxVmsCount=2, MinVmsCount=2)
            cls.vm_ids += cls.vpc_inst_ids
            cls.a1_r1.fcu.StopInstances(InstanceId=[cls.vm_ids[1]], Force=True)
            ret_vol = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.azs[0], Size=1)
            ret_vol2 = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.azs[0], Size=1)
            cls.vol_ids = [ret_vol.response.volumeId, ret_vol2.response.volumeId]
            wait_volumes_state(cls.a1_r1, cls.vol_ids, 'available')
            cls.a1_r1.fcu.AttachVolume(Device="/dev/xvdb", InstanceId=cls.vm_ids[0], VolumeId=cls.vol_ids[0])
            cls.a1_r1.fcu.AttachVolume(Device="/dev/xvdc", InstanceId=cls.vm_ids[0], VolumeId=cls.vol_ids[1])
            wait_volumes_state(cls.a1_r1, cls.vol_ids, 'in-use')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vol_ids:
                for vol in cls.vol_ids:
                    cls.a1_r1.fcu.DetachVolume(VolumeId=vol)
                wait_volumes_state(cls.a1_r1, cls.vol_ids, 'available')
                for vol in cls.vol_ids:
                    cls.a1_r1.fcu.DeleteVolume(VolumeId=vol)
            if cls.vm_ids:
                cls.a1_r1.fcu.StopInstances(InstanceId=cls.vm_ids, Force=True)
                cls.a1_r1.fcu.TerminateInstances(InstanceId=cls.vm_ids)
                wait_instances_state(cls.a1_r1, cls.vm_ids, state='terminated')
            if cls.subnet_id:
                for sub_id in cls.subnet_id:
                    cls.a1_r1.fcu.DeleteSubnet(SubnetId=sub_id)
            if cls.vpc_id:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)
        finally:
            super(Test_UpdateVm, cls).teardown_class()

    def test_T2127_missing_instance_id(self):
        try:
            self.a1_r1.oapi.UpdateVm(DeletionProtection=False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2128_incorrect_instance_id(self):
        inst_id = 'toto'
        try:
            self.a1_r1.oapi.UpdateVm(VmId=inst_id, DeletionProtection=False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert error.status_code == 400

    def test_T2129_unknown_instance_id(self):
        inst_id = 'i-12345678'
        try:
            self.a1_r1.oapi.UpdateVm(VmId=inst_id, DeletionProtection=False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    def test_T2130_unknown_attribute_name(self):
        try:
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], Toto=False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T2131_incorrect_type_attribute(self):
        try:
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], DeletionProtection='false')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T2132_BlockDeviceMapping(self):
        self.a1_r1.oapi.UpdateVm(
            VmId=self.vm_ids[0],
            BlockDeviceMappings=[
                {"DeviceName": "/dev/xvdb", "Bsu": {"DeleteOnVmDeletion": False, "VolumeId": self.vol_ids[0]}},
                {"DeviceName": "/dev/xvdc", "Bsu": {"DeleteOnVmDeletion": True, "VolumeId": self.vol_ids[1]}}])
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[0]]}).response.Vms[0]
        assert ret.VmId == self.vm_ids[0]
        assert len(ret.BlockDeviceMappings) == 3
        assert "/dev/xvdb" in (x.DeviceName for x in ret.BlockDeviceMappings)
        assert "/dev/xvdc" in (x.DeviceName for x in ret.BlockDeviceMappings)
        assert "/dev/sda1" in (x.DeviceName for x in ret.BlockDeviceMappings)
        assert self.vol_ids[0] in (x.Bsu.VolumeId for x in ret.BlockDeviceMappings)

    def test_T2133_BlockMappingDevice_missing_device_name(self):
        try:
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[1],
                                     BlockDeviceMappings=[
                                         {'Bsu': {'DeleteOnVmDeletion': 'false', "VolumeId": self.vol_ids[0]}}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T2134_BlockMappingDevice_missing_dot(self):
        try:
            ret = self.a1_r1.oapi.UpdateVm(
                VmId=self.vm_ids[0],
                BlockDeviceMappings=[
                    {"DeviceName": "/dev/xvdb", "Bsu": {"DeleteOnVmDeletion": False, "VolumeId": self.vol_ids[0]}},
                    {"DeviceName": "/dev/xvdc", "Bsu": {"VolumeId": self.vol_ids[1]}}])
            assert hasattr(ret.response, 'requestId')
            assert ret.response.osc_return
            ret = self.a1_r1.oapi.ReadVmAttribute(VmId=self.vm_ids[0], Attribute='BlockDeviceMappings')
            assert ret.response.VmId == self.vm_ids[0]
            assert len(ret.response.BlockDeviceMappings) == 3
            assert "/dev/xvdb" in (x.DeviceName for x in ret.response.BlockDeviceMappings)
            assert "/dev/xvdc" in (x.DeviceName for x in ret.response.BlockDeviceMappings)
            assert "/dev/sda1" in (x.DeviceName for x in ret.response.BlockDeviceMappings)
            assert self.vol_ids[0] in (x.Bsu.VolumeId for x in ret.response.BlockDeviceMappings)

        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2135_DisableApiTermination(self):
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], DeletionProtection=True)
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[0]]}).response.Vms[0]
        assert ret.VmId == self.vm_ids[0]
        assert ret.DeletionProtection is True

        self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], DeletionProtection=False)
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[0]]}).response.Vms[0]
        assert ret.VmId == self.vm_ids[0]
        assert ret.DeletionProtection is False

    def test_T2136_modify_ebs_optimized_false(self):
        self.a1_r1.oapi.UpdateVm(BsuOptimized=False, VmId=self.vm_ids[1])
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[1]]}).response.Vms[0]
        assert ret.VmId == self.vm_ids[1]
        assert ret.BsuOptimized is False

    def test_T2137_modify_ebs_optimized_true(self):
        try:
            self.a1_r1.oapi.UpdateVm(BsuOptimized=True, VmId=self.vm_ids[1])
            pytest.fail("UpdateVm should not have succeeded")
        except OscApiException as error:
            # this is the good error only if the vm_id selected have configuration compatibility problems.
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4017')

    def test_T2138_modify_ebs_optimized_running(self):
        try:
            self.a1_r1.oapi.UpdateVm(BsuOptimized=False, VmId=self.vm_ids[0])
            assert False, "UpdateVm should not have succeeded"
        except OscApiException as error:
            assert_oapi_error(error, 409, 'InvalidState', '6003')

    def test_T2139_GroupId(self):
        sg_id = None
        try:
            ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[0]]}).response.Vms[0]
            sg_id = create_security_group(self.a1_r1, id_generator(prefix='T2139'), 'desc')
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], SecurityGroupIds=[sg_id])
            ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[0]]}).response.Vms[0]
            assert ret.VmId == self.vm_ids[0]
            assert ret.DeletionProtection is False
            assert isinstance(ret.SecurityGroups, list)
            assert ret.SecurityGroups[0].SecurityGroupId == sg_id
        finally:
            pass

    def test_T2140_IISB(self):
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], VmInitiatedShutdownBehavior='stop')
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[0]]}).response.Vms[0]
        assert ret.VmId == self.vm_ids[0]
        assert ret.VmInitiatedShutdownBehavior == 'stop'

    def test_T2141_IISB_unknown_value(self):
        try:
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], VmInitiatedShutdownBehavior='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2142_InstanceType(self):
        self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[1], VmType='m4.xlarge')
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[1]]}).response.Vms[0]
        assert ret.VmId == self.vm_ids[1]
        assert ret.VmType == 'm4.xlarge'
        assert ret.Performance == 'high'

    def test_T2143_InstanceType_unknown_value(self):
        try:
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[1], VmType='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5024')

    def test_T2144_SourceDestCheck(self):
        self.a1_r1.oapi.UpdateVm(VmId=self.vpc_inst_ids[0], IsSourceDestChecked=True)
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vpc_inst_ids[0]]}).response.Vms[0]
        assert ret.VmId == self.vpc_inst_ids[0]
        assert ret.IsSourceDestChecked

    def test_T2145_SourceDestCheck_unknown_value(self):
        try:
            self.a1_r1.oapi.UpdateVm(VmId=self.vpc_inst_ids[0], IsSourceDestChecked='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T2146_SourceDestCheck_public_instance(self):
        try:
            self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[0], IsSourceDestChecked=True)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 409, 'ResourceConflict', '9062')

    def test_T2147_user_data_private_only_true_false(self):
        inst_info = None
        try:
            data_true = base64.encodebytes(
                '-----BEGIN OUTSCALE SECTION-----\nprivate_only=true\n-----END OUTSCALE SECTION-----'.encode()).decode().strip()
            data_false = base64.encodebytes(
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
            self.a1_r1.oapi.UpdateVm(UserData=data_false, VmId=inst_id)
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_false, 'Incorrect user data value'
            self.a1_r1.oapi.StartVms(VmIds=[inst_id])
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
        except OscApiException as error:
            raise error
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T2148_user_data_private_only_false_true(self):
        inst_info = None
        try:
            data_true = base64.encodebytes(
                '-----BEGIN OUTSCALE SECTION-----\nprivate_only=true\n-----END OUTSCALE SECTION-----'.encode()).decode().strip()
            data_false = base64.encodebytes(
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
            self.a1_r1.oapi.UpdateVm(UserData=data_true, VmId=inst_id)
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_true, 'Incorrect user data value'
            self.a1_r1.oapi.StartVms(VmIds=[inst_id])
            wait_instances_state(self.a1_r1, instance_id_list=[inst_id], state='running')
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == data_true, 'Incorrect user data value'
            ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id])
            inst = ret.response.reservationSet[0].instancesSet[0]
            assert hasattr(inst, 'privateIpAddress')
            if hasattr(inst, 'ipAddress'):
                known_error('TINA-6134', 'incorrect ip allocation')
            assert not hasattr(inst, 'ipAddress')
        except OscApiException as error:
            raise error
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T3541_dry_run(self):
        ret = self.a1_r1.oapi.UpdateVm(VmId=self.vm_ids[1], VmType='m4.xlarge', DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3542_other_account(self):
        try:
            self.a2_r1.oapi.UpdateVm(VmId=self.vm_ids[1], VmType='m4.xlarge')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5063')

    def test_T3188_userdata_auto_attach(self):
        public_ip = None
        try:
            public_ip = self.a1_r1.oapi.CreatePublicIp().response.PublicIp.PublicIp
            userdata = base64.b64encode("""-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.eip.auto-attach={}
            -----END OUTSCALE SECTION-----""".format(public_ip).encode('utf-8')).decode('utf-8')
            inst_info = create_instances(self.a1_r1)
            inst_id = inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id])
            inst = ret.response.reservationSet[0].instancesSet[0]
            assert hasattr(inst, 'privateIpAddress')
            assert hasattr(inst, 'ipAddress')
            stop_instances(self.a1_r1, instance_id_list=[inst_id])
            self.a1_r1.oapi.UpdateVm(UserData=userdata, VmId=inst_id)
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == userdata, 'Incorrect user data value'
            self.a1_r1.oapi.StartVms(VmIds=[inst_id])
            wait_instances_state(self.a1_r1, instance_id_list=[inst_id], state='running')
            ret = self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=inst_id, Attribute='userData')
            assert ret.response.userData.value == userdata, 'Incorrect user data value'
            ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id])
            inst = ret.response.reservationSet[0].instancesSet[0]
            assert inst.ipAddress == public_ip
        except OscApiException as error:
            raise error
        finally:
            if public_ip:
                self.a1_r1.oapi.DeletePublicIp(PublicIp=public_ip)

    def test_T4899_base64_userdata(self):
        userdata= """I2Nsb3VkLWNvbmZpZwpjbG91ZF9jb25maWdfbW9kdWxlczoKLSBydW5jbWQKCnJ1bmNtZDoKLSB0b
        3VjaCAvdG1wL3FhLXZhbGlkLXRlcnJhZm9ybS11c2VyLWRhdGEtY2xvdWQtaW5pdAotIGVjaG8gImJsYWJsYSIgPj4gL2Rldi90dHlTMAo="""
        try:
            inst_info = create_instances(self.a1_r1)
            inst_id = inst_info[INSTANCE_ID_LIST][0]
            stop_instances(self.a1_r1, instance_id_list=[inst_id])
            self.a1_r1.oapi.UpdateVm(UserData=userdata, VmId=inst_id)
        except OscApiException as error:
            raise error
        finally:
            terminate_instances(self.a1_r1, [inst_id])
