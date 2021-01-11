from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_common.objects.osc_objects import OscObjectXml
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNETS, SECURITY_GROUP_ID
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_security_groups
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID


def to_dict(val_to_dict):
    if type(val_to_dict) is list:
        return [to_dict(elem) for elem in val_to_dict]
    elif isinstance(val_to_dict, OscObjectXml):
        ret_dict = {}
        for key in list(val_to_dict.__dict__.keys()):
            if key.startswith('_') or key == 'groupName':
                continue
            new_key = key[:1].upper() + key[1:]
            ret_dict[new_key] = to_dict(val_to_dict.__dict__[key])
        return ret_dict
    else:
        return val_to_dict


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

    def test_T5360_with_default_and_non_default_sg(self):
        self.vpc1_info = None
        try:
            self.vpc1_info = create_vpc(self.a1_r1, no_eip=True, nb_instance=1 , cidr_prefix="172.16", igw=False, default_rtb=False, state='running')
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.vpc1_info[SUBNETS][0][SECURITY_GROUP_ID], IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp='10.0.0.0/16')
            ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'vpc-id', 'Value': self.vpc1_info[VPC_ID]}])
            if ret.response.securityGroupInfo:
                for group in ret.response.securityGroupInfo:
                    if group.groupName == "default":
                        # delete all rules
                        if group.ipPermissions:
                            permList = [to_dict(perm) for perm in group.ipPermissions]
                            self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=group.groupId, IpPermissions=permList)
                        continue
        finally:
            if self.vpc1_info:
                delete_vpc(self.a1_r1, self.vpc1_info)

    def test_T5361_with_invalid_sg(self):
        try:
            self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId='sg-xxxxx')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'sg-xxxxx' does not exist.")

    def test_T5362_with_invalid_IpProtocol(self):
        try:
            self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=self.groupId, IpPermissions=[{'IpProtocol': '30', 'IpRanges': None, 'PrefixListIds': None}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', 'Unsupported IP protocol "30"  - supported: [tcp, udp, icmp]')

    def test_T5363_with_invalid_IpRanges(self):
        try:
            self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=self.groupId, IpPermissions=[{'IpRanges': [{'CidrIp': 'X.X.X.X/32'}]}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', "Invalid IP range: 'X.X.X.X/32'")
