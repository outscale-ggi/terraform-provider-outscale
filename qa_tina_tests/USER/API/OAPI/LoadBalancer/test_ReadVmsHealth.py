import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.setup_tools import setup_public_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old, delete_lbu


class Test_ReadVmsHealth(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadVmsHealth, cls).setup_class()
        cls.lbu_name = id_generator(prefix='lb-')
        cls.lbu_name2 = id_generator(prefix='lb-')
        cls.inst_ids = None
        cls.inst_ids2 = None
        cls.ret_lb = None
        cls.ret_lb2 = None
        try:
            cls.inst_ids, cls.ret_lb = setup_public_load_balancer(cls.a1_r1, cls.lbu_name, [cls.a1_r1.config.region.az_name], state='ready')
            cls.inst_ids2, cls.ret_lb2 = setup_public_load_balancer(cls.a1_r1, cls.lbu_name2, [cls.a1_r1.config.region.az_name], register=False,
                                                                    state='ready')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_ids:
                delete_instances_old(cls.a1_r1, cls.inst_ids)
            if cls.inst_ids2:
                delete_instances_old(cls.a1_r1, cls.inst_ids2)
            if cls.ret_lb:
                delete_lbu(cls.a1_r1, cls.lbu_name)
            if cls.ret_lb2:
                delete_lbu(cls.a1_r1, cls.lbu_name2)
        except Exception as error:
            raise error
        finally:
            super(Test_ReadVmsHealth, cls).teardown_class()

    def test_T3456_valid_params_without_register(self):
        ret = self.a1_r1.oapi.ReadVmsHealth(LoadBalancerName=self.lbu_name2)
        ret.check_response()

    def test_T2945_valid_params(self):
        ret = self.a1_r1.oapi.ReadVmsHealth(LoadBalancerName=self.lbu_name)
        assert len(ret.response.BackendVmHealth) == 2
        ret.check_response()


    def test_T2946_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadVmsHealth(LoadBalancerName=self.lbu_name, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3455_other_account(self):
        try:
            self.a2_r1.oapi.ReadVmsHealth(LoadBalancerName=self.lbu_name)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5030)
