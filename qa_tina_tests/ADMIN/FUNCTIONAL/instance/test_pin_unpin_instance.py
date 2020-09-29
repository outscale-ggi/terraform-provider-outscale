import pytest
from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, start_instances
from qa_tina_tools.tools.tina.delete_tools import terminate_instances, stop_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


class Test_pin_unpin_instance(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.inst_id = None
        super(Test_pin_unpin_instance, cls).setup_class()
        try:
            pass
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_pin_unpin_instance, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        try:
            self.inst_info = create_instances(self.a1_r1)
            self.inst_id = self.inst_info[INSTANCE_ID_LIST][0]
            ret = self.a1_r1.intel.instance.find(id=self.inst_id)
            self.server = ret.response.result[0].servers[0].server
            stop_instances(self.a1_r1, [self.inst_id])
            self.a1_r1.intel.instance.pin(vmid=self.inst_id, target=self.server)
            start_instances(self.a1_r1, [self.inst_id])
        except OscApiException as error:
            try:
                self.teardown_method(method)
            except Exception:
                pass
            raise error

    def teardown_method(self, method):
        try:
            if self.inst_info:
                terminate_instances(self.a1_r1, [self.inst_id])
        finally:
            OscTestSuite.teardown_method(self, method)

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
            self.a1_r1.intel.instance.pin(vmid=self.inst_id, target="in2-ucs1-pr-kvm-13")
            assert False, 'Call should not been successful'
        except OscApiException as error:
            assert_error(error, 200, 0, "invalid-target - Target: in2-ucs1-pr-kvm-13, PZ: in2b. Expected: in2")
