from qa_common_tools.config.configuration import Configuration
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_security_groups
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
import string


class Test_AuthorizeSecurityGroupIngress(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.publicGroupId = None
        cls.privateGroupId = None
        cls.vpc_info = None
        super(Test_AuthorizeSecurityGroupIngress, cls).setup_class()
        cls.name = id_generator(prefix='Name_')
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, igw=False, nb_subnet=0)
            cls.publicGroupId = cls.a1_r1.fcu.CreateSecurityGroup(GroupName=cls.name, GroupDescription='Description').response.groupId
            cls.privateGroupId = cls.a1_r1.fcu.CreateSecurityGroup(GroupName=cls.name, GroupDescription='Description',
                                                                   VpcId=cls.vpc_info[VPC_ID]).response.groupId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.publicGroupId:
                cleanup_security_groups(cls.a1_r1, security_group_id_list=[cls.publicGroupId])
            if cls.privateGroupId:
                cleanup_security_groups(cls.a1_r1, security_group_id_list=[cls.privateGroupId])
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_AuthorizeSecurityGroupIngress, cls).teardown_class()

    def test_T577_no_param(self):
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress()
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Either GroupName or GroupId must be specified')

    def test_T578_invalid_group_id_foo(self):
        name_sg = 'foo'
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=name_sg, IpProtocol='tcp', FromPort='42', ToPort='42',
                                                         CidrIp=Configuration.get('cidr', 'allips'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         'Value ({}) for parameter GroupId is invalid. Group ids must be in the format sg-*.'.format(name_sg))

    def test_T579_invalid_group_id_correct_format(self):
        group_id = id_generator(prefix='sg-', size=8, chars=string.digits)
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=group_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group '{}' does not exist.".format(group_id))

    def test_T580_invalid_group_id_incorrect_format(self):
        sg_name = 'T580_{}'.format(id_generator())
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_name, GroupName=sg_name, IpProtocol='tcp', FromPort='42', ToPort='42',
                                                     CidrIp=Configuration.get('cidr', 'allips'))
            sg_id = ret.response.groupId
            sg_id = "{}yyy{}".format(sg_id[:3], sg_id[-8:])
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group '" + sg_id + "' does not exist.")
        finally:
            self.a1_r1.fcu.DeleteSecurityGroup(GroupName=sg_name)

    def test_T961_source_security_group_name(self):
        sg1_name = 'T961_1_{}'.format(id_generator())
        sg2_name = 'T961_2_{}'.format(id_generator())
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg1_name, GroupName=sg1_name)
            sg1_id = ret.response.groupId
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg2_name, GroupName=sg2_name)
            sg2_id = ret.response.groupId
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg2_id, SourceSecurityGroupName=sg1_name)
            ret = self.a1_r1.fcu.DescribeSecurityGroups(GroupId=[sg2_id])
            # ICMP
            assert ret.response.securityGroupInfo[0].ipPermissions[0].groups[0].groupId == sg1_id
            # TCP
            assert ret.response.securityGroupInfo[0].ipPermissions[1].groups[0].groupId == sg1_id
            # UDP
            assert ret.response.securityGroupInfo[0].ipPermissions[2].groups[0].groupId == sg1_id
        finally:
            self.a1_r1.fcu.DeleteSecurityGroup(GroupName=sg2_name)
            self.a1_r1.fcu.DeleteSecurityGroup(GroupName=sg1_name)

    def test_T1300_source_sg_owner_id_and_group_id(self):
        sg1_name = 'T962_1_{}'.format(id_generator())
        sg2_name = 'T962_2_{}'.format(id_generator())
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg1_name, GroupName=sg1_name)
            ret = self.a2_r1.fcu.CreateSecurityGroup(GroupDescription=sg2_name, GroupName=sg2_name)
            sg2_id = ret.response.groupId
            ret = self.a2_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg2_id,
                                                               SourceSecurityGroupOwnerId=self.a1_r1.config.account.account_id,
                                                               SourceSecurityGroupName=sg1_name)
        finally:
            self.a2_r1.fcu.DeleteSecurityGroup(GroupName=sg2_name)
            self.a1_r1.fcu.DeleteSecurityGroup(GroupName=sg1_name)

    def test_T962_source_sg_owner_id(self):
        sg1_name = 'T962_1_{}'.format(id_generator())
        sg2_name = 'T962_2_{}'.format(id_generator())
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg1_name, GroupName=sg1_name)
            ret = self.a2_r1.fcu.CreateSecurityGroup(GroupDescription=sg2_name, GroupName=sg2_name)
            sg2_id = ret.response.groupId
            ret = self.a2_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=sg2_id, SourceSecurityGroupOwnerId=self.a1_r1.config.account.account_id)
        except OscApiException as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', 'IpProtocol, IpPermissions or SourceSecurityGroupName is missing')
        finally:
            self.a2_r1.fcu.DeleteSecurityGroup(GroupName=sg2_name)
            self.a1_r1.fcu.DeleteSecurityGroup(GroupName=sg1_name)

    def test_T1408_valid_ipv6_address_format_inbound(self):
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.publicGroupId,
                                                         IpPermissions=[{'IpProtocol': 'icmp',
                                                                         'Ipv6Ranges': [{'CidrIpv6': Configuration.get('ipv6', 'ipv6.1')}]}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This option is not yet implemented: Ipv6Ranges')

    def test_T1412_public_no_ip_protocol_param(self):
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.publicGroupId, FromPort='42', ToPort='42',
                                                         CidrIp=Configuration.get('cidr', 'allips'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', "IpProtocol, IpPermissions or SourceSecurityGroupName is missing")

    def test_T3046_private_no_ip_protocol_param(self):
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.privateGroupId, FromPort='42', ToPort='42',
                                                         CidrIp=Configuration.get('cidr', 'allips'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', "IpProtocol, IpPermissions or SourceSecurityGroupName is missing")

    def test_T2987_valid_group_name(self):
        try:
            sg_name = id_generator(prefix='sg_name')
            vpc_id = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16')).response.vpc.vpcId
            subnet_id = self.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=vpc_id).response.subnet.subnetId
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name, VpcId=vpc_id).response.groupId
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=sg_name, IpProtocol='tcp', FromPort=22, ToPort=22,
                                                         CidrIp=Configuration.get('cidr', 'allips'))
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'InvalidGroup.NotFound':
                known_error('TINA-4771', 'AuthorizeSecurityGroupIngress with group name --> error and incorrect message')
            assert False, 'Remove known error code'
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pass
            if subnet_id:
                try:
                    self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)
                except Exception:
                    pass
            if vpc_id:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
                except Exception:
                    pass

    def test_T3026_valid_group_name_without_vpc(self):
        try:
            sg_name = id_generator(prefix='sg_name')
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name).response.groupId
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=sg_name, IpProtocol='tcp', FromPort=22, ToPort=22,
                                                         CidrIp=Configuration.get('cidr', 'allips'))
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pass

    def test_T3043_invalid_port_range_minus_1_to_8(self):
        try:
            sg_name = id_generator(prefix='sg_name')
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name).response.groupId
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=sg_name, IpProtocol='icmp', FromPort=-1, ToPort=8,
                                                         CidrIp=Configuration.get('cidr', 'allips'))
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', 'Wildcard ICMP type MUST have wildcard ICMP code')
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pass

    def test_T3044_invalid_port_range_8_to_minus_1(self):
        try:
            sg_name = id_generator(prefix='sg_name')
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name).response.groupId
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=sg_name, IpProtocol='icmp', FromPort=8, ToPort=-1,
                                                         CidrIp=Configuration.get('cidr', 'allips'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Start/End ports must be in valid int range')
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pass

    def test_T3045_invalid_port_range_minus_9_to_8(self):
        sg_id = None
        try:
            sg_name = id_generator(prefix='sg_name')
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name).response.groupId
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupName=sg_name, IpProtocol='icmp', FromPort=9, ToPort=8,
                                                         CidrIp=Configuration.get('cidr', 'allips'))
            assert False, 'Call should not have been successful'
        except Exception as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Start/End ports must be in valid int range')
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pass

    def test_T3231_ippermissions_missing_ipprotocol(self):
        self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.publicGroupId,
                                                     IpPermissions=[{'FromPort': 1,
                                                                     'ToPort': 65535,
                                                                     'IpRanges': [{'CidrIp': '46.231.147.8/32'}]}])

    def test_T3232_ippermissions_missing_fromport(self):
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.publicGroupId,
                                                         IpPermissions=[{'IpProtocol': 'tcp',
                                                                         'ToPort': 65535,
                                                                         'IpRanges': [{'CidrIp': '46.231.147.8/32'}]}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', 'TCP/UDP port (-1) out of range')

    def test_T3233_ippermissions_missing_toport(self):
        try:
            self.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=self.publicGroupId,
                                                         IpPermissions=[{'IpProtocol': 'tcp',
                                                                         'FromPort': 1,
                                                                         'IpRanges': [{'CidrIp': '46.231.147.8/32'}]}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidPermission.Malformed', 'TCP/UDP port (-1) out of range')
