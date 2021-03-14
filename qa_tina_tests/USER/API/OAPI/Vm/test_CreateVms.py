
import base64
import string
import zlib

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import KEY_PAIR, PATH
from qa_tina_tools.tina.oapi import delete_Vms, create_Vms
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state, wait_network_interfaces_state, wait_security_groups_state
from qa_tina_tests.USER.API.OAPI.Vm.Vm import validate_vm_response, create_vms


class Test_CreateVms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.user_data = '''#!/usr/bin/bash
echo "yes" > /tmp/userdata.txt
'''
        cls.info = None
        super(Test_CreateVms, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateVms, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateVms, self).setup_method(method)
        self.info = None

    def teardown_method(self, method):
        try:
            if self.info:
                wait_instances_state(self.a1_r1, instance_id_list=self.info, state='running')
                self.a1_r1.oapi.StopVms(VmIds=self.info, ForceStop=True)
                self.a1_r1.oapi.DeleteVms(VmIds=self.info)
                wait_instances_state(self.a1_r1, self.info, state='terminated')
        finally:
            super(Test_CreateVms, self).teardown_method(method)

    def check_user_data(self, vm_info, gzip=False, decode=True):
        sshclient = SshTools.check_connection_paramiko(vm_info['vms'][0]['PublicIp'], vm_info[KEY_PAIR][PATH],
                                                       username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        out, _, _ = SshTools.exec_command_paramiko(sshclient, 'curl http://169.254.169.254/latest/user-data', decode=decode)
        if gzip:
            self.logger.debug(zlib.decompress(out))
            out = zlib.decompress(out).decode('utf-8')
        assert out.replace("\r\n", "\n") == self.user_data
        if not gzip:
            out, _, _ = SshTools.exec_command_paramiko(sshclient, 'cat /tmp/userdata.txt')
            assert out.startswith('yes')

    def test_T2937_missing_param(self):
        try:
            self.a1_r1.oapi.CreateVms()
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T2938_invalid_image_id(self):
        try:
            self.a1_r1.oapi.CreateVms(ImageId='tata')
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.CreateVms(ImageId='vpc-12345678')
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')

    def test_T2939_unknown_image_id(self):
        try:
            self.a1_r1.oapi.CreateVms(ImageId='ami-12345678')
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5023')
        try:
            self.a1_r1.oapi.CreateVms(ImageId='aki-12345678')
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5023')
        try:
            self.a1_r1.oapi.CreateVms(ImageId='ari-12345678')
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5023')

    def test_T2940_malformed_image_id(self):
        try:
            self.a1_r1.oapi.CreateVms(ImageId='ami-123456')
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4105')

    def test_T3160_invalid_parameter_combination(self):
        try:
            self.a1_r1.oapi.CreateVms(ImageId='ami-12345678', SubnetId='subnet-12345678',
                                      Nics=[{'NicId': 'eni-12345678'}])
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')
        try:
            self.a1_r1.oapi.CreateVms(ImageId='ami-12345678', SecurityGroupIds=['sg-12345678'],
                                      Nics=[{'NicId': 'eni-12345678'}])
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')

    def test_T2029_no_param(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None)
        assert len(self.info) == 1
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm={
                'Architecture': 'x86_64',
                'BlockDeviceMappings': None,
                'BsuOptimized': False,
                'DeletionProtection': False,
                'Hypervisor': 'xen',
                'ImageId': self.a1_r1.config.region.get_info(constants.CENTOS7),
                'IsSourceDestChecked': True,
                'LaunchNumber': 0,
                'Performance': 'medium',
                'Placement': None,
                'ProductCodes': None,
                'ReservationId': None,
                'RootDeviceName': '/dev/sda1',
                'RootDeviceType': 'ebs',
                'State': 'pending',
                'StateReason': None,
                'UserData': None,
                'VmId': None,
                'VmInitiatedShutdownBehavior': None,
                'VmType': 't2.small'
            },
            placement={
                'Tenancy': 'default',
                'SubregionName': self.a1_r1.config.region.get_info(constants.ZONE)[0],
            },
            bdm=[{
                'DeviceName': 'default',
                'Bsu': {
                    'DeleteOnVmDeletion': True,
                    'State': 'attaching',
                    'VolumeId': 'vol-',
                },
            }]
        )
        # assert len(ret.response.Vms[0].SecurityGroups) == 1
        # assert ret.response.Vms[0].LaunchNumber == 0 (not working for the moment)
        # assert len(ret.response.Vms[0].Nics) == 0
        assert len(ret.response.Vms[0].ProductCodes) == 1

    def test_T2041_two_vms(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, MaxVmsCount=2, MinVmsCount=2)
        assert len(self.info) == 2
        for inst in ret.response.Vms:
            validate_vm_response(
                inst,
                expected_vm={
                    'Architecture': 'x86_64',
                    'BsuOptimized': False,
                    'Hypervisor': 'xen',
                    'ImageId': self.a1_r1.config.region.get_info(constants.CENTOS7),
                    'IsSourceDestChecked': True,
                    'RootDeviceName': '/dev/sda1',
                    'RootDeviceType': 'ebs',
                    'State': 'pending',
                },
                placement={
                    'Tenancy': 'default',
                    'SubregionName': self.a1_r1.config.region.get_info(constants.ZONE)[0],
                },
                bdm=[{
                    'DeviceName': 'default',
                    'Bsu': {
                        'DeleteOnVmDeletion': True,
                        'State': 'attaching',
                        'VolumeId': 'vol-',
                    },
                }]
            )

    def test_T2033_with_vm_type(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, VmType='t2.small')
        validate_vm_response(ret.response.Vms[0], expected_vm={'VmType': 't2.small'})

    def test_T2034_with_bsu_optimized(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, BsuOptimized=True, VmType='c4.large')
        validate_vm_response(ret.response.Vms[0], expected_vm={'VmType': 'c4.large', 'BsuOptimized': True})

    def test_T2035_without_instance_shutdown_behavior(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None)
        validate_vm_response(ret.response.Vms[0], expected_vm={'VmInitiatedShutdownBehavior': 'stop'})
        assert len(self.info) == 1
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceInitiatedShutdownBehavior', InstanceId=self.info[0])
        assert ret.response.instanceInitiatedShutdownBehavior.value == 'stop'

    def test_T2036_with_instance_shutdown_behavior_stop(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, VmInitiatedShutdownBehavior='stop')
        validate_vm_response(ret.response.Vms[0], expected_vm={'VmInitiatedShutdownBehavior': 'stop'})
        assert len(self.info) == 1
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceInitiatedShutdownBehavior', InstanceId=self.info[0])
        assert ret.response.instanceInitiatedShutdownBehavior.value == 'stop'

    def test_T2037_with_instance_shutdown_behavior_terminate(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, VmInitiatedShutdownBehavior='terminate')
        validate_vm_response(ret.response.Vms[0], xpected_vm={'VmInitiatedShutdownBehavior': 'terminate'})
        assert len(self.info) == 1
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceInitiatedShutdownBehavior', InstanceId=self.info[0])
        assert ret.response.instanceInitiatedShutdownBehavior.value == 'terminate'

    def test_T2038_with_instance_shutdown_behavior_restart(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, VmInitiatedShutdownBehavior='restart')
        validate_vm_response(ret.response.Vms[0], expected_vm={'VmInitiatedShutdownBehavior': 'restart'})
        assert len(self.info) == 1
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceInitiatedShutdownBehavior', InstanceId=self.info[0])
        assert ret.response.instanceInitiatedShutdownBehavior.value == 'restart'

    def test_T2039_with_instance_shutdown_behavior_invalid(self):
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, VmInitiatedShutdownBehavior='shutdown')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2040_with_userdata_private_only(self):
        userdata = """-----BEGIN OUTSCALE SECTION-----
            private_only=true
            -----END OUTSCALE SECTION-----"""
        ret, self.info = create_vms(ocs_sdk=self.a1_r1,
                                    UserData=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'))
        validate_vm_response(ret.response.Vms[0],
                             expected_vm={'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8')})

    def test_T3161_with_invalid_userdata(self):
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1,
                                      UserData='abc')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T3162_with_userdata_script_powershell(self):
        userdata = """# autoexecutepowershellnopasswd
            Write-Host 'Hello, World!'
            # autoexecutepowershellnopasswd"""
        ret, self.info = create_vms(ocs_sdk=self.a1_r1,
                                    UserData=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'))
        validate_vm_response(ret.response.Vms[0],
                             expected_vm={'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8')})

    def test_T3163_with_userdata_attract_server(self):
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_server=front80
            -----END OUTSCALE SECTION-----"""
        ret, self.info = create_vms(ocs_sdk=self.a1_r1,
                                    UserData=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'))
        validate_vm_response(ret.response.Vms[0],
                             expected_vm={'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8')})

    def test_T3164_with_userdata_auto_attach(self):
        public_ip = None
        try:
            public_ip = self.a1_r1.oapi.CreatePublicIp().response.PublicIp.PublicIp
            userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.eip.auto-attach={}
            -----END OUTSCALE SECTION-----""".format(public_ip)
            ret, self.info = create_vms(ocs_sdk=self.a1_r1,
                                        UserData=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'))
            validate_vm_response(ret.response.Vms[0],
                                 expected_vm={'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8')})
            ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [ret.response.Vms[0].VmId]})
            validate_vm_response(ret.response.Vms[0],
                                 expected_vm={'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8'),
                                              'PublicIp': public_ip})
        finally:
            if public_ip:
                self.a1_r1.oapi.DeletePublicIp(PublicIp=public_ip)

    def test_T3165_with_nic_missing_device_number(self):
        # missing device_number
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'NicId': 'eni-12345678'}])
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T3166_with_nic_invalid_nic_id(self):
        # invalid id
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'NicId': 'abc-12345678'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')
        # malformed id
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'NicId': 'eni-1234567'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4105')
        # unknown id
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'NicId': 'eni-12345678'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5036')

    def test_T3167_with_nic_invalid_subnet_id(self):
        # invalid id
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'SubnetId': 'abc-12345678'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')
        # malformed id
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'SubnetId': 'subnet-1234567'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4105')
        # unknown id
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'SubnetId': 'subnet-12345678'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5057')

    def test_T3168_with_nic_invalid_parameter_combination(self):
        # provide nic id and subnet id
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'NicId': 'eni-12345678',
                                                                 'SubnetId': 'subnet-12345678'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')
        # provide nic id and security_group_ids
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'NicId': 'eni-12345678',
                                                                 'SecurityGroupIds': ['sg-12345678']}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')
        # provide nic id and private_ips
        try:
            _, self.info = create_vms(
                ocs_sdk=self.a1_r1,
                Nics=[{
                    'DeviceNumber': 1,
                    'NicId': 'eni-12345678',
                    'PrivateIps': [{
                        'IsPrimary': True,
                        'PrivateIp': '120.1.2.3'}]
                }]
            )
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')
        # provide nic id and secondary_ip_count
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'NicId': 'eni-12345678',
                                                                 'SecondaryPrivateIpCount': 50}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')
        # provide nic id and delete_on_vm_deletion to True
        try:
            _, self.info = create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'NicId': 'eni-12345678',
                                                                 'DeleteOnVmDeletion': True}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')
        # too much primary ips
        try:
            _, self.info = create_vms(
                ocs_sdk=self.a1_r1,
                Nics=[{
                    'DeviceNumber': 1,
                    'SubnetId': 'subnet-12345678',
                    'PrivateIps': [
                        {
                            'IsPrimary': True,
                            'PrivateIp': '120.1.2.3'
                        },
                        {
                            'IsPrimary': True,
                            'PrivateIp': '120.1.2.3'
                        }
                    ]
                }]
            )
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3002')

    def test_T3169_with_nic_invalid_ips(self):
        # private ips not ipv4
        try:
            _, self.info = create_vms(
                ocs_sdk=self.a1_r1,
                Nics=[{
                    'DeviceNumber': 1,
                    'SubnetId': 'subnet-12345678',
                    'PrivateIps': [{
                        'IsPrimary': True,
                        'PrivateIp': 'hello_ips'}]
                }]
            )
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4047')
        # private ips not ipv4
        try:
            _, self.info = create_vms(
                ocs_sdk=self.a1_r1,
                Nics=[{
                    'DeviceNumber': 1,
                    'SubnetId': 'subnet-12345678',
                    'PrivateIps': [{
                        'IsPrimary': True,
                        'PrivateIp': '120.1.2.3.5'}]
                }]
            )
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4047')
        # private ips not ipv4
        try:
            _, self.info = create_vms(
                ocs_sdk=self.a1_r1,
                Nics=[{
                    'DeviceNumber': 1,
                    'SubnetId': 'subnet-12345678',
                    'PrivateIps': [{
                        'IsPrimary': True,
                        'PrivateIp': '120.1.2.3000'}]
                }]
            )
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4047')

    def test_T3398_with_bdm(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, BlockDeviceMappings=[{'DeviceName': '/dev/sdb', 'Bsu': {'VolumeSize': 2}}])
        assert len(self.info) == 1
        for inst in ret.response.Vms:
            validate_vm_response(
                inst,
                bdm=[{
                    'DeviceName': '/dev/sda',
                    'Bsu': {
                        'DeleteOnVmDeletion': True,
                        'State': 'attaching',
                        'VolumeId': 'vol-',
                    },
                },
                    {
                    'DeviceName': '/dev/sdb',
                    'Bsu': {
                        'DeleteOnVmDeletion': True,
                        'State': 'attaching',
                        'VolumeId': 'vol-',
                    },
                }]
            )

    def test_T3399_with_bdm_with_volume_type_gp2(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1,
                                    BlockDeviceMappings=[{'DeviceName': '/dev/sdb', 'Bsu': {'VolumeSize': 2, 'VolumeType': 'gp2'}}])
        assert len(self.info) == 1
        for inst in ret.response.Vms:
            validate_vm_response(
                inst,
                bdm=[{
                    'DeviceName': '/dev/sdb',
                    'Bsu': {
                        'DeleteOnVmDeletion': True,
                        'State': 'attaching',
                        'VolumeId': 'vol-',
                    },
                }]
            )

    def test_T3400_with_bdm_with_volume_type_io1(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1,
                                    BlockDeviceMappings=[{'DeviceName': '/dev/sdb', 'Bsu': {'Iops': 100, 'VolumeSize': 4, 'VolumeType': 'io1'}}])
        assert len(self.info) == 1
        for inst in ret.response.Vms:
            validate_vm_response(
                inst,
                bdm=[{
                    'DeviceName': '/dev/sdb',
                    'Bsu': {
                        'DeleteOnVmDeletion': True,
                        'State': 'attaching',
                        'VolumeId': 'vol-',
                    },
                }]
            )

    def test_T5120_with_bdm_with_empty_volume_type(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, BlockDeviceMappings=[{'DeviceName': '/dev/sdb', 'Bsu': {'VolumeSize': 4, 'VolumeType': ''}}])
        assert len(self.info) == 1

        for inst in ret.response.Vms:
            validate_vm_response(
                inst,
                bdm=[{
                    'DeviceName': '/dev/sdb',
                    'Bsu': {
                        'DeleteOnVmDeletion': True,
                        'State': 'attaching',
                        'VolumeId': 'vol-',
                    },
                }]
            )

        ret_volumes = self.a1_r1.oapi.ReadVolumes(
            Filters={'VolumeIds': [bdm.Bsu.VolumeId for bdm in ret.response.Vms[0].BlockDeviceMappings]})
        found = False
        for vol in ret_volumes.response.Volumes:
            if vol.LinkedVolumes and len(vol.LinkedVolumes) == 1 and vol.LinkedVolumes[0].DeviceName == '/dev/sdb' and vol.VolumeType == 'standard':
                found = True
                break
        assert found, 'Could not find the attached volume'

    def test_T4157_vm_as_stopped(self):
        ret, self.info = create_vms(ocs_sdk=self.a1_r1, state=None, BootOnCreation=False)
        validate_vm_response(ret.response.Vms[0], expected_vm={'VmInitiatedShutdownBehavior': 'stop'})
        assert len(self.info) == 1
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceInitiatedShutdownBehavior', InstanceId=self.info[0])
        assert ret.response.instanceInitiatedShutdownBehavior.value == 'stop'
        wait_instances_state(self.a1_r1, self.info, state='stopped')
        self.a1_r1.oapi.StopVms(VmIds=self.info, ForceStop=True)
        self.a1_r1.oapi.DeleteVms(VmIds=self.info)
        wait_instances_state(self.a1_r1, self.info, state='terminated')
        self.info = None

    def test_T5072_userdata_base64_gzip(self):
        vm_info = None
        user_data = base64.b64encode(zlib.compress(self.user_data.encode('utf-8'))).decode('utf-8')
        try:
            vm_info = create_Vms(osc_sdk=self.a1_r1, state='ready',
                                         user_data=user_data)
            self.check_user_data(vm_info, gzip=True, decode=False)
        finally:
            if vm_info:
                delete_Vms(self.a1_r1, vm_info)


