import pytest

from qa_test_tools.config import config_constants as constants

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, KEY_PAIR, PATH, INSTANCE_ID_LIST
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state


class Test_create_image_from_snapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_image_from_snapshot, cls).setup_class()

        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_create_image_from_snapshot, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T1572_create_image_from_snapshot(self):
        ci1_info = None
        ci2_info = None
        ret_ri = None
        ret_cs = None
        try:
            # run instance
            ci1_info = create_instances(self.a1_r1, state='ready')
            assert len(ci1_info[INSTANCE_SET]) == 1
            instance = ci1_info[INSTANCE_SET][0]
            # check instance connection
            SshTools.check_connection_paramiko(instance['ipAddress'], ci1_info[KEY_PAIR][PATH],
                                               username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # get instance boot disk
            assert len(instance['blockDeviceMapping']) == 1
            # stop instance
            stop_instances(self.a1_r1, ci1_info[INSTANCE_ID_LIST], force=True, wait=True)
            # snapshot instance boot disk
            ret_cs = self.a1_r1.fcu.CreateSnapshot(VolumeId=instance['blockDeviceMapping'][0]['ebs']['volumeId'])
            wait_snapshots_state(self.a1_r1, [ret_cs.response.snapshotId], 'completed')
            # create omi from snapshot
            image_name = id_generator(prefix='img_')
            ret_ri = self.a1_r1.fcu.RegisterImage(BlockDeviceMapping=[{'Ebs': {'SnapshotId': ret_cs.response.snapshotId}, 'DeviceName': '/dev/sda1'}],
                                                  Name=image_name, RootDeviceName='/dev/sda1', Architecture='x86_64')
            # run instance with new omi
            ci2_info = create_instances(self.a1_r1, state='ready', omi_id=ret_ri.response.imageId)
            assert len(ci2_info[INSTANCE_SET]) == 1
            # check instance connection
            SshTools.check_connection_paramiko(ci2_info[INSTANCE_SET][0]['ipAddress'], ci2_info[KEY_PAIR][PATH],
                                               username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        finally:
            if ci2_info:
                try:
                    delete_instances(self.a1_r1, ci2_info)
                except:
                    pass
            if ci1_info:
                try:
                    delete_instances(self.a1_r1, ci1_info)
                except:
                    pass
            if ret_ri:
                try:
                    cleanup_images(self.a1_r1, image_id_list=[ret_ri.response.imageId], force=True)
                except:
                    pass

    @pytest.mark.region_admin
    def test_T5246_create_image_from_snapshot_without_product_type(self):
        ret_ri = None
        ret_cs = None
        vol_id = None
        try:
            ret = self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name, Size='1')
            vol_id = ret.response.volumeId
            wait_volumes_state(osc_sdk=self.a1_r1, state='available', volume_id_list=[vol_id])
            # snapshot volume
            ret_cs = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id)
            wait_snapshots_state(self.a1_r1, [ret_cs.response.snapshotId], 'completed')
            ret = self.a1_r1.fcu.GetProductType(SnapshotId=ret_cs.response.snapshotId)
            assert ret.response.productTypeId == '0001'
            self.a1_r1.intel.product.set(resource=ret_cs.response.snapshotId, product_ids=[])
            ret = self.a1_r1.fcu.GetProductType(SnapshotId=ret_cs.response.snapshotId)
            assert not ret.response.productTypeId
            # create omi from snapshot
            image_name = id_generator(prefix='img_')
            ret_ri = self.a1_r1.fcu.RegisterImage(
                BlockDeviceMapping=[{'Ebs': {'SnapshotId': ret_cs.response.snapshotId},
                                     'DeviceName': '/dev/sda1'}], Name=image_name,
                RootDeviceName='/dev/sda1', Architecture='x86_64')
            ret = self.a1_r1.fcu.GetProductType(ImageId=ret_ri.response.imageId)
            assert ret.response.productTypeId == '0001'
        finally:
            if ret_ri:
                try:
                    cleanup_images(self.a1_r1, image_id_list=[ret_ri.response.imageId], force=True)
                except:
                    pass
            if vol_id:
                # remove volume
                self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                wait_volumes_state(osc_sdk=self.a1_r1, cleanup=True, volume_id_list=[vol_id])
