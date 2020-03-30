from qa_test_tools.config.configuration import Configuration
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_security_groups


class Test_RevokeSecurityGroupIngress(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RevokeSecurityGroupIngress, cls).setup_class()
        cls.sg = None
        cls.name = id_generator(prefix='Name_')
        ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupName=cls.name, GroupDescription='Description')
        cls.groupId = ret.response.groupId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.groupId:
                cleanup_security_groups(cls.a1_r1, security_group_id_list=[cls.groupId])
        finally:
            super(Test_RevokeSecurityGroupIngress, cls).teardown_class()

    def test_T1411_valid_ipv6_address_format_inbound_revoke(self):
        try:
            self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=self.groupId,
                                                      IpPermissions=[{'IpProtocol': 'icmp',
                                                                      'Ipv6Ranges': [{'CidrIpv6': Configuration.get('ipv6', 'ipv6.1')}]}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: Ipv6Ranges')
