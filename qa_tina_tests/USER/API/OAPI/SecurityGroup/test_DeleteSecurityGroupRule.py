# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import SecurityGroup, validate_sg


class Test_DeleteSecurityGroupRule(SecurityGroup):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteSecurityGroupRule, cls).setup_class()
        try:
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=cls.sg1['name'],
                SecurityGroupAccountIdToLink=cls.a1_r1.config.account.account_id,
                SecurityGroupId=cls.sg1['id'])
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg2['id'])
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='udp',
                FromPortRange=4578,
                ToPortRange=4679,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg1['id'])
            # cls.a1_r1.oapi.CreateSecurityGroupRule(
            #     Flow='Inbound',
            #     Rules=[
            #         {
            #             'IpProtocol': 'icmp',
            #             'FromPortRange': -1,
            #             'ToPortRange': -1,
            #             'IpRanges': ['10.0.0.12/32']
            #         },
            #         {
            #             'SecurityGroupsMembers': [{
            #                 'AccountId': cls.a1_r1.config.account.account_id,
            #                 'Name': cls.sg1['name'],
            #             }],
            #             'IpProtocol': 'tcp',
            #             'FromPortRange': 45,
            #             'ToPortRange': 4609,
            #             'IpRanges': ['10.0.0.12/32']}],
            #     SecurityGroupId=cls.sg1['id'])
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg2['id'])
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                Rules=[
                    {
                        'IpProtocol': 'icmp',
                        'FromPortRange':-1,
                        'ToPortRange':-1,
                        'IpRanges': ['10.0.0.12/32']
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPortRange': 45,
                        'ToPortRange': 4609,
                        'IpRanges': ['10.0.0.12/32']
                    }],
                SecurityGroupId=cls.sg3['id'])
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    def test_T2737_without_param(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2738_missing_id(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                FromPortRange=1234,
                IpProtocol='tcp',
                IpRange='10.0.0.12/32',
                ToPortRange=1234,
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                FromPortRange=1234,
                IpProtocol='tcp',
                IpRange='10.0.0.12/32',
                ToPortRange=1234,
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2739_valid_case_inbound(self):
        sg = self.a1_r1.oapi.DeleteSecurityGroupRule(
            Flow='Inbound',
            IpProtocol='tcp',
            FromPortRange=1234,
            ToPortRange=1234,
            IpRange='10.0.0.12/32',
            SecurityGroupId=self.sg1['id']).response.SecurityGroup
        validate_sg(sg)

    def test_T2740_valid_case_outbound(self):
        sg = self.a1_r1.oapi.DeleteSecurityGroupRule(
            Flow='Outbound',
            IpProtocol='tcp',
            FromPortRange=1234,
            ToPortRange=1234,
            IpRange='10.0.0.12/32',
            SecurityGroupId=self.sg2['id']).response.SecurityGroup
        validate_sg(sg)

    def test_T2741_with_sg_to_unlink_param(self):
        sg = self.a1_r1.oapi.DeleteSecurityGroupRule(
            Flow='Outbound',
            SecurityGroupNameToUnlink=self.sg2['name'],
            SecurityGroupAccountIdToUnlink=self.a1_r1.config.account.account_id,
            SecurityGroupId=self.sg2['id']).response.SecurityGroup
        validate_sg(sg)
        sg = self.a1_r1.oapi.DeleteSecurityGroupRule(
            Flow='Inbound',
            SecurityGroupNameToUnlink=self.sg1['name'],
            SecurityGroupAccountIdToUnlink=self.a1_r1.config.account.account_id,
            SecurityGroupId=self.sg1['id']).response.SecurityGroup
        validate_sg(sg)

    def test_T2742_invalid_ip_range(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='Hello',
                SecurityGroupId=self.sg2['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='Hello',
                SecurityGroupId=self.sg1['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2743_unknown_protocol(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='new_protocol',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg2['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='new_protocol',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2744_invalid_port_range_inbound(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg2['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T3003_invalid_port_range_outbound(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2745_outbound_rules_without_net(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8004')

    def test_T2746_missing_port_spec(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='Hello', Rules=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPortRange': 1234,
                        'ToPortRange': 1235,
                        'IpRanges': ['10.0.0.12/32'],
                    }],
                SecurityGroupId=self.sg1['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                Rules=[
                    {
                        'IpProtocol': 'icmp',
                        'FromPortRange':-1,
                        'ToPortRange':-1,
                        'IpRanges': ['10.0.0.12/32']
                    },
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupId': self.sg1['id'],
                            'Name': self.sg1['name'],
                        }],
                        'IpProtocol': 'udp',
                        'FromPortRange': 45,
                        'ToPortRange': 60,
                        'IpRanges': ['10.0.0.12/32']}],
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                Rules=[
                    {
                        'IpProtocol': 'icmp',
                        'FromPortRange':-1,
                        'ToPortRange':-1,
                        'IpRanges': ['10.0.0.12/32']
                    },
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupId': self.sg2['id'],
                            'Name': self.sg2['name'],
                        }],
                        'IpProtocol': 'udp',
                        'FromPortRange': 45,
                        'ToPortRange': 60,
                        'IpRanges': ['10.0.0.12/32']}],
                SecurityGroupId=self.sg2['id'])

            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='Hello',
                Rules=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPortRange': 1234,
                        'ToPortRange': 1235,
                        'IpRanges': ['10.0.0.12/32'],
                    }],
                SecurityGroupId=self.sg2['id']
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2747_inbound_rules_array_1_element(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                Rules=[
                    {
                        'SecurityGroupsMembers': [{
                            "AccountId": self.a1_r1.config.account.account_id,
                            "SecurityGroupName": self.sg1['name'],
                        }],
                        'IpProtocol': "tcp",
                        'FromPortRange': 45,
                        'ToPortRange': 7890,
                        'IpRanges': ["10.0.0.12/32"]}],
                SecurityGroupId=self.sg1['id'])
        except OscApiException as error:
            assert_oapi_error(error, 400, 'DefaultError', '0')

    def test_T2748_rules_array_single_element(self):
        self.a1_r1.oapi.DeleteSecurityGroupRule(
            Flow='Inbound',
            Rules=[
                {
                    'SecurityGroupsMembers': [{
                        'AccountId': self.a1_r1.config.account.account_id,
                        'SecurityGroupName': self.sg1['name'],
                    }],
                    'IpProtocol': "icmp",
                    'FromPortRange':-1,
                    'ToPortRange':-1,
                    'IpRanges': ["10.0.0.12/32"]}],
            SecurityGroupId=self.sg1['id'])

    def test_T2749_rules_array_many_element(self):
        self.a1_r1.oapi.DeleteSecurityGroupRule(
            Flow='Inbound',
            Rules=[
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 1234,
                    'ToPortRange': 1235,
                    'IpRanges': ['10.0.0.12/32'],
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 4325,
                    'ToPortRange': 6587,
                    'IpRanges': ['10.0.0.12/32'],
                }
            ],
            SecurityGroupId=self.sg3['id'])

        self.a1_r1.oapi.DeleteSecurityGroupRule(
            Flow='Inbound',
            Rules=[
                {
                    'IpProtocol': 'icmp',
                    'FromPortRange':-1,
                    'ToPortRange':-1,
                    'IpRanges': ['10.0.0.12/32']
                },
                {
                    'SecurityGroupsMembers': [{
                        'AccountId': self.a1_r1.config.account.account_id,
                        'SecurityGroupId': self.sg1['id'],
                    }],
                    'IpProtocol': 'udp',
                    'FromPortRange': 56,
                    'ToPortRange': 78,
                    'IpRanges': ['10.0.0.12/32']
                }
            ],
            SecurityGroupId=self.sg1['id'])

    @pytest.mark.tag_sec_confidentiality
    def test_T3532_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5020')
