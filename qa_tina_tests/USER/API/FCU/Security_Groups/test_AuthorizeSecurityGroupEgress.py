from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_security_groups


class Test_AuthorizeSecurityGroupEgress(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AuthorizeSecurityGroupEgress, cls).setup_class()
        cls.sg = None
        cls.name = id_generator(prefix='Name_')
        try:
            ret = cls.a1_r1.fcu.CreateSecurityGroup(GroupName=cls.name, GroupDescription='Description')
            cls.groupId = ret.response.groupId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.groupId:
                cleanup_security_groups(cls.a1_r1, security_group_id_list=[cls.groupId])
        finally:
            super(Test_AuthorizeSecurityGroupEgress, cls).teardown_class()

    # TODO redefine later
    # def test_T952_default_tcp(self):
    #    self.a1_r1.fcu.AuthorizeSecurityGroupEgress(FromPort=101, ToPort=101, IpProtocol='tcp', CidrIp=Configuration.get('ipaddress', 'sg_ip_1'))

    def test_T1407_valid_ipv6_address_format_outbound(self):
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupEgress(GroupId=self.groupId,
                                                        IpPermissions=[{'IpProtocol': 'icmp',
                                                                        'Ipv6Ranges': [{'CidrIpv6': Configuration.get('ipv6', 'ipv6.1')}]}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: Ipv6Ranges')
