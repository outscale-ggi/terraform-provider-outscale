import datetime

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances, \
    terminate_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info1 = None
        cls.inst_info2 = None
        super(Test_find, cls).setup_class()
        try:
            cls.start_date = (datetime.datetime.utcnow() - datetime.timedelta(minutes=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            cls.inst_info1 = create_instances(cls.a1_r1, nb=1, inst_type='tinav3.c2r8p2')
            cls.inst_info2 = create_instances(cls.a1_r1, nb=3, inst_type='tinav2.c1r1p1')
            # cls.stopping_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            stop_instances(cls.a1_r1, instance_id_list=cls.inst_info2[INSTANCE_ID_LIST][0:1])
            # cls.terminating_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            terminate_instances(cls.a1_r1, instance_id_list=cls.inst_info2[INSTANCE_ID_LIST][1:2])
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
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='tinav2.c1r1p1')
        assert len(ret.response.result) == 3

    def test_T3783_with_filters_creation_date(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='tinav2.c1r1p1',
                                             creation_date=[self.start_date, self.end_date])
        assert len(ret.response.result) == 3

    def test_T3784_with_filters_destruction_date(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='tinav2.c1r1p1',
                                             destruction_date=[self.start_date, self.end_date])
        assert len(ret.response.result) == 1

    def test_T3785_with_filters_state_last_changed(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, type='tinav2.c1r1p1',
                                             state_last_changed=[self.start_date, self.end_date])
        assert len(ret.response.result) == 3

    def test_T4569_with_filters_performance(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, performance=['2'])
        assert len(ret.response.result) == 1

    def test_T4570_with_filters_generation(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, generation=['2'])
        assert len(ret.response.result) == 3
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, generation=['3'])
        assert len(ret.response.result) == 1

    def test_T4571_with_filters_generation_performance(self):
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id, generation=['3'], performance=['2'])
        assert len(ret.response.result) == 1

    def test_T4316_check_response(self):
        attributes = ['allocate_console', 'allocated_pci', 'api_termination', 'architecture', 'asked_type', 'az', 'boot_on_creation',
                     'cdrom_attach', 'core', 'creation', 'creation_date', 'destruction_date', 'ephemerals', 'gateway_ip', 'groups', 'id', 'image', 'imaging',
                     'in_vpc', 'inconsistent', 'keypair', 'keypairs', 'launch_index', 'lifecycle', 'mac_addr', 'mapping', 'memory', 'migration',
                     'network', 'nics', 'owner', 'platform', 'private_dns', 'private_ip', 'private_only', 'product_types', 'public_dns', 'public_ip',
                     'pvops_enabled', 'quarantine', 'required_pci', 'reservation', 'root_device', 'root_type', 'rstate', 'run', 'servers',
                     'shutdown_behavior', 'slots', 'source_dest_check', 'specs', 'started_once', 'state', 'state_last_changed', 'state_reason',
                     'sticky_slot', 'storage_bandwidth', 'subnet', 'tags', 'tenancy', 'terminating', 'tina_type', 'tina_type_compliant', 'token',
                      'type', 'user_data', 'ustate']
        wait_instances_state(self.a1_r1, self.inst_info1[INSTANCE_ID_LIST], state='running')
        ret = self.a1_r1.intel.instance.find(owner=self.a1_r1.config.account.account_id,
                                             id=self.inst_info1[INSTANCE_ID_LIST][0])
        for attribute in attributes:
            assert hasattr(ret.response.result[0], attribute), "Missing {} attribute".format(attribute)
