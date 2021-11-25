import string

import pytest

from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_snapshots_state
from qa_tina_tools.tools.state import SnapshotStatus, VolumeStatus


@pytest.mark.region_admin
class Test_get_product_types(OscTinaTest):

    def test_T6107_with_valid_parameters(self):
        img_id = None
        inst_info = None
        vol_id_list = None
        snap_id = None

        try:

            inst_info = create_instances(self.a1_r1, state="running")
            img_name = id_generator(prefix="omi-", size=8, chars=string.ascii_lowercase)
            img_id = self.a1_r1.fcu.CreateImage(InstanceId=inst_info[INSTANCE_ID_LIST][0],
                                                Name=img_name).response.imageId
            _, vol_id_list = create_volumes(self.a1_r1)
            vol1_id = vol_id_list[0]
            wait_volumes_state(self.a1_r1, vol_id_list, VolumeStatus.Available.value)
            snap_id = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol1_id).response.snapshotId
            wait_snapshots_state(self.a1_r1, [snap_id], SnapshotStatus.Completed.value)
            ret = self.a1_r1.intel.oapi.product_type.get_product_types(owner_id=self.a1_r1.config.account.account_id,
                                                                       snapshot_id=snap_id)
            assert ret.response.result.product_types[0].product_type_id == '0001'
            assert ret.response.result.product_types[0].description == 'Linux/UNIX'
            ret = self.a1_r1.intel.oapi.product_type.get_product_types(owner_id=self.a1_r1.config.account.account_id,
                                                                       image_id=img_id)
            assert ret.response.result.product_types[0].product_type_id == '0001'
            assert ret.response.result.product_types[0].description == 'Linux/UNIX'
        finally:
            if img_id:
                self.a1_r1.fcu.DeregisterImage(ImageId=img_id)
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
            if snap_id:
                self.a1_r1.fcu.DeleteSnapshot(SnapshotId=snap_id)
            if vol_id_list:
                delete_volumes(self.a1_r1, vol_id_list)
