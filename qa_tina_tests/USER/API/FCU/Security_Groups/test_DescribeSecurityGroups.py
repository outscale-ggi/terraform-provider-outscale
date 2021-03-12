
import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException, OscSdkException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.create_tools import create_security_group, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_security_group, delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID

# attention priv > pub >= 2 otherwise it won't work
NB_PUB_SG = 2
NB_PRIV_SG = 4


class Test_DescribeSecurityGroups(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeSecurityGroups, cls).setup_class()
        cls.pub_sg_ids = []
        cls.priv_sg_ids = []
        cls.vpc_info = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
            cls.sg_names = []
            for _ in range(max(NB_PUB_SG, NB_PRIV_SG)):
                cls.sg_names.append(id_generator(prefix='sgname', chars=string.digits))
            for i in range(NB_PUB_SG):
                cls.pub_sg_ids.append(create_security_group(cls.a1_r1, name=cls.sg_names[i], desc="desc{}".format(i + 1)))
            for i in range(NB_PRIV_SG):
                cls.priv_sg_ids.append(create_security_group(cls.a1_r1, name=cls.sg_names[i], desc="desc{}".format(i + 1),
                                                             vpc_id=cls.vpc_info[info_keys.VPC_ID]))
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.pub_sg_ids[0], SourceSecurityGroupName=cls.sg_names[1])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            cls.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=cls.pub_sg_ids[0], SourceSecurityGroupName=cls.sg_names[1])
            for sg_id in cls.pub_sg_ids:
                delete_security_group(cls.a1_r1, sg_id)
            for sg_id in cls.priv_sg_ids:
                delete_security_group(cls.a1_r1, sg_id)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DescribeSecurityGroups, cls).teardown_class()

    def test_T3184_with_other_account(self):
        try:
            self.a2_r1.fcu.DescribeSecurityGroups(GroupId=[self.pub_sg_ids[0]])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.NotFound", "The security group '{}' does not exist".format(self.pub_sg_ids[0]))

    def test_T5398_no_params(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups()
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG + NB_PRIV_SG + 1 + 1
        try:
            ret.check_response()
            assert False, 'Remove known error'
        except OscSdkException:
            known_error('API-156', 'incorrect response structure')

    def test_T5399_with_invalid_group_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=['toto'])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'toto' does not exist")

    def test_T5400_with_nonexisting_group_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=['sg-12345678'])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'sg-12345678' does not exist")

    def test_T5401_with_invalid_group_id_type(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.pub_sg_ids[0])
            known_error('TINA-6073', "GroupId should be a list")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, '', None)

    def test_T5402_with_public_group_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.pub_sg_ids)
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG

    def test_T5403_with_private_group_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.priv_sg_ids)
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == NB_PRIV_SG

    def test_T5404_with_mixed_group_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupId=[self.pub_sg_ids[0], self.priv_sg_ids[0]])
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == 2

    def test_T5405_with_nonexisting_group_name(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=['foobar'])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'foobar' does not exist")

    def test_T5406_with_invalid_group_name_type(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names[0])
            known_error('TINA-6073', "GroupName should be a list")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, '', None)

    def test_T5407_with_public_group_name(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names[0:NB_PUB_SG])
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG

    def test_T5408_with_private_group_name(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names[NB_PUB_SG:NB_PUB_SG + NB_PRIV_SG])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.NotFound", None)

    def test_T5409_with_mixed_group_name(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 500, "InternalError", None)
            known_error('TINA-6072', 'Unexpected internal error')
            assert_error(error, 400, "InvalidGroup.NotFound", None)

    def test_T5410_with_public_group_name_and_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.pub_sg_ids, GroupName=self.sg_names[0:1])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 500, "InternalError", None)
            known_error('TINA-6072', 'Unexpected internal error')
            assert_error(error, 400, "InvalidGroup.NotFound", None)

    def test_T5411_with_private_group_name_and_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.priv_sg_ids, GroupName=self.sg_names[NB_PUB_SG:NB_PRIV_SG])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.NotFound", None)

    def test_T5412_with_mixed_group_name_and_id(self):
        ids = []
        ids.extend(self.pub_sg_ids)
        ids.extend(self.priv_sg_ids)
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=ids, GroupName=self.sg_names)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 500, "InternalError", None)
            known_error('TINA-6072', 'Unexpected internal error')
            assert_error(error, 400, "InvalidGroup.NotFound", None)

    # filters (from documentation)
    # description: The description of the security group.
    # group-id: The ID of the security group.
    # group-name: The name of the security group.
    # ip-permission.cidr: A CIDR range that has been granted permission.
    # ip-permission.from-port: The beginning of the port range for the TCP and UDP protocols, or an ICMP type number.
    # ip-permission.group-id: The ID of a security group that has been granted permission.
    # ip-permission.group-name: The name of a security group that has been granted permission.
    # ip-permission.protocol: The IP protocol for the permission (tcp | udp | icmp, or a protocol number, or -1 for all protocols).
    # ip-permission.to-port: The end of the port range for the TCP and UDP protocols, or an ICMP code.
    # ip-permission.user-id: The account ID of a user that has been granted permission.
    # owner-id: The account ID of the owner of the security group.
    # tag-key: The key of a tag associated with the resource. WILL NOT BE TESTED HERE
    # tag-value: The value of a tag associated with the resource. WILL NOT BE TESTED HERE
    # tag:XXXX: The value of a tag associated with the resource, where XXXX is the key of the tag. WILL NOT BE TESTED HERE
    # vpc-id: The ID of the VPC specified when the security group was created.

    def test_T5413_filter_description(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'description', 'Value': ['desc1']}])
        assert len(ret.response.securityGroupInfo) == 2
        for sg_info in ret.response.securityGroupInfo:
            assert sg_info.groupDescription == 'desc1'

    def test_T5414_filter_group_id_public(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'group-id', 'Value': self.pub_sg_ids}])
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG

    def test_T5415_filter_group_id_private(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'group-id', 'Value': self.priv_sg_ids}])
        assert len(ret.response.securityGroupInfo) == NB_PRIV_SG

    def test_T5416_filter_group_name(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'group-name', 'Value': self.sg_names}])
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG + NB_PRIV_SG

    def test_T5417_filter_ip_permission_cidr(self):
        cidr_range = '11.22.33.44/32'
        protocol = 'tcp'
        to_port = 65535
        from_port = 1
        self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.priv_sg_ids[0],
                                                     IpPermissions=[{'IpProtocol': protocol,
                                                                     'ToPort': to_port, 'FromPort': from_port,
                                                                     'IpRanges': [{'CidrIp': cidr_range}]}])
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'ip-permission.cidr', 'Value': [cidr_range]}])
        assert len(ret.response.securityGroupInfo) == 1
        found = 0
        for perm in ret.response.securityGroupInfo[0].ipPermissions:
            if perm.ipRanges[0].cidrIp == cidr_range:
                assert perm.ipProtocol == protocol
                assert perm.fromPort == str(from_port)
                assert perm.toPort == str(to_port)
                found += 1
        assert found == 1, 'Could not find rule'

    def test_T5418_filter_ip_permission_group_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'ip-permission.group-id', 'Value': [self.pub_sg_ids[1]]}])
        assert len(ret.response.securityGroupInfo) == 1
        for sg_info in ret.response.securityGroupInfo:
            assert sg_info.groupId == self.pub_sg_ids[0]
            assert sg_info.groupName == self.sg_names[0]
            for perm in sg_info.ipPermissions:
                if getattr(perm, 'groups') is not None:
                    for group in perm.groups:
                        assert group.groupId == self.pub_sg_ids[1]
                        assert group.groupName == self.sg_names[1]
                        assert group.userId == self.a1_r1.config.account.account_id

    def test_T5419_filter_ip_permission_group_name(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'ip-permission.group-name', 'Value': [self.sg_names[1]]}])
        assert len(ret.response.securityGroupInfo) == 1
        for sg_info in ret.response.securityGroupInfo:
            assert sg_info.groupId == self.pub_sg_ids[0]
            assert sg_info.groupName == self.sg_names[0]
            for perm in sg_info.ipPermissions:
                if getattr(perm, 'groups') is not None:
                    for group in perm.groups:
                        assert group.groupId == self.pub_sg_ids[1]
                        assert group.groupName == self.sg_names[1]
                        assert group.userId == self.a1_r1.config.account.account_id

    def test_T5426_filter_ip_permission_protocol(self):
        protocol = 'tcp'
        ret = self.a1_r1.fcu.DescribeSecurityGroups(
            Filter=[{'Name': 'ip-permission.protocol', 'Value': [protocol]}])
        for sg_info in ret.response.securityGroupInfo:
            found = False
            for perm in sg_info.ipPermissions:
                if hasattr(perm, 'ipProtocol') and perm.ipProtocol == protocol:
                    found = True
                    break
            assert found

    def test_T5420_filter_ip_permission_to_port(self):
        to_port = '22'
        ret = self.a1_r1.fcu.DescribeSecurityGroups(
            Filter=[{'Name': 'ip-permission.to-port', 'Value': [to_port]}])
        for sg_info in ret.response.securityGroupInfo:
            found = False
            for perm in sg_info.ipPermissions:
                if hasattr(perm, 'toPort') and perm.toPort == to_port:
                    found = True
                    break
            assert found

    def test_T5421_filter_ip_permission_user_id(self):
        sg2_name = id_generator(prefix='sg2_name', chars=string.digits)
        try:
            sg2_id = create_security_group(self.a2_r1, name=sg2_name, desc=sg2_name)
            for sg_id in self.pub_sg_ids:
                self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg_id,
                                                             SourceSecurityGroupOwnerId=self.a2_r1.config.account.account_id,
                                                             SourceSecurityGroupName=sg2_name)
            user_id = self.a2_r1.config.account.account_id
            ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'ip-permission.user-id', 'Value': [user_id]}])
            assert len(ret.response.securityGroupInfo) == NB_PUB_SG
            for sg_info in ret.response.securityGroupInfo:
                for perm in sg_info.ipPermissions:
                    if hasattr(perm, 'groups') and getattr(perm, 'groups') is not None:
                        for group in perm.groups:
                            if hasattr(group, 'groupName') and group.groupName == sg2_name:
                                assert hasattr(group, 'userId') and group.userId == user_id
        finally:
            for sg_id in self.pub_sg_ids:
                self.a1_r1.fcu.RevokeSecurityGroupIngress(GroupId=sg_id,
                                                          SourceSecurityGroupOwnerId=self.a2_r1.config.account.account_id,
                                                          SourceSecurityGroupName=sg2_name)
            if sg2_id:
                delete_security_group(self.a2_r1, sg2_id)

    def test_T5422_filter_owner_id(self):
        account_id = self.a1_r1.config.account.account_id
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'owner-id', 'Value': [account_id]}])
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG + NB_PRIV_SG + 1 + 1
        for i in range(max(NB_PUB_SG, NB_PRIV_SG)):
            assert account_id == ret.response.securityGroupInfo[i].ownerId

    def test_T5423_filter_vpc_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'vpc-id', 'Value': [self.vpc_info[VPC_ID]]}])
        assert len(ret.response.securityGroupInfo) == NB_PRIV_SG + 1
        for sg in ret.response.securityGroupInfo:
            assert sg.vpcId == self.vpc_info[VPC_ID]

    def test_T5424_filter_description_nonexistent(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'description', 'Value': ['xxx']}])
        assert ret.response.securityGroupInfo is None

    def test_T5425_filter_description_invalid_type(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'description', 'Value': 'desc1'}])
            known_error('TINA-6117', "the Value should be a list")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, '', None)
