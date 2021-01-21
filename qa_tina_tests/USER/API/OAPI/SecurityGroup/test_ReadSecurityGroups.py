# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.compare_objects import verify_response
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import SecurityGroup, validate_sg
import os
from qa_tina_tools.tools.tina.info_keys import VPC_ID


class Test_ReadSecurityGroups(SecurityGroup):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSecurityGroups, cls).setup_class()
        try:
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=cls.sg1.SecurityGroupName,
                SecurityGroupAccountIdToLink=cls.a1_r1.config.account.account_id,
                SecurityGroupId=cls.sg1.SecurityGroupId)
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='udp',
                FromPortRange=1,
                ToPortRange=535,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg1.SecurityGroupId)
            cls.a1_r1.oapi.CreateSecurityGroupRule(
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
                            'SecurityGroupId': cls.sg1.SecurityGroupId,
                        }],
                        'IpProtocol': 'tcp',
                        'FromPortRange': 45,
                        'ToPortRange': 4609,
                        'IpRanges': ['10.0.0.12/32']
                    }
                ],
                SecurityGroupId=cls.sg1.SecurityGroupId)
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg2.SecurityGroupId)
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.sg1.SecurityGroupId], Tags=[{'Key': 'sg_key', 'Value': 'sg_value'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.sg2.SecurityGroupId], Tags=[{'Key': 'sg_key', 'Value': 'sg_toto'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.sg3.SecurityGroupId], Tags=[{'Key': 'sg_toto', 'Value': 'sg_value'}])

            cls.hints = {'AccountId' : cls.a1_r1.config.account.account_id}
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

# filters
#       "AccountIds": ["string"],
#       "Descriptions": ["string"],
#       "InboundRuleAccountIds": ["string"],
#       "InboundRuleFromPortRanges": [int],
#       "InboundRuleIpRanges": ["string"],
#       "InboundRuleProtocols": ["string"],
#       "InboundRuleSecurityGroupIds": ["string"],
#       "InboundRuleSecurityGroupNames": ["string"],
#       "InboundRuleToPortRanges": [int],
#       "NetIds": ["string"],
#       "OutboundRuleAccountIds": ["string"],
#       "OutboundRuleFromPortRanges": [int],
#       "OutboundRuleIpRanges": ["string"],
#       "OutboundRuleProtocols": ["string"],
#       "OutboundRuleSecurityGroupIds": ["string"],
#       "OutboundRuleSecurityGroupNames": ["string"],
#       "OutboundRuleToPortRanges": [int],
#       "SecurityGroupIds": ["string"],
#       "SecurityGroupNames": ["string"],
#       "TagKeys": ["string"],
#       "TagValues": ["string"],
#       "Tags": ["string"]

    def test_T2750_empty_filters(self):
        ret = self.a1_r1.oapi.ReadSecurityGroups().response
        assert verify_response(ret, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'empty_filters.json'), self.hints), 'Could not verify response content.'

    def test_T2751_filters_account_ids(self):
        filters = {'AccountIds': [self.a1_r1.config.account.account_id]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert verify_response(ret, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filters_account_ids.json'), self.hints), 'Could not verify response content.'

    def test_T2752_filters_sg_id1(self):
        filters = {'SecurityGroupIds': [self.sg1.SecurityGroupId]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg1.SecurityGroupId,
                'Description': 'test_desc',
                'SecurityGroupName': self.sg1.SecurityGroupName},
            in_rules=[
                {
                    'IpProtocol': 'icmp',
                    'FromPortRange':-1,
                    'IpRanges': ['10.0.0.12/32'],
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1.SecurityGroupId,
                        'SecurityGroupName': self.sg1.SecurityGroupName,
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange':-1,
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 45,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1.SecurityGroupId,
                        'SecurityGroupName': self.sg1.SecurityGroupName,
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 4609,
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 0,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1.SecurityGroupId,
                        'SecurityGroupName': self.sg1.SecurityGroupName,
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 65535,
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 0,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1.SecurityGroupId,
                        'SecurityGroupName': self.sg1.SecurityGroupName,
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 65535,
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 0,
                    'IpRanges': ['10.0.0.12/32'],
                    'ToPortRange': 535,
                }
            ]
        )

    def test_T2753_filters_sg_rule_set_id2(self):
        filters = {'SecurityGroupIds': [self.sg2.SecurityGroupId]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg2.SecurityGroupId,
                'Description': 'test_desc',
                'SecurityGroupName': self.sg2.SecurityGroupName},
            out_rules=[{
                'IpProtocol': 'tcp', 'FromPortRange': 1234,
                'ToPortRange': 1234, 'IpRanges': ['10.0.0.12/32'],
            },
                {
                    'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
            }], net_id=self.vpc_info[VPC_ID])

    def test_T2754_filters_sg_rule_set_id3(self):
        filters = {'SecurityGroupIds': [self.sg3.SecurityGroupId]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg3.SecurityGroupId,
                'Description': 'test_desc',
                'SecurityGroupName': self.sg3.SecurityGroupName,
                'NetId': self.vpc_info[VPC_ID],
            },
            out_rules=[{
                'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
            }])

    def test_T2755_filters_sg_rule_set_name3(self):
        filters = {'SecurityGroupNames': [self.sg3.SecurityGroupName]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg3.SecurityGroupId,
                'Description': 'test_desc',
                'SecurityGroupName': self.sg3.SecurityGroupName,
                'NetId': self.vpc_info[VPC_ID],
            },
            out_rules=[{
                'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
            }])

    @pytest.mark.tag_sec_confidentiality
    def test_T3417_with_other_account(self):
        ret = self.a2_r1.oapi.ReadSecurityGroups().response.SecurityGroups
        assert len(ret) < 2

    @pytest.mark.tag_sec_confidentiality
    def test_T3418_with_other_account_filters(self):
        filters = {'SecurityGroupIds': [self.sg3.SecurityGroupId]}
        ret = self.a2_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert not ret

    def test_T5064_with_NetIds_filters(self):
        filters = {'NetIds': [self.vpc_info[VPC_ID]]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 3

        filters = {'NetIds': ['vpc-123456789']}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 0

    def test_T5369_with_tags_filter(self):
        filters = {'Tags': ['sg_key=sg_value']}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1

    def test_T5370_with_tagskey_filter(self):
        filters = {"TagKeys": ['sg_key']}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 2

    def test_T5371_with_tagvalues_filter(self):
        filters = {"TagValues": ['sg_value']}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 2

    def test_T5372_with_invalid_tags_filter(self):
        try:
            filters = {'Tags': 'sg_invalid_key=sg_invalid_value'}
            self.a1_r1.oapi.ReadSecurityGroups(Filters=filters)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5373_with_invalid_tagskey_filter(self):
        try:
            filters = {"TagKeys": 'sg_invalid_key'}
            self.a1_r1.oapi.ReadSecurityGroups(Filters=filters)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5374_with_invalid_tagvalues_filter(self):
        try:
            filters = {"TagValues": 'sg_invalid_value'}
            self.a1_r1.oapi.ReadSecurityGroups(Filters=filters)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5375_with_incorrect_tags_filter(self):
        filters = {"TagValues": ['sg_inc_key=sg_inc_value']}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 0

    def test_T5376_with_tags_filter_from_another_account(self):
        filters = {'Tags': ['sg_key=sg_value']}
        ret = self.a2_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 0
