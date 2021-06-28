
import pytest

from qa_tina_tools.tina import wait
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.config import config_constants as constants

class Test_CreateSnapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vm_id = None
        cls.snap_ids = None
        super(Test_CreateSnapshot, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateSnapshot, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateSnapshot, self).setup_method(method)
        self.snap_ids = []
        try:
            self.vm_id = self.a1_r1.oapi.CreateVms(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS_LATEST)).response.Vms[0].VmId
            wait.wait_Vms_state(self.a1_r1, [self.vm_id], state='ready')
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.snap_ids:
                for snap_id in self.snap_ids:
                    self.a1_r1.oapi.DeleteSnapshot(SnapshotId=snap_id)
                wait.wait_Snapshots_state(self.a1_r1, self.snap_ids, cleanup=True)
            if self.vm_id:
                self.a1_r1.oapi.DeleteVms([self.vm_id])
                wait.wait_Vms_state(self.a1_r1, [self.vm_id], state='terminated')
        except Exception as error:
            self.logger.exception(error)
            pytest.fail("An unexpected error happened : " + str(error))
        finally:
            super(Test_CreateSnapshot, self).teardown_method(method)

    def test_T5766_create_snap_when_vm_terminated(self):
        pytest.skip("Test need to set consul config intel/restart_snapshot_creation")
        vm_info = self.a1_r1.oapi.ReadVms(Filters={'VmIds': [self.vm_id]}).response.Vms[0]
        volume_id = vm_info.BlockDeviceMappings[0].Bsu.VolumeId

        ret = self.a1_r1.oapi.CreateSnapshot(VolumeId=volume_id, Description='hello')
        self.snap_ids.append(ret.response.Snapshot.SnapshotId)

        try:
            self.a1_r1.oapi.DeleteVms(VmIds=[vm_info.VmId])
            self.vm_id = None
        except Exception as error:
            self.logger.exception(error)
            pytest.fail("An unexpected error happened : " + str(error))
        finally:
            try:
                wait.wait_Snapshots_state(self.a1_r1, [ret.response.Snapshot.SnapshotId], state='completed')
            except Exception as error:
                self.logger.exception(error)
                pytest.fail("An unexpected error happened : " + str(error))
