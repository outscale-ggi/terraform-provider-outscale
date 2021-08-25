import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
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
TO_BYTES = 1073741824


@pytest.mark.region_admin
class Test_update_image_bdm(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.bdm = None
        cls.vm_info = None
        cls.image_id = None
        cls.snapshot_id = None
        cls.size = None
        cls.delete_termination_state = False
        super(Test_update_image_bdm, cls).setup_class()
        try:
            cls.vm_info = oapi.create_Vms(cls.a1_r1, nb=1, state='running')
            oapi.stop_Vms(cls.a1_r1, cls.vm_info[info_keys.VM_IDS], force=False)
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
            if cls.vm_info:
                oapi.delete_Vms(cls.a1_r1, cls.vm_info)
        finally:
            super(Test_update_image_bdm, cls).teardown_class()

    def setup_method(self, method):
        self.image_id = None
        self.snapshot_id = None
        self.size = None
        self.delete_termination_state = False
        OscTinaTest.setup_method(self, method)
        try:
            ret = self.a1_r1.oapi.CreateImage(VmId=self.vm_info[info_keys.VM_IDS][0], ImageName=id_generator(prefix='omi_'), NoReboot=True)
            self.image_id = ret.response.Image.ImageId
            self.snapshot_id = ret.response.Image.BlockDeviceMappings[0].Bsu.SnapshotId
            self.size = ret.response.Image.BlockDeviceMappings[0].Bsu.VolumeSize
            self.delete_termination_state = ret.response.Image.BlockDeviceMappings[0].Bsu.DeleteOnVmDeletion
            wait.wait_Images_state(osc_sdk=self.a1_r1, image_ids=[self.image_id], state='available')
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

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

    def test_T5896_without_params(self):
        try:
            self.a1_r1.intel.image.update_bdm()
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'missing-parameter - Parameter cannot be empty: ImageID')

    def test_T5897_with_required_params(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id)
        except OscApiException as error:
            if error.message == "missing-parameter - Insufficient parameters provided out of: DeleteOnTermination, size," \
                                " volumeType. Expected at least: 1":
                known_error('TINA-6704', 'error messages with the call intel.update_bdm')
            assert False, 'Remove known error'

    def test_T5898_without_image_id(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'missing-parameter - Parameter cannot be empty: ImageID')

    def test_T5899_without_owner(self):
        try:
            self.a1_r1.intel.image.update_bdm(image_id=self.image_id)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'missing-parameter - Parameter cannot be empty: Owner')

    def test_T5900_with_all_params(self):
        new_size = (SIZE + 10) * TO_BYTES
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id,
                                                snapshot_id=self.snapshot_id, delete_on_termination=False, volume_type='io1',
                                                size=new_size, iops=IOPS+100)
        for elt in ret.response.result.mapping:
            assert elt.size == new_size
            assert elt.volume_type == 'io1'
            assert elt.delete_on_termination is False
            assert elt.iops == IOPS + 100

    def test_T5901_with_snapshot_id(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, snapshot_id=self.snapshot_id)
            assert False, 'Remove known error'
        except OscApiException as error:
            if error.message == "missing-parameter - Insufficient parameters provided out of: DeleteOnTermination, size," \
                                " volumeType. Expected at least: 1":
                known_error('TINA-6704', 'error messages with the call intel.update_bdm')
            assert False, 'Remove known error'

    def test_T5902_with_size(self):
        new_size = (SIZE + 10) * TO_BYTES
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, size=new_size)
        assert ret.response.result.mapping[0].size == new_size

    def test_T5903_with_volume_type_io1(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id,
                                              volume_type='io1')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-parameter - Parameter IOPS is required for: io1')

    def test_T5904_with_volume_type_gp2(self):
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id,
                                                volume_type='gp2')
        assert ret.response.result.mapping[0].volume_type == 'gp2'
        assert ret.response.result.mapping[0].size == self.size * TO_BYTES

    def test_T5905_with_volume_type_and_iops(self):
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, volume_type='io1', iops=IOPS+100)
        for _ in ret.response.result.mapping:
            assert _.volume_type == 'io1'
            assert _.iops == IOPS + 100
            assert _.size == SIZE * TO_BYTES

    def test_T5906_with_iops(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, iops=IOPS+100)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'missing-parameter - Insufficient parameters provided out of: DeleteOnTermination,'
                                             ' size, volumeType. Expected at least: 1')

    def test_T5907_with_delete_on_termination(self):
        ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, delete_on_termination=False)
        assert ret.response.result.mapping[0].delete_on_termination is False

    def test_T5908_with_invalid_owner(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner='foo', image_id=self.image_id)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            # Plutôt no-such-owner !
            assert_error(error, 200, 0, "missing-parameter - Insufficient parameters provided out of: DeleteOnTermination,"
                                             " size, volumeType. Expected at least: 1")

    def test_T5909_with_invalid_image_id(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id='foo')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-id-prefix - Invalid ID received: foo. Expected format: ami-, aki-, ari-')

    def test_T5910_with_invalid_snapshot_id(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, snapshot_id='foo')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-id-prefix - Invalid ID received: foo. Expected format: snap-')

    def test_T5911_with_invalid_delete_on_termination(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, delete_on_termination='foo')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, "invalid-parameter-type - Value of parameter 'DeleteOnTermination' must be of type: bool. Received: foo")

    def test_T5912_with_invalid_iops(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, iops='foo')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            # error msg !
            assert_error(error, 200, 0, 'missing-parameter - Insufficient parameters provided out of: DeleteOnTermination,'
                                             ' size, volumeType. Expected at least: 1')

    def test_T5913_with_invalid_size(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, size='foo')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, "invalid-parameter-type - Value of parameter 'Size' must be of type: int. Received: foo")

    def test_T5914_with_invalid_volume_type(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, volume_type='foo')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert error.message.startswith("invalid-parameter-value - Value of parameter 'VolumeType' is not valid: foo.")
            assert error.status_code == 200

    def test_T5915_from_another_account(self):
        try:
            new_size = (SIZE + 10) * TO_BYTES
            self.a2_r1.intel.image.update_bdm(owner=self.a2_r1.config.account.account_id, image_id=self.image_id, size=new_size)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'no-such-image')

    def test_T5916_update_size_of_vol_io1_without_iops(self):
        vm_info = None
        img_id = None
        new_size = (SIZE + 10) * TO_BYTES
        try:
            bdm = [{'DeviceName': '/dev/xvdc',
                    'Bsu': {'DeleteOnVmDeletion': True, 'VolumeSize': SIZE, 'VolumeType': 'io1', 'Iops': IOPS}}]

            vm_info = oapi.create_Vms(self.a1_r1, nb=1, bdm=bdm, state='running')
            oapi.stop_Vms(self.a1_r1, vm_info[info_keys.VM_IDS], force=False)

            img = self.a1_r1.oapi.CreateImage(VmId=vm_info[info_keys.VM_IDS][0],
                                              ImageName=id_generator(prefix='omi_'), NoReboot=True)
            img_id = img.response.Image.ImageId
            wait.wait_Images_state(osc_sdk=self.a1_r1, image_ids=[img_id], state='available')

            ret = self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=img_id,
                                                    size=new_size)
            for _ in ret.response.result.mapping:
                assert _.size == new_size
                if _.volume_type == 'io1':
                    if _.iops != IOPS:
                        known_error('TINA-6700', 'Iops value is set to None after an intel.update_bdm')
                    assert False, 'Remove known error'
                    assert _.iops == IOPS
        finally:
            if vm_info:
                oapi.delete_Vms(self.a1_r1, vm_info)
            if img_id:
                self.a1_r1.oapi.DeleteImage(ImageId=img_id)
