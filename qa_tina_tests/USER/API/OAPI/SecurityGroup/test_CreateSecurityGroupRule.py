# -*- coding:utf-8 -*-
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import SecurityGroup, validate_sg
from qa_tina_tools.specs.oapi.check_tools import check_oapi_response


class Test_CreateSecurityGroupRule(SecurityGroup):

    def test_T2719_without_param(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2720_missing_id(self):
        for flow in ['Inbound', 'Outbound']:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    FromPortRange=1234,
                    IpProtocol='tcp',
                    IpRange='10.0.0.12/32',
                    ToPortRange=1234,
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2721_valid_case_inbound(self):
        sg = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Inbound',
            IpProtocol='tcp',
            FromPortRange=1234,
            ToPortRange=1234,
            IpRange='10.0.0.12/32',
            SecurityGroupId=self.sg1['id']).response.SecurityGroup
        validate_sg(
            sg,
            expected_sg={'SecurityGroupId': self.sg1['id']},
            out_rules=[],
            in_rules=[{
                'IpProtocol': 'tcp', 'FromPortRange': 1234,
                'ToPortRange': 1234, 'IpRanges': ['10.0.0.12/32'],
            }]
        )

    def test_T2722_valid_case_outbound(self):
        sg = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Outbound',
            IpProtocol='tcp',
            FromPortRange=1234,
            ToPortRange=1234,
            IpRange='10.0.0.12/32',
            SecurityGroupId=self.sg2['id']).response.SecurityGroup
        validate_sg(
            sg,
            expected_sg={'SecurityGroupId': self.sg2['id']},
            out_rules=[{
                'IpProtocol': 'tcp', 'FromPortRange': 1234,
                'ToPortRange': 1234, 'IpRanges': ['10.0.0.12/32'],
            },
                {
                    'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
            }]
        )

    def test_T2723_with_sg_to_link_param(self):
        resp = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Inbound',
            SecurityGroupNameToLink=self.sg1['name'],
            SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
            SecurityGroupId=self.sg1['id']).response
        check_oapi_response(resp, 'CreateSecurityGroupRuleResponse')
        validate_sg(
            resp.SecurityGroup,
            expected_sg={'SecurityGroupId': self.sg1['id']},
            in_rules=[
                {
                    'IpProtocol': 'icmp',
                    'FromPortRange': -1,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1['id'],
                        'SecurityGroupName': self.sg1['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange':-1,
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 1,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1['id'],
                        'SecurityGroupName': self.sg1['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 65535,
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 1,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1['id'],
                        'SecurityGroupName': self.sg1['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 65535,
                }
            ]
        )

        resp = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Outbound',
            SecurityGroupNameToLink=self.sg2['id'], # The name can be only used in Cloud Public not in Net
            SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
            SecurityGroupId=self.sg2['id']).response
        check_oapi_response(resp, 'CreateSecurityGroupRuleResponse')
        validate_sg(
            resp.SecurityGroup,
            expected_sg={'SecurityGroupId': self.sg2['id']},
            out_rules=[
                {
                    'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
                },
                {
                    'IpProtocol': 'icmp',
                    'FromPortRange':-1,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg2['id'],
                        'SecurityGroupName': self.sg2['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange':-1,
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 1,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg2['id'],
                        'SecurityGroupName': self.sg2['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 65535,
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 1,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg2['id'],
                        'SecurityGroupName': self.sg2['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 65535,
                }]
        )

    def test_T2724_invalid_ip_range(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg2)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    IpProtocol='tcp',
                    FromPortRange=1237,
                    ToPortRange=1234,
                    IpRange='Hello',
                    SecurityGroupId=sg['id']
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2725_unknown_protocol(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg2)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    IpProtocol='new_protocol',
                    FromPortRange=1237,
                    ToPortRange=1234,
                    IpRange='10.0.0.12/32',
                    SecurityGroupId=sg['id']
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2726_invalid_port_range(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg2)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    IpProtocol='tcp',
                    FromPortRange=1237,
                    ToPortRange=1234,
                    IpRange='10.0.0.12/32',
                    SecurityGroupId=sg['id']
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    IpProtocol='icmp',
                    FromPortRange=1234,
                    ToPortRange=1234,
                    IpRange='10.0.0.12/32',
                    SecurityGroupId=sg['id']
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2727_outbound_rules_without_net(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8004')

    def test_T2728_invalid_parameters_composition(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg2)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
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
                    SecurityGroupId=sg['id']
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2729_inbound_rules_array_1_element(self):
        sg = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Inbound',
            Rules=[
                {
                    'SecurityGroupsMembers': [{
                        'AccountId': self.a1_r1.config.account.account_id,
                        'SecurityGroupName': self.sg1['name'],
                    }],
                    'IpProtocol': 'tcp',
                    'FromPortRange': 45,
                    'ToPortRange': 7890,
                    'IpRanges': ['10.0.0.12/32']}],
            SecurityGroupId=self.sg1['id']).response.SecurityGroup
        validate_sg(sg)

    def test_T2942_outbound_rules_array_1_element(self):
        resp = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Outbound', Rules=[
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 45,
                    'ToPortRange': 7890,
                    'IpRanges': ['10.0.0.12/32']
                }],
            SecurityGroupId=self.sg2['id']).response
        check_oapi_response(resp, 'CreateSecurityGroupRuleResponse')
        validate_sg(resp.SecurityGroup)

    def test_T2730_rules_invalid_array_combination(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg2)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    Rules=[
                        {
                            'SecurityGroupsMembers': [{
                                'SecurityGroupName': sg['name'],
                                'SecurityGroupId': sg['id'],
                            }],
                            'IpProtocol': 'icmp',
                            'FromPortRange':-1,
                            'ToPortRange':-1,
                            'IpRanges': ['10.0.0.12/32']}],
                    SecurityGroupId=sg['id'])
                self.a1_r1.oapi.DeleteSecurityGroupRule(
                    Flow=flow,
                    Rules=[
                        {
                            'SecurityGroupsMembers': [{
                                'SecurityGroupId': sg['id'],
                            }],
                            'IpProtocol': 'icmp',
                            'FromPortRange':-1,
                            'ToPortRange':-1,
                            'IpRanges': ['10.0.0.12/32'],
                        }
                    ],
                    SecurityGroupId=sg['id']
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2731_inbound_rules_array_many_element(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg2)]:
            resp = self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow=flow,
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
                SecurityGroupId=self.sg3['id']).response
            check_oapi_response(resp, 'CreateSecurityGroupRuleResponse')
            validate_sg(resp.SecurityGroup)
            resp = self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow=flow,
                Rules=[
                    {
                        'IpProtocol': 'icmp',
                        'FromPortRange': -1,
                        'ToPortRange': -1,
                        'IpRanges': ['10.0.0.12/32']
                    },
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupId': sg['id'],
                        }],
                        'IpProtocol': 'udp',
                        'FromPortRange': 56,
                        'ToPortRange': 78,
                        'IpRanges': ['10.0.0.12/32']
                    }
                ],
                SecurityGroupId=sg['id']).response
            check_oapi_response(resp, 'CreateSecurityGroupRuleResponse')
            validate_sg(resp.SecurityGroup)

    def test_T4386_with_bad_parameters(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='icmp',
                FromPortRange=-1,
                ToPortRange=-1,
                SecurityGroupId=self.sg1['id'])
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T4908_member_missing_security_identifier(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                Rules=[
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id
                        }],
                        'IpProtocol': 'tcp',
                        'FromPortRange': 45,
                        'ToPortRange': 7890,
                        'IpRanges': ['10.0.0.12/32']}],
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4909_member_incorrect_security_group_name(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                Rules=[
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupName': 'toto',
                        }],
                        'IpProtocol': 'tcp',
                        'FromPortRange': 45,
                        'ToPortRange': 7890,
                        'IpRanges': ['10.0.0.12/32']}],
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5060)

    def test_T4910_member_incorrect_security_group_id(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                Rules=[
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupId': 'sg-12345678',
                        }],
                        'IpProtocol': 'tcp',
                        'FromPortRange': 45,
                        'ToPortRange': 7890,
                        'IpRanges': ['10.0.0.12/32']}],
                SecurityGroupId=self.sg1['id'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5060)

    def test_T4911_incorrect_group_id(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId='sg-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5020)
