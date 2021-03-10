# -*- coding:utf-8 -*-
import os
import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import known_error
from qa_test_tools.compare_objects import verify_response
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import SecurityGroup
from qa_tina_tools.tools.tina.info_keys import VPC_ID


class Test_ReadSecurityGroups(SecurityGroup):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSecurityGroups, cls).setup_class()
        try:
            # sg1 rules
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=cls.sg5.SecurityGroupName,
                SecurityGroupAccountIdToLink=cls.a2_r1.config.account.account_id,
                SecurityGroupId=cls.sg1.SecurityGroupId)
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=cls.sg6.SecurityGroupName,
                SecurityGroupAccountIdToLink=cls.a2_r1.config.account.account_id,
                SecurityGroupId=cls.sg1.SecurityGroupId)
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='udp',
                FromPortRange=1,
                ToPortRange=535,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg3.SecurityGroupId)
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
                        'SecurityGroupsMembers': [{'SecurityGroupId': cls.sg1.SecurityGroupId}],
                        'IpProtocol': 'tcp',
                        'FromPortRange': 45,
                        'ToPortRange': 4609,
                        'IpRanges': ['10.0.0.12/32']
                    }
                ],
                SecurityGroupId=cls.sg1.SecurityGroupId)
            # sg3 rules
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                Rules=[{'SecurityGroupsMembers': [{'SecurityGroupId': cls.sg4.SecurityGroupId}]}],
                SecurityGroupId=cls.sg3.SecurityGroupId)
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.13/32',
                SecurityGroupId=cls.sg3.SecurityGroupId)
            # sg4 rules
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=2345,
                ToPortRange=2345,
                IpRange='10.0.0.14/32',
                SecurityGroupId=cls.sg4.SecurityGroupId)
            # tags
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.sg1.SecurityGroupId], Tags=[{'Key': 'sg_key', 'Value': 'sg_value'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.sg3.SecurityGroupId], Tags=[{'Key': 'sg_key', 'Value': 'sg_toto'}])
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.sg4.SecurityGroupId], Tags=[{'Key': 'sg_toto', 'Value': 'sg_value'}])

        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

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

    def test_T2750_no_params(self):
        resp = self.a1_r1.oapi.ReadSecurityGroups().response
        assert len(resp.SecurityGroups) == 4 + 2  # adding 2 default
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_empty.json'),
                               self.hints), 'Could not verify response content.'

    def test_T2751_filters_account_ids(self):
        filters = {'AccountIds': [self.a1_r1.config.account.account_id]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 4 + 2  # adding 2 default
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_account_ids.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5479_filters_account_ids_unknown(self):
        filters = {'AccountIds': ['999999999999']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(resp) == 0

    def test_T5480_filters_account_ids_incorrect_type(self):
        filters = {'AccountIds': self.a1_r1.config.account.account_id}
        try:
            self.a1_r1.oapi.ReadSecurityGroups(Filters=filters)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5481_filters_descriptions(self):
        filters = {'Descriptions': [self.sg1.Description, self.sg3.Description]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 2
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_descriptions.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5482_filters_inbound_rule_account_ids(self):
        filters = {'InboundRuleAccountIds': [self.a2_r1.config.account.account_id]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_inbound_rule_account_ids.json'),
                               self.hints), 'Could not verify response content.'
        if int(resp.SecurityGroups[0].InboundRules[0].IpProtocol):
            known_error("TINA-6173", "[oAPI] ReadSecurityGroups Incorrect value returned for IpProtocol/IpRang")
        assert False, 'Remove known error code'

    def test_T5483_filters_inbound_rule_from_port_ranges(self):
        filters = {'InboundRuleFromPortRanges': [45]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_inbound_rule_from_port_ranges.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5484_filters_inbound_rule_ip_ranges(self):
        filters = {'InboundRuleIpRanges': ['10.0.0.12/32']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        if len(resp.SecurityGroups) == 0:
            known_error('API-173', 'Cannot filter by inbound ip range value')
        assert False, 'Remove known error'
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_inbound_rule_ip_ranges.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5485_filters_inbound_rule_protocols(self):
        filters = {'InboundRuleProtocols': ['udp']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        if len(resp.SecurityGroups) == 0:
            known_error('API-173', 'Cannot filter by outbound protocol value')
        assert False, 'Remove known error'
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_inbound_rule_protocols.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5486_filters_inbound_rule_sg_ids(self):
        filters = {'InboundRuleSecurityGroupIds': [self.sg5.SecurityGroupId]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_inbound_rule_sg_ids.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5487_filters_inbound_sg_names(self):
        filters = {'InboundRuleSecurityGroupNames': [self.sg6.SecurityGroupName]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_inbound_rule_sg_names.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5488_filters_inbound_to_port_ranges(self):
        filters = {'InboundRuleToPortRanges': [535]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_inbound_rule_to_port_ranges.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5489_filters_net_ids(self):
        filters = {'NetIds': [self.vpc_info[VPC_ID]]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_net_ids.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5490_filters_outbound_rule_account_ids(self):
        filters = {'OutboundRuleAccountIds': [self.a2_r1.config.account.account_id]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_outbound_rule_account_ids.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5491_filters_outbound_rule_from_port_ranges(self):
        filters = {'OutboundRuleFromPortRanges': [1234]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_outbound_rule_from_port_ranges.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5492_filters_outbound_rule_ip_ranges(self):
        filters = {'OutboundRuleIpRanges': ['10.0.0.13/32']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        if len(resp.SecurityGroups) == 0:
            known_error('API-173', 'Cannot filter by outbound ip range value')
        assert False, 'Remove known error'
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_outbound_rule_ip_ranges.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5493_filters_outbound_protocols(self):
        filters = {'OutboundRuleProtocols': ['tcp']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        if len(resp.SecurityGroups) == 0:
            known_error('API-173', 'Cannot filter by outbound protocol value')
        assert False, 'Remove known error'
        assert len(resp.SecurityGroups) == 2
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_outbound_rule_protocols.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5494_filters_outbound_sg_ids(self):
        filters = {'OutboundRuleSecurityGroupIds': [self.sg4.SecurityGroupId]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_outbound_rule_sg_ids.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5495_filters_outbound_sg_names(self):
        filters = {'OutboundRuleSecurityGroupNames': [self.sg4.SecurityGroupName]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_outbound_rule_sg_names.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5496_filters_outbound_to_port_ranges(self):
        filters = {'OutboundRuleFromPortRanges': [2345]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_outbound_rule_to_port_ranges.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5497_filters_sg_ids(self):
        filters = {'SecurityGroupIds': [self.sg1.SecurityGroupId, self.sg3.SecurityGroupId]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_sg_ids.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5498_filters_sg_names(self):
        filters = {'SecurityGroupNames': [self.sg1.SecurityGroupName, self.sg4.SecurityGroupName]}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_sg_names.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5369_filters_tags(self):
        filters = {'Tags': ['sg_key=sg_value']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 1
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  'read_filters_tags.json'), self.hints), 'Could not verify response content.'

    def test_T5370_filters_tagkeys(self):
        filters = {"TagKeys": ['sg_key']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 2
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_tagkeys.json'),
                               self.hints), 'Could not verify response content.'

    def test_T5371_filters_tagvalues(self):
        filters = {"TagValues": ['sg_value']}
        resp = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 2
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_filters_tagvalues.json'),
                               self.hints), 'Could not verify response content.'

    @pytest.mark.tag_sec_confidentiality
    def test_T3417_with_other_account(self):
        resp = self.a2_r1.oapi.ReadSecurityGroups().response
        assert len(resp.SecurityGroups) == 2 + 1  # adding 1 default
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_with_other_account.json'),
                               self.hints), 'Could not verify response content.'

    @pytest.mark.tag_sec_confidentiality
    def test_T3418_with_other_account_filters(self):
        filters = {'SecurityGroupIds': [self.sg3.SecurityGroupId]}
        resp = self.a2_r1.oapi.ReadSecurityGroups(Filters=filters).response
        assert len(resp.SecurityGroups) == 0
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_with_other_account_filters.json'),
                               self.hints), 'Could not verify response content.'
