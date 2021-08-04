
import os
import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.compare_objects import verify_response, create_hints
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi
from qa_tina_tools.tina.oapi import info_keys

class Test_ReadVms(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.vm_info = None
        super(Test_ReadVms, cls).setup_class()
        try:
            cls.vm_info = oapi.create_Vms(cls.a1_r1, nb=3)
            hints = []
            hints.append(cls.a1_r1.config.region.name)
            hints.append(cls.a1_r1.config.region.az_name)
            hints.append(cls.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE))
            hints.append(cls.a1_r1.config.region.get_info(constants.CENTOS_LATEST))
            for vm_info in cls.vm_info[info_keys.VMS]:
                hints.append(vm_info["VmId"])
                for sg_info in vm_info["SecurityGroups"]:
                    hints.append(sg_info["SecurityGroupId"])
                    hints.append(sg_info["SecurityGroupName"])
                for bdm_info in vm_info["BlockDeviceMappings"]:
                    hints.append(bdm_info["Bsu"]["VolumeId"])
                hints.append(str(vm_info["LaunchNumber"]))
                hints.append(vm_info["ReservationId"])
                hints.append(vm_info["PrivateDnsName"])
                hints.append(vm_info["PrivateIp"])
                hints.append(vm_info["PublicDnsName"])
                hints.append(vm_info["PublicIp"])
                hints.append(vm_info["KeypairName"])
                hints.append(vm_info["CreationDate"])
            cls.hints = create_hints(hints)

        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vm_info:
                oapi.delete_Vms(cls.a1_r1, cls.vm_info)
        finally:
            super(Test_ReadVms, cls).teardown_class()

    def test_T3423_dry_run(self):
        ret = self.a1_r1.oapi.ReadVms(DryRun=True)
        assert_dry_run(ret)

    def test_T2070_without_filters(self):
        vms = self.a1_r1.oapi.ReadVms().response.Vms
        assert len(vms) == len(self.vm_info[info_keys.VMS])

    def test_T2069_with_ids(self):
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': self.vm_info[info_keys.VM_IDS][0:1]})
        verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'readvms_with_ids.json'), self.hints)

    @pytest.mark.tag_sec_confidentiality
    def test_T3424_other_account(self):
        ret = self.a2_r1.oapi.ReadVms().response.Vms
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3425_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadVms(Filters={'VmIds': self.vm_info[info_keys.VM_IDS]}).response.Vms
        assert not ret

    def test_T4390_with_tagged_vm(self):
        self.a1_r1.oapi.CreateTags(ResourceIds=[self.vm_info[info_keys.VM_IDS][1]], Tags=[{'Key': 'key', 'Value': 'value'}])
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_info[info_keys.VM_IDS][1]]})
        assert hasattr(ret.response.Vms[0], 'Tags')

    def test_T5075_with_state_filter(self):
        try:
            self.a1_r1.oapi.ReadVms(Filters={"VmStates": ['running']})
            assert False, 'call should not have been successful'
        except OscApiException as err:
            misc.assert_oapi_error(err, 400, 'InvalidParameter', '3001')
