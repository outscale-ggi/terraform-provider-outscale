# pylint: disable=missing-docstring

import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.create_tools import create_security_group, \
    create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_security_group, \
    delete_vpc


# attention priv > pub otherwise it won't work
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
            cls.sg_names= []
            for _ in range(max(NB_PUB_SG, NB_PRIV_SG)):
                cls.sg_names.append(id_generator(prefix='sgname', chars=string.digits))
            for i in range(NB_PUB_SG):
                cls.pub_sg_ids.append(create_security_group(cls.a1_r1, name=cls.sg_names[i], desc="desc{}".format(i+1)))
            for i in range(NB_PRIV_SG):
                cls.priv_sg_ids.append(create_security_group(cls.a1_r1, name=cls.sg_names[i], desc="desc{}".format(i+1), vpc_id=cls.vpc_info[info_keys.VPC_ID]))
            
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
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
            
    def test_TXXX_no_params(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups()
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG + NB_PRIV_SG + 1 + 1
        try:
            ret.check_response()
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-156', 'incorrect response structure')
 
    def test_TXXX_with_invalid_group_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=['toto'])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'toto' does not exist")

    def test_TXXX_with_nonexisting_group_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=['sg-12345678'])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'sg-12345678' does not exist")

    def test_TXXX_with_invalid_group_id_type(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.pub_sg_ids[0])
            known_error('TINA-6073', "GroupId should be a list")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, '', None)

    def test_TXXX_with_public_group_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.pub_sg_ids)
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG
  
    def test_TXXX_with_private_group_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.priv_sg_ids)
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == NB_PRIV_SG
  
    def test_TXXX_with_mixed_group_id(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupId=[self.pub_sg_ids[0], self.priv_sg_ids[0]])
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == 2
  
    def test_TXXX_with_nonexisting_group_name(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=['foobar'])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'foobar' does not exist")

    def test_TXXX_with_invalid_group_name_type(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names[0])
            known_error('TINA-6073', "GroupName should be a list")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert False, "remove known error code"
            assert_error(error, 400, '', None)

    def test_TXXX_with_public_group_name(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names[0:NB_PUB_SG])
        # ret.check_response()
        assert len(ret.response.securityGroupInfo) == NB_PUB_SG
  
    def test_TXXX_with_private_group_name(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names[NB_PUB_SG:NB_PUB_SG+NB_PRIV_SG])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.NotFound", None)
          
    def test_TXXX_with_mixed_group_name(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupName=self.sg_names)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 500, "InternalError", None)
            known_error('TINA-6072', 'Unexpected internal error')
            assert_error(error, 400, "InvalidGroup.NotFound", None)
  
    def test_TXXX_with_public_group_name_and_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.pub_sg_ids, GroupName=self.sg_names[0:1])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 500, "InternalError", None)
            known_error('TINA-6072', 'Unexpected internal error')
            assert_error(error, 400, "InvalidGroup.NotFound", None)
  
    def test_TXXX_with_private_group_name_and_id(self):
        try:
            self.a1_r1.fcu.DescribeSecurityGroups(GroupId=self.priv_sg_ids, GroupName=self.sg_names[NB_PUB_SG:NB_PRIV_SG])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.NotFound", None)
  
    def test_TXXX_with_mixed_group_name_and_id(self):
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
    
    def test_TXXX_filter_description(self):
        ret = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'description', 'Value': ['desc1', 'desc2']}])
        assert len(ret.response.securityGroupInfo) == 4
