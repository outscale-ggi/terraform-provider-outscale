
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.ssh import SshTools, OscCommandError
from qa_test_tools.config import config_constants as constants
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_vpc, start_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, stop_instances
from qa_tina_tools.tools.tina import info_keys


class Test_lan_sg_tags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.quotas = {
                        'bypass_group_limit': 5,
                        'vm_limit': 20,
                     }
        cls.vpc_info_empty = None
        cls.vpc_info_full_default = None
        cls.vpc_info_full_enable = None
        cls.vpc_info_full_disable = None
        super(Test_lan_sg_tags, cls).setup_class()
        try:
            cls.vpc_info_empty = create_vpc(cls.a1_r1, cidr_prefix='20.0', nb_subnet=0, igw=False, no_ping=True)
            cls.vpc_info_full_default = create_vpc(cls.a1_r1, cidr_prefix='30.0', nb_subnet=2, nb_instance=3, igw=True, state='running', no_ping=True)
            cls.vpc_info_full_disable = create_vpc(cls.a1_r1, cidr_prefix='40.0', nb_subnet=2, nb_instance=3, igw=True, state='running',
                                                   tags=[{'Key': 'osc.fcu.disable_lan_security_groups', 'Value': '0'}], no_ping=True)
            cls.vpc_info_full_enable = create_vpc(cls.a1_r1, cidr_prefix='50.0', nb_subnet=2, nb_instance=3, igw=True, state='running',
                                                  tags=[{'Key': 'osc.fcu.enable_lan_security_groups', 'Value': '0'}], no_ping=True)
            cls.vpc_ids = [cls.vpc_info_empty[info_keys.VPC_ID], cls.vpc_info_full_disable[info_keys.VPC_ID],
                           cls.vpc_info_full_disable[info_keys.VPC_ID], cls.vpc_info_full_enable[info_keys.VPC_ID]]
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info_empty:
                delete_vpc(cls.a1_r1, cls.vpc_info_empty)
            if cls.vpc_info_full_default:
                delete_vpc(cls.a1_r1, cls.vpc_info_full_default)
            if cls.vpc_info_full_disable:
                delete_vpc(cls.a1_r1, cls.vpc_info_full_disable)
            if cls.vpc_info_full_enable:
                delete_vpc(cls.a1_r1, cls.vpc_info_full_enable)
        finally:
            super(Test_lan_sg_tags, cls).teardown_class()

    def test_T1921_check_init_tags(self):
        for vpc_id in self.vpc_ids:
            ret = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [vpc_id]}])
            assert not ret.response.tagSet or len(ret.response.tagSet) == 1

    def add_tag(self, res_id, key, value):
        self.a1_r1.fcu.CreateTags(ResourceId=[res_id], Tag=[{'Key': key, 'Value': value}])
        ret = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [res_id]}])
        if len(ret.response.tagSet) == 2:
            known_error('TINA-4502', 'Both tags are present')
        assert len(ret.response.tagSet) == 1
        assert ret.response.tagSet[0].key == key
        assert ret.response.tagSet[0].value == value
        return ret

    def multi_check_ping(self, vpc_info, success, inc=3):
        error = None
        for _ in range(inc):
            try:
                self.check_ping(vpc_info, success)
                return
            except Exception as err:
                error = err
        if error:
            raise error

    def check_ping(self, vpc_info, success):
        try:
            out, _, _ = SshTools.run_command_paramiko(
                vpc_info[info_keys.SUBNETS][0][info_keys.EIP]['publicIp'],
                vpc_info[info_keys.KEY_PAIR][info_keys.PATH],
                'ping -c 5 {}'.format(vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_SET][1]['privateIpAddress']),
                username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        except OscCommandError as error:
            if success:
                raise error
            return
        if not success:
            assert False, 'Ping should not have been successful'
        assert '5 received' in out
        assert '0% packet loss' in out

    def delete_tag(self, res_id, key, value):
        self.a1_r1.fcu.DeleteTags(ResourceId=[res_id], Tag=[{'Key': key, 'Value': value}])

    def test_T1930_set_disable_empty(self):
        self.add_tag(self.vpc_info_empty[info_keys.VPC_ID], 'osc.fcu.disable_lan_security_groups', '1')

    def test_T1931_set_disable_full_disable(self):
        self.add_tag(self.vpc_info_full_disable[info_keys.VPC_ID], 'osc.fcu.disable_lan_security_groups', '1')

    def test_T1932_set_disable_full_enable(self):
        vpc_id = self.vpc_info_full_enable[info_keys.VPC_ID]
        try:
            self.add_tag(vpc_id, 'osc.fcu.disable_lan_security_groups', '1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message.startswith('The volume'):
                known_error('TINA-4501', 'Incorrect error message')
            assert False, 'Remove known error code'
            assert_error(error, 400, 'InvalidVpcState', 'The vpc is not in a valid state for this operation: {}.'.format(vpc_id))

    def test_T1933_set_enable_empty(self):
        self.add_tag(self.vpc_info_empty[info_keys.VPC_ID], 'osc.fcu.enable_lan_security_groups', '1')

    def test_T1934_set_enable_full_enable(self):
        try:
            self.add_tag(self.vpc_info_full_enable[info_keys.VPC_ID], 'osc.fcu.enable_lan_security_groups', '1')
            assert False, 'Remove known error code'
        except OscApiException as error:
            assert_error(error, 500, 'InternalError', 'Internal Error')
            known_error('TINA-6569', 'Unexpected internal error')

    def test_T1935_set_enable_full_disable(self):
        vpc_id = self.vpc_info_full_disable[info_keys.VPC_ID]
        try:
            self.add_tag(vpc_id, 'osc.fcu.enable_lan_security_groups', '1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.message.startswith('The volume'):
                known_error('TINA-4501', 'Incorrect error message')
            assert False, 'Remove known error code'
            assert_error(error, 400, 'InvalidVpcState', 'The vpc is not in a valid state for this operation: {}.'.format(vpc_id))

    def test_T1936_check_ping_disable(self):
        info = self.vpc_info_full_disable
        stop_instances(self.a1_r1, info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST])
        start_instances(self.a1_r1, info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], state='ready')
        # on subnet ping from instance to another
        self.multi_check_ping(info, True)

    def test_T1937_check_ping_enable_without_rule(self):
        info = self.vpc_info_full_enable
        stop_instances(self.a1_r1, info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST])
        start_instances(self.a1_r1, info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], state='ready')
        # on subnet ping from instance to another
        self.multi_check_ping(info, False)

    def test_T1938_check_ping_enable_with_rule(self):
        ret = None
        info = self.vpc_info_full_enable
        try:
            ret = self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=info[info_keys.SUBNETS][0][info_keys.SECURITY_GROUP_ID],
                                                               IpProtocol='icmp', FromPort=-1, ToPort=-1,
                                                               CidrIp=Configuration.get('cidr', 'allips'))
            stop_instances(self.a1_r1, info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST])
            start_instances(self.a1_r1, info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST], state='ready')
            # on subnet ping from instance to another
            self.multi_check_ping(info, True)
        finally:
            if ret:
                ret = self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=info[info_keys.SUBNETS][0][info_keys.SECURITY_GROUP_ID],
                                                                IpProtocol='icmp', FromPort=-1, ToPort=-1,
                                                                CidrIp=Configuration.get('cidr', 'allips'))

    def test_T1939_check_ping_disable_inst_tag_diff(self):
        info = self.vpc_info_full_disable
        insts = info[info_keys.SUBNETS][0][info_keys.INSTANCE_SET]
        try:
            ret1 = self.add_tag(insts[0]['instanceId'], 'osc.fcu.disable_lan_security_groups', '1')
            ret2 = self.add_tag(insts[1]['instanceId'], 'osc.fcu.disable_lan_security_groups', '2')
            stop_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']])
            start_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']], state='ready')
            self.multi_check_ping(info, True)
        finally:
            if ret1:
                self.delete_tag(insts[0]['instanceId'], 'osc.fcu.enable_lan_security_groups', '1')
            if ret2:
                self.delete_tag(insts[1]['instanceId'], 'osc.fcu.enable_lan_security_groups', '2')

    def test_T1940_check_ping_disable_inst_tag_same(self):
        info = self.vpc_info_full_disable
        insts = info[info_keys.SUBNETS][0][info_keys.INSTANCE_SET]
        try:
            ret1 = self.add_tag(insts[0]['instanceId'], 'osc.fcu.disable_lan_security_groups', '1')
            ret2 = self.add_tag(insts[1]['instanceId'], 'osc.fcu.disable_lan_security_groups', '1')
            stop_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']])
            start_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']], state='ready')
            self.multi_check_ping(info, True)
        finally:
            if ret1:
                self.delete_tag(insts[0]['instanceId'], 'osc.fcu.enable_lan_security_groups', '1')
            if ret2:
                self.delete_tag(insts[1]['instanceId'], 'osc.fcu.enable_lan_security_groups', '1')

    def test_T1941_check_ping_enable_inst_tag_diff(self):
        info = self.vpc_info_full_enable
        insts = info[info_keys.SUBNETS][0][info_keys.INSTANCE_SET]
        try:
            ret1 = self.add_tag(insts[0]['instanceId'], 'osc.fcu.enable_lan_security_groups', '1')
            ret2 = self.add_tag(insts[1]['instanceId'], 'osc.fcu.enable_lan_security_groups', '2')
            stop_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']])
            start_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']], state='ready')
            self.multi_check_ping(info, False)
        finally:
            if ret1:
                self.delete_tag(insts[0]['instanceId'], 'osc.fcu.disable_lan_security_groups', '1')
            if ret2:
                self.delete_tag(insts[1]['instanceId'], 'osc.fcu.disable_lan_security_groups', '2')

    def test_T1942_check_ping_enable_inst_tag_same(self):
        info = self.vpc_info_full_enable
        insts = info[info_keys.SUBNETS][0][info_keys.INSTANCE_SET]
        try:
            ret1 = self.add_tag(insts[0]['instanceId'], 'osc.fcu.enable_lan_security_groups', '1')
            ret2 = self.add_tag(insts[1]['instanceId'], 'osc.fcu.enable_lan_security_groups', '1')
            stop_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']])
            start_instances(self.a1_r1, [insts[0]['instanceId'], insts[1]['instanceId']], state='ready')
            self.multi_check_ping(info, False)
        finally:
            if ret1:
                self.delete_tag(insts[0]['instanceId'], 'osc.fcu.disable_lan_security_groups', '1')
            if ret2:
                self.delete_tag(insts[1]['instanceId'], 'osc.fcu.disable_lan_security_groups', '1')
