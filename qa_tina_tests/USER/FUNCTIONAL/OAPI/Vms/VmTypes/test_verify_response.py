
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tests.USER.API.OAPI.Vm.Vm import create_vms
from qa_tina_tools.tools.tina.create_tools import start_instances
from qa_tina_tools.tools.tina.delete_tools import stop_instances
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_verify_response(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info1 = None
        cls.inst_info2 = None
        cls.converted_type = 'tinav5.c4r8p1'
        cls.default_type = 't2.small'
        super(Test_verify_response, cls).setup_class()
        try:
            _, cls.inst_info1 = create_vms(ocs_sdk=cls.a1_r1, state=None)
            _, cls.inst_info2 = create_vms(ocs_sdk=cls.a1_r1, state=None, VmType=cls.converted_type)

        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info1:
                cls.a1_r1.oapi.DeleteVms(VmIds=cls.inst_info1)
            if cls.inst_info2:
                cls.a1_r1.oapi.DeleteVms(VmIds=cls.inst_info2)
        finally:
            super(Test_verify_response, cls).teardown_class()

    def verif_instance_type(self, instanceid=None, default_type=None, converted_type=None, default_perf=None, new_perf=None):
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=instanceid, state='running')
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': instanceid})
        assert ret.response.Vms[0].VmType == default_type
        assert ret.response.Vms[0].Performance == default_perf
        stop_instances(osc_sdk=self.a1_r1, instance_id_list=instanceid, force=True)
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=instanceid, state='stopped')
        self.a1_r1.oapi.UpdateVm(VmId=instanceid[0], VmType=converted_type)
        start_instances(osc_sdk=self.a1_r1, instance_id_list=instanceid, state='running')
        ret = self.a1_r1.oapi.ReadVms(Filters={'VmIds': instanceid})
        assert ret.response.Vms[0].VmType == converted_type
        assert ret.response.Vms[0].Performance == new_perf

    def test_T4350_t2small_to_cxrypz(self):
        self.verif_instance_type(instanceid=self.inst_info1, default_type=self.default_type, converted_type=self.converted_type, default_perf='medium', new_perf='highest')

    def test_T4351_cxrypz_to_t2small(self):
        self.verif_instance_type(instanceid=self.inst_info2, default_type=self.converted_type, converted_type=self.default_type, default_perf='highest', new_perf='medium')
