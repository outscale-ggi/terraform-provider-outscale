import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi, info_keys, wait


# @tx_export(isolation_level='SERIALIZABLE')
# @outscale.check.arg('delete_on_termination', types={bool})
# @outscale.check.arg('image_id', required=True, resource_ids={'aki-', 'ami-', 'ari-'})
# @outscale.check.arg('owner', required=True, types={str})
# @outscale.check.arg('size', types={int})
# @outscale.check.arg('snapshot_id', resource_ids={"snap-"})
# @outscale.check.arg('volume_type', choices=set(tina.intel.managed_volumes.MAPPING))
# @outscale.check.required_some_of(
#     "delete_on_termination", "size", "volume_type", count={(1, 3)}
# )
# def update_bdm(
#     session: TinaSession,
#     owner: str,
#     image_id: str,
#     snapshot_id: Optional[str] = None,
#     delete_on_termination: Optional[bool] = None,
#     iops: int = None,
#     size: Optional[int] = None,
#     volume_type: Optional[str] = None,
# ) -> model.Image:
#     """Update attributes in database for an image's block device mapping.
#
#     The func can update only images in state : available.
#
#     :param bool delete_on_termination: (optional) update this option in database.
#     :param str image_id: Image ID.
#     :param int iops: New IOPS value for the BDMs.
#     :param: str owner: Owner of the image.
#     :param int size: (optional) update size in database.
#     :param int snapshot_id: (optional) Snap ID if you want update just one image_bdm.
#     :param str volume_type: (optional) update volume type in database.
#
#     :rtype: Image
#     """


SIZE = 10
IOPS = 400


@pytest.mark.region_admin
class Test_update_image_bdm(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.bdm = None
        cls.vm_info = None
        cls.image_id = None
        cls.snapshot_id = None
        super(Test_update_image_bdm, cls).setup_class()
        try:
            cls.bdm = [{'DeviceName': '/dev/xvdb', 'Bsu': {'DeleteOnVmDeletion': True, 'VolumeSize': SIZE, 'VolumeType': 'standard'}},
                       {'DeviceName': '/dev/xvdc', 'Bsu': {'DeleteOnVmDeletion': True, 'VolumeSize': SIZE, 'VolumeType': 'io1', 'Iops': IOPS}},
                       {'DeviceName': '/dev/xvdd', 'Bsu': {'DeleteOnVmDeletion': True, 'VolumeSize': SIZE, 'VolumeType': 'gp2'}}
                       ]
            cls.vm_info = oapi.create_Vms(cls.a1_r1, nb=1, bdm=cls.bdm, state='stopped')
            #oapi.stop_Vms(cls.a1_r1, cls.vm_info[info_keys.VM_IDS], force=False)
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
            super(Test_update_image_bdm, cls).teardown_class()


    def setup_method(self, method):
        self.image_id = None
        self.snapshot_id = None
        OscTinaTest.setup_method(self, method)
        try:
            ret = self.a1_r1.oapi.CreateImage(VmId=self.vm_info[info_keys.VM_IDS][0], ImageName=misc.id_generator(prefix='omi_'), NoReboot=True)
            self.image_id = ret.response.Image.ImageId
            wait.wait_Images_state(osc_sdk=self.a1_r1, image_ids=[self.image_id], state='available')
            self.snapshot_id = ret.response.Image.BlockDeviceMappings[0].Bsu.SnapshotId
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.image_id:
                self.a1_r1.oapi.DeleteImage(ImageId=self.image_id)
        finally:
            OscTinaTest.teardown_method(self, method)

    def check_image(self, delete_on_vm_termination=True, vol_type=None, vol_size=SIZE, vol_io1_iops=None, snap_id=None):
        vm_info = None
        vol_list = []
        try:
            vm_info = oapi.create_Vms(self.a1_r1, omi_id=self.image_id)
            resp = self.a1_r1.oapi.ReadVms(Filters={'VmIds': vm_info[info_keys.VM_IDS]}).response
            self.logger.debug(resp.display())
            assert len(resp.Vms) == 1
            vol_list = [item.Bsu.VolumeId for item in resp.Vms[0].BlockDeviceMappings]
            for item in resp.Vms[0].BlockDeviceMappings:
                assert item.Bsu.DeleteOnVmDeletion == delete_on_vm_termination
                vol = self.a1_r1.oapi.ReadVolumes(Filters={'VolumeIds': [item.Bsu.VolumeId]}).response
                self.logger.debug(vol.display())
                assert len(vol.Volumes) == 1
                if not snap_id or vol.Volumes[0].SnapshotId == snap_id:
                    assert vol.Volumes[0].Size == vol_size
                    assert vol.Volumes[0].SnapshotId
                    if not vol_type:
                        if vol.Volumes[0].LinkedVolumes[0].DeviceName == '/dev/sda1':
                            assert vol.Volumes[0].VolumeType == 'standard'
                        else:
                            for bsu in self.bdm:
                                if bsu['DeviceName'] == vol.Volumes[0].LinkedVolumes[0].DeviceName:
                                    assert vol.Volumes[0].VolumeType == bsu['Bsu']['VolumeType']
                    else:
                        assert vol.Volumes[0].VolumeType == vol_type
                    if vol_io1_iops:
                        assert vol.Volumes[0].Iops == vol_io1_iops
                    else:
                        assert not hasattr(vol.Volumes[0], "Iops")
                else:
                    assert vol.Volumes[0].Size == SIZE
                    assert vol.Volumes[0].SnapshotId
                    if vol.Volumes[0].LinkedVolumes[0].DeviceName == '/dev/sda1':
                        assert vol.Volumes[0].VolumeType == 'standard'
                    else:
                        for bsu in self.bdm:
                            if bsu['DeviceName'] == vol.Volumes[0].LinkedVolumes[0].DeviceName:
                                assert vol.Volumes[0].VolumeType == bsu['Bsu']['VolumeType']
                    if vol.Volumes[0].VolumeType == 'io1':
                        assert vol.Volumes[0].Iops == IOPS
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if not delete_on_vm_termination:
                for vol in vol_list:
                    self.a1_r1.oapi.DeleteVolume(VolumeId=vol)
                    wait.wait_Volumes_state(self.a1_r1, [vol], cleanup=True)

    def test_T5926_modified_size(self):
        self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, size=(SIZE + 1) * 2**30)
        try:
            self.check_image(vol_size=SIZE + 1)
            assert False, 'Remove known error'
        except OscApiException:
            known_error('TINA-6700', 'Iops value is set to None after an intel.update_bdm')

    def test_T5927_modified_type_to_std(self):
        self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, volume_type="standard")
        self.check_image(vol_type="standard")

    def test_T5928_modified_type_to_io1(self):
        self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, volume_type='io1', iops=IOPS)
        self.check_image(vol_type="io1", vol_io1_iops=IOPS)

    def test_T5929_modified_delete_on_termination(self):
        self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, delete_on_termination=False)
        try:
            self.check_image(delete_on_vm_termination=False)
            assert False, 'Remove known error'
        except OscApiException:
            known_error('TINA-6700', 'Iops value is set to None after an intel.update_bdm')

    def test_T5930_modified_only_one_vol(self):
        self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, snapshot_id=self.snapshot_id,
                                          size=(SIZE + 1) * 2**30)
        self.check_image(vol_size=SIZE + 1, snap_id=self.snapshot_id)