class Test_CreateVmsWithSubnet(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateVmsWithSubnet, cls).setup_class()
        cls.net_id = None
        cls.subnet_id = None
        cls.nic_id = None
        cls.vm_id_list = None
        cls.sg_id = None
        try:
            cls.net_id = cls.a1_r1.oapi.CreateNet(IpRange='10.1.0.0/16').response.Net.NetId
            cls.subnet_id = cls.a1_r1.oapi.CreateSubnet(NetId=cls.net_id, IpRange='10.1.0.0/24').response.Subnet.SubnetId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.subnet_id:
                cls.a1_r1.fcu.DeleteSubnet(SubnetId=cls.subnet_id)
            if cls.net_id:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.net_id)
        finally:
            super(Test_CreateVmsWithSubnet, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateVmsWithSubnet, self).setup_method(method)
        self.nic_id = None
        self.vm_id_list = None
        self.sg_id = None

    def teardown_method(self, method):
        try:
            if self.vm_id_list:
                self.a1_r1.oapi.StopVms(VmIds=self.vm_id_list, ForceStop=True)
                self.a1_r1.oapi.DeleteVms(VmIds=self.vm_id_list)
                wait_instances_state(self.a1_r1, self.vm_id_list, state='terminated')
            if self.sg_id:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=self.sg_id)
                wait_security_groups_state(self.a1_r1, [self.sg_id], cleanup=True)
            if self.nic_id:
                self.a1_r1.oapi.DeleteNic(NicId=self.nic_id)
                wait_network_interfaces_state(self.a1_r1, [self.nic_id], cleanup=True)
        finally:
            super(Test_CreateVmsWithSubnet, self).teardown_method(method)

    def test_T2031_with_subnet_id(self):
        ret, self.vm_id_list = create_vms(ocs_sdk=self.a1_r1, state='running', SubnetId=self.subnet_id)
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm={
                'ImageId': self.a1_r1.config.region.get_info(constants.CENTOS7),
                'PrivateDnsName': '.compute',
            },
            placement={
                'Tenancy': 'default',
                'SubregionName': self.a1_r1.config.region.get_info(constants.ZONE)[0],
            },
            nic=[{
                'LinkNic': {
                    'DeviceNumber': 0,
                },
                'SubnetId': self.subnet_id,
                'NetId': self.net_id,
            }],
        )

    def test_T2032_with_subnet_id_private_ips(self):
        ret, self.vm_id_list = create_vms(ocs_sdk=self.a1_r1, state='running', SubnetId=self.subnet_id,
                                          PrivateIps=['10.1.0.4'])
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm={
                'PrivateDnsName': '.compute',
                'PrivateIp': '10.1.0.4',
            },
            placement={
                'Tenancy': 'default',
                'SubregionName': self.a1_r1.config.region.get_info(constants.ZONE)[0],
            },
            nic=[{
                'LinkNic': {
                    'DeviceNumber': 0,
                },
                'SubnetId': self.subnet_id,
                'NetId': self.net_id,
            }],
        )
        assert len(ret.response.Vms[0].Nics) == 1
        assert len(ret.response.Vms[0].Nics[0].PrivateIps) == 1

    def test_T3170_with_nic_invalid_sg_id(self):
        # invalid id
        try:
            create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'SubnetId': self.subnet_id, 'SecurityGroupIds': ['tata-12345678']}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')
        # malformed id
        try:
            create_vms(ocs_sdk=self.a1_r1, Nics=[{'DeviceNumber': 1, 'SubnetId': self.subnet_id, 'SecurityGroupIds': ['sg-1234567']}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4105')

    def test_T3171_with_nic_valid_nic_id(self):
        self.nic_id = self.a1_r1.oapi.CreateNic(SubnetId=self.subnet_id).response.Nic.NicId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            Nics=[{'DeviceNumber': 0, 'NicId': self.nic_id}]
        )
        validate_vm_response(
            ret.response.Vms[0],
            nic=[{
                'LinkNic': {
                    'DeviceNumber': 0,
                },
                'NicId': self.nic_id,
            }],
        )

    def test_T4401_with_two_valid_nic_id(self):
        nic_id2 = None
        subnet_id2 = None
        try:
            subnet_id2 = self.a1_r1.oapi.CreateSubnet(NetId=self.net_id,
                                                      IpRange='10.1.1.0/24').response.Subnet.SubnetId
            self.nic_id = self.a1_r1.oapi.CreateNic(SubnetId=self.subnet_id).response.Nic.NicId
            nic_id2 = self.a1_r1.oapi.CreateNic(SubnetId=subnet_id2).response.Nic.NicId
            ret, self.vm_id_list = create_vms(
                ocs_sdk=self.a1_r1, VmType='tinav4.c2r4p1',
                Nics=[{'DeviceNumber': 0, 'NicId': self.nic_id}, {'DeviceNumber': 1, 'NicId': nic_id2}]
            )
            validate_vm_response(
                ret.response.Vms[0],
                nic=[{
                    'LinkNic': {
                        'DeviceNumber': 0,
                    },
                    'NicId': self.nic_id,
                }, {
                    'LinkNic': {
                        'DeviceNumber': 1,
                    },
                    'NicId': nic_id2,
                }],
            )
        finally:
            if nic_id2:
                self.a1_r1.oapi.UnlinkNic(LinkNicId=ret.response.Vms[0].Nics[1].LinkNic.LinkNicId)
                wait_network_interfaces_state(osc_sdk=self.a1_r1, network_interface_id_list=[nic_id2], state='available')
                self.a1_r1.oapi.DeleteNic(NicId=nic_id2)
            if subnet_id2:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id2)

    def test_T4402_with_incorrect_device_number(self):
        nic_id1 = None
        subnet_id1 = None
        try:
            self.nic_id = self.a1_r1.oapi.CreateNic(SubnetId=self.subnet_id).response.Nic.NicId

            subnet_id1 = self.a1_r1.oapi.CreateSubnet(NetId=self.net_id,
                                                      IpRange='10.1.1.0/24').response.Subnet.SubnetId
            nic_id1 = self.a1_r1.oapi.CreateNic(SubnetId=subnet_id1).response.Nic.NicId

            try:
                _, self.vm_id_list = create_vms(
                    ocs_sdk=self.a1_r1,
                    Nics=[{'DeviceNumber': 0, 'NicId': self.nic_id}, {'DeviceNumber': 8, 'NicId': nic_id1}])
                assert False, 'Call should not have been successful'
            except OscApiException as err:
                assert_oapi_error(err, 400, 'InvalidParameterValue', '4047')

        finally:
            if nic_id1:
                self.a1_r1.oapi.DeleteNic(NicId=nic_id1)
            if subnet_id1:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id1)

    def test_T3172_with_nic_valid_subnet_id(self):
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            Nics=[{'DeviceNumber': 0, 'SubnetId': self.subnet_id}]
        )
        validate_vm_response(
            ret.response.Vms[0],
            nic=[{
                'LinkNic': {
                    'DeviceNumber': 0,
                },
                'SubnetId': self.subnet_id,
                'NetId': self.net_id,
            }],
        )

    def test_T3173_with_nic_with_sg_ids(self):
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=id_generator(size=7, chars=string.ascii_lowercase),
            Description='test', NetId=self.net_id).response.SecurityGroup.SecurityGroupId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            Nics=[
                {
                    'DeviceNumber': 0,
                    'SubnetId': self.subnet_id, 'SecurityGroupIds': [self.sg_id],
                }
            ]
        )
        validate_vm_response(
            ret.response.Vms[0],
            nic=[{
                'LinkNic': {
                    'DeviceNumber': 0,
                },
                'SubnetId': self.subnet_id,
                'NetId': self.net_id,
            }],
            sgs=[{'SecurityGroupId': self.sg_id}]
        )

    def test_T3174_with_nic_with_sg_id_in_another_vpc(self):
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=id_generator(size=7, chars=string.ascii_lowercase),
            Description='test').response.SecurityGroup.SecurityGroupId
        try:
            _, self.vm_id_list = create_vms(
                ocs_sdk=self.a1_r1,
                Nics=[
                    {
                        'DeviceNumber': 0,
                        'SubnetId': self.subnet_id,
                        'SecurityGroupIds': [self.sg_id]
                    }
                ]
            )
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5022')

    def test_T3175_with_nic_valid_subnet_id_with_1_private_ip(self):
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            Nics=[{'DeviceNumber': 0, 'SubnetId': self.subnet_id,
                   'PrivateIps': [{
                       'IsPrimary': True,
                       'PrivateIp': '10.1.0.50'}]}]
        )
        validate_vm_response(
            ret.response.Vms[0],
            nic=[{
                'LinkNic': {
                    'DeviceNumber': 0,
                },
                'SubnetId': self.subnet_id,
                'NetId': self.net_id,
                'PrivateIps': [{
                    'IsPrimary': True,
                    'PrivateIp': '10.1.0.50'}],
            }],
        )

    def test_T3558_with_nic_valid_subnet_id_with_more_private_ips(self):
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            Nics=[{'DeviceNumber': 0, 'SubnetId': self.subnet_id,
                   'PrivateIps': [
                       {
                           'IsPrimary': True,
                           'PrivateIp': '10.1.0.50'
                       },
                       {
                           'IsPrimary': False,
                           'PrivateIp': '10.1.0.51'
                       }]
                   }]
        )
        validate_vm_response(
            ret.response.Vms[0],
            nic=[{
                'LinkNic': {
                    'DeviceNumber': 0,
                },
                'SubnetId': self.subnet_id,
                'NetId': self.net_id,
                'PrivateIps': [
                    {
                        'IsPrimary': True,
                        'PrivateIp': '10.1.0.50'
                    },
                    {
                        'IsPrimary': False,
                        'PrivateIp': '10.1.0.51'
                    }],
            }],
        )

    def test_T3176_with_nic_valid_subnet_id_with_1_private_ip_and_secondary(self):
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            Nics=[{
                'DeviceNumber': 0, 'SubnetId': self.subnet_id,
                'PrivateIps': [
                    {
                        'IsPrimary': True,
                        'PrivateIp': '10.1.0.50'
                    }],
                'SecondaryPrivateIpCount': 1,
            }]
        )
        validate_vm_response(
            ret.response.Vms[0],
        )

    def test_T3177_with_multiple_nic_valid_subnet_id_with_1_private_ip(self):
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            Nics=[
                {
                    'DeviceNumber': 0, 'SubnetId': self.subnet_id,
                    'PrivateIps': [
                        {
                            'IsPrimary': True,
                            'PrivateIp': '10.1.0.50'
                        }
                    ],
                },
                {
                    'DeviceNumber': 1, 'SubnetId': self.subnet_id,
                    'PrivateIps': [
                        {
                            'IsPrimary': True,
                            'PrivateIp': '10.1.0.51'
                        }
                    ],
                }]
        )
        validate_vm_response(
            ret.response.Vms[0],
            nic=[
                {
                    'LinkNic': {
                        'DeviceNumber': 0,
                    }, 'SubnetId': self.subnet_id,
                    'PrivateIps': [
                        {
                            'IsPrimary': True,
                            'PrivateIp': '10.1.0.50'
                        }
                    ],
                },
                {
                    'LinkNic': {
                        'DeviceNumber': 1,
                    },
                    'SubnetId': self.subnet_id,
                    'PrivateIps': [
                        {
                            'IsPrimary': True,
                            'PrivateIp': '10.1.0.51'
                        }
                    ],
                }],
        )

    def test_T3178_with_subnet_and_sg_ids(self):
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=id_generator(size=7, chars=string.ascii_lowercase),
            Description='test', NetId=self.net_id).response.SecurityGroup.SecurityGroupId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            SubnetId=self.subnet_id,
            SecurityGroupIds=[self.sg_id],
        )
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm={
                'SubnetId': self.subnet_id,
            },
            sgs=[{'SecurityGroupId': self.sg_id}]
        )

    def test_T3179_with_sg_ids_in_specific_vpc(self):
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=id_generator(size=7, chars=string.ascii_lowercase),
            Description='test', NetId=self.net_id).response.SecurityGroup.SecurityGroupId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            SubnetId=self.subnet_id,
            SecurityGroupIds=[self.sg_id],
        )
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm={
                'SubnetId': self.subnet_id,
            },
            sgs=[{'SecurityGroupId': self.sg_id}]
        )

    def test_T3180_with_sg_id(self):
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=id_generator(size=7, chars=string.ascii_lowercase),
            Description='test').response.SecurityGroup.SecurityGroupId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            SecurityGroupIds=[self.sg_id],
        )
        validate_vm_response(
            ret.response.Vms[0],
            sgs=[{'SecurityGroupId': self.sg_id}]
        )

    def test_T3181_with_subnet_and_sg_names(self):
        name = id_generator(size=7, chars=string.ascii_lowercase)
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=name,
            Description='test', NetId=self.net_id).response.SecurityGroup.SecurityGroupId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            SubnetId=self.subnet_id,
            SecurityGroups=[name],
        )
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm={
                'SubnetId': self.subnet_id,
            },
            sgs=[{'SecurityGroupId': self.sg_id, 'SecurityGroupName': name}]
        )

    def test_T3182_with_sg_names_in_specific_vpc(self):
        name = id_generator(size=7, chars=string.ascii_lowercase)
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=name,
            Description='test', NetId=self.net_id).response.SecurityGroup.SecurityGroupId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            SubnetId=self.subnet_id,
            SecurityGroups=[name],
        )
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm={
                'SubnetId': self.subnet_id,
            },
            sgs=[{'SecurityGroupId': self.sg_id, 'SecurityGroupName': name}]
        )

    def test_T3183_with_sg_names(self):
        name = id_generator(size=7, chars=string.ascii_lowercase)
        self.sg_id = self.a1_r1.oapi.CreateSecurityGroup(
            SecurityGroupName=name,
            Description='test').response.SecurityGroup.SecurityGroupId
        ret, self.vm_id_list = create_vms(
            ocs_sdk=self.a1_r1,
            SecurityGroups=[name],
        )
        validate_vm_response(
            ret.response.Vms[0],
            sgs=[{'SecurityGroupId': self.sg_id, 'SecurityGroupName': name}]
        )

    def test_T4574_with_large_userdata(self):
        msg = id_generator(size=15000, chars=string.ascii_lowercase)
        userdata = """# autoexecutepowershellnopasswd
            Write-Host '{}'
            # autoexecutepowershellnopasswd""".format(msg)
        ret, _ = create_vms(ocs_sdk=self.a1_r1, UserData=base64.b64encode(userdata.encode('utf-8')).decode('utf-8'))
        validate_vm_response(ret.response.Vms[0], expected_vm={'UserData': base64.b64encode(userdata.encode('utf-8')).decode('utf-8')})
