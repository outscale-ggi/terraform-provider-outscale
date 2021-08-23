import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
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
            bdm = [{'DeviceName': '/dev/xvdb', 'Ebs': {'DeleteOnTermination': 'true', 'VolumeSize': str(SIZE), 'VolumeType': 'standard'}},
                   {'DeviceName': '/dev/xvdc', 'Ebs': {'DeleteOnTermination': 'true', 'VolumeSize': str(SIZE), 'VolumeType': 'io1', 'Iops': IOPS}},
                   {'DeviceName': '/dev/xvdd', 'Ebs': {'DeleteOnTermination': 'true', 'VolumeSize': str(SIZE), 'VolumeType': 'gp2'}}]
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
            ret = self.a1_r1.oapi.CreateImage(VmId=self.vm_info[info_keys.VM_IDS][0], Name=misc.id_generator(prefix='omi_'), NoReboot=True)
            self.image_id = ret.response.ImageId
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

    # sample error test
    def test_T0000_incorrect_size(self):
        try:
            self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, size=SIZE - 1)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '', '')

    # sample successful test
    def test_T0000_modified_size(self):
        self.a1_r1.intel.image.update_bdm(owner=self.a1_r1.config.account.account_id, image_id=self.image_id, size=SIZE + 1)
        self.check_image()
