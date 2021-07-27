import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_instances, start_instances
from qa_tina_tools.tools.tina.delete_tools import stop_instances, terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


@pytest.mark.region_admin
class Test_pin_unpin_instance(OscTinaTest):
    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.inst_id = None
        cls.server = None
        super(Test_pin_unpin_instance, cls).setup_class()

    def setup_method(self, method):
        OscTinaTest.setup_method(self, method)
        try:
            self.inst_info = create_instances(self.a1_r1)
            self.inst_id = self.inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.intel.instance.find(id=self.inst_id)
            self.server = ret.response.result[0].servers[0].server
            stop_instances(self.a1_r1, [self.inst_id])
            self.a1_r1.intel.instance.pin(vmid=self.inst_id, target=self.server)
            start_instances(self.a1_r1, [self.inst_id])
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.inst_info:
                terminate_instances(self.a1_r1, [self.inst_id])
        finally:
            OscTinaTest.teardown_method(self, method)

    @pytest.mark.region_admin
    def test_T4629_pin_terminated_instance(self):
        terminate_instances(self.a1_r1, [self.inst_id])
        self.inst_info = None
        try:
            self.a1_r1.intel.instance.pin(vmid=self.inst_id, target=self.server)
            assert False, 'Call should not been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state')

    def test_T4630_unpin_terminated_instance(self):
        terminate_instances(self.a1_r1, [self.inst_id])
        self.inst_info = None
        try:
            self.a1_r1.intel.instance.unpin(vmid=self.inst_id)
            assert False, 'Call should not been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-state')

    def test_T4631_check_empty_user_data_for_terminated_instance_pinned(self):
        terminate_instances(self.a1_r1, [self.inst_id])
        self.inst_info = None
        ret = self.a1_r1.intel.instance.find(id=self.inst_id)
        assert ret.response.result[0].user_data == ''

    def test_T4686_with_different_az(self):
        stop_instances(self.a1_r1, [self.inst_id])
        try:
            self.a1_r1.intel.instance.pin(vmid=self.inst_id, target="in1-ucs2-pr-kvm-1")
            assert False, 'Call should not been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, "invalid-target - Target: in1-ucs2-pr-kvm-1, PZ: in1b. Expected: in1")
