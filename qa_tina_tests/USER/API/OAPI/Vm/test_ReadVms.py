
import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tests.USER.API.OAPI.Vm.Vm import create_vms
from qa_tina_tests.USER.API.OAPI.Vm.Vm import validate_vm_response


class Test_ReadVms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadVms, cls).setup_class()
        try:
            _, cls.vm_ids = create_vms(cls.a1_r1, MaxVmsCount=3, MinVmsCount=3)
            cls.info = None
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vm_ids:
                cls.a1_r1.fcu.StopInstances(InstanceId=cls.vm_ids, Force=True)
                cls.a1_r1.fcu.TerminateInstances(InstanceId=cls.vm_ids)
        finally:
            super(Test_ReadVms, cls).teardown_class()

    def test_T3423_dry_run(self):
        ret = self.a1_r1.oapi.ReadVms(DryRun=True)
        assert_dry_run(ret)

    def test_T2070_without_filters(self):
        vms = self.a1_r1.oapi.ReadVms().response.Vms
        assert len(vms) == len(self.vm_ids)

    def test_T2069_with_ids(self):
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': self.vm_ids[0:1]})
        assert len(ret.response.Vms) == 1
        validate_vm_response(
            ret.response.Vms[0],
            expected_vm=
            {
                'Architecture': 'x86_64',
                'BlockDeviceMappings': None,
                'BsuOptimized': False,
                'DeletionProtection': False,
                'Hypervisor': 'xen',
                'ImageId': self.a1_r1.config.region.get_info(constants.CENTOS7),
                'IsSourceDestChecked': True,
                'LaunchNumber': 0,
                'Placement': None,
                'ProductCodes': None,
                'ReservationId': None,
                'RootDeviceName': '/dev/sda1',
                'RootDeviceType': 'ebs',
                'State': 'running',
                'StateReason': None,
                'UserData': None,
                'VmId': self.vm_ids[0],
                'VmInitiatedShutdownBehavior': 'stop',
                'VmType': 't2.small'
            },
            placement=
            {
                'Tenancy': 'default',
                'SubregionName': self.a1_r1.config.region.get_info(constants.ZONE)[0],
            },
            bdm=
            [{
                'DeviceName': 'default',
                'Bsu': {
                    'DeleteOnVmDeletion': True,
                    'State': 'attached',
                    'VolumeId': 'vol-',
                },
            }]
        )
        assert len(ret.response.Vms[0].SecurityGroups) == 1
        # assert ret.response.Vms[0].LaunchNumber == 0 (not working for the moment)
        # assert len(ret.response.Vms[0].Nics) == 0
        # assert ret.response.Vms[0].PrivateIp != ''
        assert len(ret.response.Vms[0].ProductCodes) == 1
        # assert '.in-west-2.compute.outscale.com' in ret.response.Vms[0].PublicDnsName # TODO: valid only on in.
        # assert ret.response.Vms[0].PublicIp != ''
        # assert len(ret.response.Vms[0].SecurityGroups) == 1
        # assert ret.response.Vms[0].VmType == 't2.small' # TODO : is it different in 'in' and 'dv'(m1.small) ?
        assert not hasattr(ret.response.Vms[0], 'Nics')
        # assert len(ret.response.Vms[0].Nics) == 1

    @pytest.mark.tag_sec_confidentiality
    def test_T3424_other_account(self):
        ret = self.a2_r1.oapi.ReadVms().response.Vms
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3425_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadVms(Filters={'VmIds': self.vm_ids}).response.Vms
        assert not ret

    def test_T4390_with_tagged_vm(self):
        self.a1_r1.oapi.CreateTags(ResourceIds=[self.vm_ids[1]], Tags=[{'Key': 'key', 'Value': 'value'}])
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_ids[1]]})
        assert hasattr(ret.response.Vms[0], 'Tags')

    def test_T5075_with_state_filter(self):
        try:
            self.a1_r1.oapi.ReadVms(Filters={"VmStates": ['running']})
            assert False, 'call should not have been successful'
        except OscApiException as err:
            misc.assert_oapi_error(err, 400, 'InvalidParameter', '3001')
