import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi, info_keys, wait
from qa_test_tools import misc


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
        super(Test_update_image_bdm, cls).setup_class()
        try:
            bdm = [{'DeviceName': '/dev/xvdb', 'Bsu': {'DeleteOnVmDeletion': True, 'VolumeSize': SIZE, 'VolumeType': 'standard'}},
                   {'DeviceName': '/dev/xvdc', 'Bsu': {'DeleteOnVmDeletion': True, 'VolumeSize': SIZE, 'VolumeType': 'io1', 'Iops': IOPS}},
                   {'DeviceName': '/dev/xvdd', 'Bsu': {'DeleteOnVmDeletion': True, 'VolumeSize': SIZE, 'VolumeType': 'gp2'}}]
            cls.vm_info = oapi.create_Vms(cls.a1_r1, nb=1, bdm=bdm, state='running')
            oapi.stop_Vms(cls.a1_r1, cls.vm_info[info_keys.VM_IDS], force=False)
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
        OscTinaTest.setup_method(self, method)
        try:
            ret = self.a1_r1.oapi.CreateImage(VmId=self.vm_info[info_keys.VM_IDS][0], ImageName=misc.id_generator(prefix='omi_'), NoReboot=True)
            self.image_id = ret.response.Image.ImageId
            wait.wait_Images_state(osc_sdk=self.a1_r1, image_ids=[self.image_id], state='available')
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

    def check_image(self):
        vm_info = None
        try:
            vm_info = oapi.create_Vms(self.a1_r1, omi_id=self.image_id)
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)

    def test_T0000_without_params(self):
        try:
            # self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id)
            self.a1_r1.intel.image.update_bdm()
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 200, 0, 'missing-parameter - Parameter cannot be empty: ImageID')

    def test_T0000_with_size(self):
        # SIZE en bytes
        new_size = (SIZE + 5)*10**9
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, size=new_size)
        for _ in ret.response.result.mapping:
            assert _.size == new_size
            if _.volume_type == 'io1':
                if _.iops != IOPS:
                    known_error('TINA-6700', 'Iops value is set to None after an intel.update_bdm')
                assert False, 'Remove known error'
                assert _.iops == IOPS
            # self.check_image()

    def test_T000_with_vol_type_io1(self):
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, volume_type='io1', iops=IOPS+100)
        to_bytes = 1073741824
        for _ in ret.response.result.mapping:
            assert _.volume_type == 'io1'
            assert _.iops == IOPS + 100
            assert _.size == SIZE * to_bytes

    def test_T000_with_vol_type_gp2(self):
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, volume_type='gp2')
        to_bytes = 1073741824
        error = False
        try:
            for _ in ret.response.result.mapping:
                try:
                    assert _.volume_type == 'gp2'
                    if _.device != '/dev/xvdc':
                        _.iops is None
                    else:
                        if _.iops != IOPS:
                            error = True
                        assert _.iops == IOPS
                    assert _.size == SIZE * to_bytes
                except OscApiException as error:
                    if error:
                        pass
                    else:
                        misc.assert_error(error, 200, 0, '')
        finally:
            if error:
                known_error('TINA-6700', 'Iops value is set to None after an intel.update_bdm')
            assert False, 'Remove known error'

    def test_T0000_with_vol_type_gp2_std(self):
        pass

    def test_T0000_with_invalid_vol_type(self):
        pass

    def test_T000_with_lower_size(self):
        pass

