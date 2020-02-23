from qa_common_tools.constants import CENTOS_USER
from qa_tina_tools.tools.state import InstanceState
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_keypair
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, NAME, PATH, \
    INSTANCE_ID_LIST
from qa_common_tools.ssh import SshTools


class Test_instance_metadata(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.URL = 'http://169.254.169.254/latest/meta-data/'
        cls.kp_info = None
        cls.inst_info = None
        super(Test_instance_metadata, cls).setup_class()
        try:
            cls.kp_info = create_keypair(cls.a1_r1)
            cls.inst_info = create_instances(cls.a1_r1, state=InstanceState.Ready.value, key_name=cls.kp_info[NAME])
            inst = cls.inst_info[INSTANCE_SET][0]
            cls.a1_r1.fcu.CreateTags(ResourceId=[inst['instanceId']], Tag=[{'Key': 'key1', 'Value': 'value1'},
                                                                           {'Key': 'key2', 'Value': 'value2'},
                                                                           {'Key': 'key3', 'Value': ''}])
            cls.connection = SshTools.check_connection_paramiko(inst['ipAddress'], cls.kp_info[PATH], cls.a1_r1.config.region.get_info(CENTOS_USER))
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.kp_info:
                delete_keypair(cls.a1_r1, cls.kp_info)
        finally:
            super(Test_instance_metadata, cls).teardown_class()

    def check(self, metadata_category, expected_response, URL):
        command = 'curl {}/{} 2> /dev/null'.format(URL, metadata_category)
        output, _, _ = SshTools.exec_command_paramiko_2(self.connection, command)
        if expected_response:
            assert output.strip() == expected_response
        return output

    def test_T1771_tags_access(self):
        out, _, _ = SshTools.exec_command_paramiko_2(self.connection, 'curl http://169.254.169.254/latest/meta-data/tags/')
        keys = out.split()
        assert len(keys) == 3
        assert 'key1' in keys
        assert 'key2' in keys
        assert 'key3' in keys

    def test_T1772_latest_metadata_access(self):
        out, _, _ = SshTools.exec_command_paramiko_2(self.connection, 'curl http://169.254.169.254/latest/meta-data/')
        assert 'tags/' in out.split()

    def test_T1778_tag_value_access(self):
        out1, _, _ = SshTools.exec_command_paramiko_2(self.connection, 'curl http://169.254.169.254/latest/meta-data/tags/key1')
        out2, _, _ = SshTools.exec_command_paramiko_2(self.connection, 'curl http://169.254.169.254/latest/meta-data/tags/key2')
        out3, _, _ = SshTools.exec_command_paramiko_2(self.connection, 'curl http://169.254.169.254/latest/meta-data/tags/key3')
        assert out1.strip() == 'value1'
        assert out2.strip() == 'value2'
        assert out3.strip() == ''

    def test_T1780_metadata_access(self):
        out, _, _ = SshTools.exec_command_paramiko_2(self.connection, 'curl http://169.254.169.254/')
        values = out.split()
        assert '1.0' == values[0]
        assert 'latest' == values[len(values) - 1]

    def test_T1779_latest_access(self):
        out, _, _ = SshTools.exec_command_paramiko_2(self.connection, 'curl http://169.254.169.254/latest/')
        values = out.split()
        assert len(values) == 2
        assert 'user-data' in values
        assert 'meta-data' in values

    def test_T4595_check_meta_data(self):
        instance = self.a1_r1.intel.instance.get(owner=self.a1_r1.config.account.account_id,
                                             id=self.inst_info[INSTANCE_ID_LIST][0]).response.result
        for metadata_category, expected_msg in [
            ('ami-id', instance.image),
            ('ami-launch-index', instance.launch_index),
            ('placement/availability-zone', instance.az),
            ('block-device-mapping/ami', instance.mapping[0].device),
            ('block-device-mapping/root', instance.mapping[0].device),
            ('hostname', instance.private_dns),
            ('instance-id', instance.id),
            ('instance-type', instance.type),
            ('local-hostname', instance.private_dns),
            ('mac', instance.mac_addr),
            ('local-ipv4', instance.private_ip),
            ('public-hostname', instance.public_dns),
            ('public-ipv4', instance.public_ip),
            ('reservation-id', instance.reservation),
            ('security-groups', instance.groups[0].name),
        ]:
            self.check(metadata_category, expected_msg, self.URL)
        nic0 = instance.nics[0]
        # NIC checks
        self.URL += 'network/interfaces/macs/{}/'.format(nic0.macaddr)
        for metadata_category, expected_msg in [
            ('device-number', 0),
            ('interface-id', nic0.id),
            ('gateway-ipv4', instance.gateway_ip),
            ('ipv4-associations/', nic0.public_ip),
            ('local-hostname', nic0.private_dns),
            ('mac', nic0.macaddr),
            ('owner-id', nic0.owner),
            ('public-hostname', nic0.public_dns),
            ('local-ipv4s', nic0.ip),
            ('public-ipv4s', nic0.public_ip),
            ('security-groups', nic0.groups[0].name),
            ('security-group-ids', nic0.groups[0].id),
            ('subnet-id', nic0.private_subnet),
        ]:
            self.check(metadata_category, expected_msg, self.URL)
