from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, \
    terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
import datetime
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info1 = None
        cls.inst_info2 = None
        super(Test_find, cls).setup_class()
        try:
            cls.start_date = (datetime.datetime.utcnow() - datetime.timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            cls.inst_info2 = create_instances(cls.a1_r1, nb=1, inst_type='tinav3.c2r8')
            cls.inst_info1 = create_instances(cls.a1_r1, nb=3, inst_type='t2.small')
            # cls.stopping_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            stop_instances(cls.a1_r1, instance_id_list=cls.inst_info1[INSTANCE_ID_LIST])
            # cls.terminating_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            terminate_instances(cls.a1_r1, instance_id_list=cls.inst_info1[INSTANCE_ID_LIST])
            cls.end_date = (datetime.datetime.utcnow() + datetime.timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info2:
                delete_instances(cls.a1_r1, cls.inst_info2)
            if cls.inst_info1:
                delete_instances(cls.a1_r1, cls.inst_info1)
        finally:
            super(Test_find, cls).teardown_class()

    def test_T3576_with_filters_type(self):
        inst_info = create_instances(self.a1_r1, nb=3, inst_type='t2.micro')
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='t2.micro')
        assert len(ret.response.result) == 3
        terminate_instances(self.a1_r1, instance_id_list=inst_info[INSTANCE_ID_LIST])

    def test_T3783_with_filters_creation_date(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='t2.small',
                                             creation_date=[self.start_date, self.end_date])
        assert len(ret.response.result) == 3

    def test_T3784_with_filters_destruction_date(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='t2.small',
                                             destruction_date=[self.start_date, self.end_date])
        assert len(ret.response.result) == 3

    def test_T3785_with_filters_state_last_changed(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='t2.small',
                                             state_last_changed=[self.start_date, self.end_date])
        assert len(ret.response.result) == 3

    def test_T4569_with_filters_performance(self):
        inst_info = create_instances(self.a1_r1, nb=2, inst_type='t1.micro')
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, performance=['3'])
        assert len(ret.response.result) == 8
        terminate_instances(self.a1_r1, instance_id_list=inst_info[INSTANCE_ID_LIST])

    def test_T4570_with_filters_generation(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, generation=['1'])
        assert len(ret.response.result) == 2
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, generation=['2'])
        assert len(ret.response.result) == 6

    def test_T4571_with_filters_generation_performance(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, generation=['1'], performance=['3'])
        assert len(ret.response.result) == 2

    def test_T4316_check_response(self):
        attributes = ['tina_type', 'allocate_console', 'allocated_pci', 'api_termination', 'architecture', 'asked_type', 'az', 'boot_on_creation',
                     'cdrom_attach', 'core', 'creation', 'creation_date', 'destruction_date', 'ephemerals', 'groups', 'id', 'image', 'imaging',
                     'in_vpc', 'inconsistent', 'keypair', 'keypairs', 'launch_index', 'lifecycle', 'mac_addr', 'mapping', 'memory', 'migration',
                     'network', 'nics', 'owner', 'platform', 'private_dns', 'private_ip', 'private_only', 'product_types', 'public_dns', 'public_ip',
                     'pvops_enabled', 'quarantine', 'required_pci', 'reservation', 'root_device', 'root_type', 'rstate', 'run', 'servers',
                     'shutdown_behavior', 'slots', 'source_dest_check', 'specs', 'started_once', 'state', 'state_last_changed', 'state_reason',
                     'sticky_slot', 'storage_bandwidth', 'subnet', 'tags', 'tenancy', 'terminating', 'tina_type', 'tina_type_compliant', 'token',
                      'type', 'user_data', 'ustate', 'gateway_ip']
        wait_instances_state(self.a1_r1, self.inst_info2[INSTANCE_ID_LIST], state='running')
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id,
                                             id=self.inst_info2[INSTANCE_ID_LIST][0])
        for attribute in attributes:
            assert hasattr(ret.response.result[0], attribute), "Missing {} attribute".format(attribute)
