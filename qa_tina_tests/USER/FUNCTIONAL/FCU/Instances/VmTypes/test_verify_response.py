
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, start_instances
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances
from qa_test_tools.config import config_constants as constants


class Test_verify_response(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info1 = None
        cls.inst_info2 = None
        cls.inst_type = 'tinav5.c4r8p3'
        super(Test_verify_response, cls).setup_class()
        try:
            cls.inst_info1 = create_instances(cls.a1_r1)
            cls.inst_info2 = create_instances(cls.a1_r1, inst_type=cls.inst_type)
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
                delete_instances(cls.a1_r1, cls.inst_info1)
            if cls.inst_info2:
                delete_instances(cls.a1_r1, cls.inst_info2)
        finally:
            super(Test_verify_response, cls).teardown_class()

    def verif_instance_type(self, instanceid=None, default_type=None, converted_type=None):
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=instanceid, state='running')
        ret = self.a1_r1.fcu.DescribeInstances(InstanceId=[instanceid[0]])
        assert ret.response.reservationSet[0].instancesSet[0].instanceType == default_type
        stop_instances(osc_sdk=self.a1_r1, instance_id_list=instanceid, force=True)
        wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=instanceid, state='stopped')
        ret = self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=instanceid[0], InstanceType={'Value': converted_type})
        start_instances(osc_sdk=self.a1_r1, instance_id_list=instanceid, state='running')
        ret = self.a1_r1.fcu.DescribeInstances(InstanceId=instanceid[0])
        assert ret.response.reservationSet[0].instancesSet[0].instanceType == converted_type


    def test_T4348_t2nano_to_cxrypz(self):
        default_type = self.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
        self.verif_instance_type(instanceid=self.inst_info1[INSTANCE_ID_LIST], default_type=default_type, converted_type=self.inst_type)
        
    def test_T4349_cxrypz_to_t2nano(self):
        default_type = self.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)
        self.verif_instance_type(instanceid=self.inst_info2[INSTANCE_ID_LIST], default_type=self.inst_type, converted_type=default_type)
