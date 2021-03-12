
import os

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.compare_objects import verify_response
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import known_error
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import SecurityGroup


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
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Inbound',
            IpProtocol='tcp',
            FromPortRange=1234,
            ToPortRange=1234,
            IpRange='10.0.0.12/32',
            SecurityGroupId=self.sg1.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_rule_valid_case_inbound.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')

    def test_T2722_valid_case_outbound(self):
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Outbound',
            IpProtocol='tcp',
            FromPortRange=1234,
            ToPortRange=1234,
            IpRange='10.0.0.12/32',
            SecurityGroupId=self.sg3.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       'create_rule_valid_case_outbound.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')

    def test_T2723_with_sg_to_link_param_inbound(self):
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Inbound',
            SecurityGroupNameToLink=self.sg1.SecurityGroupName,
            SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
            SecurityGroupId=self.sg1.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_rule_with_sg_to_link_param_inbound.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')

    def test_T5475_with_sg_to_link_param_outbound(self):
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Outbound',
            SecurityGroupNameToLink=self.sg3.SecurityGroupId,  # The name can be only used in Cloud Public not in Net
            SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
            SecurityGroupId=self.sg3.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_rule_with_sg_to_link_param_outbound.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')

    def test_T2724_invalid_ip_range(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg3)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    IpProtocol='tcp',
                    FromPortRange=1237,
                    ToPortRange=1234,
                    IpRange='Hello',
                    SecurityGroupId=sg.SecurityGroupId
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2725_unknown_protocol(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg3)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    IpProtocol='new_protocol',
                    FromPortRange=1237,
                    ToPortRange=1234,
                    IpRange='10.0.0.12/32',
                    SecurityGroupId=sg.SecurityGroupId
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T2726_invalid_port_range(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg3)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    IpProtocol='tcp',
                    FromPortRange=1237,
                    ToPortRange=1234,
                    IpRange='10.0.0.12/32',
                    SecurityGroupId=sg.SecurityGroupId
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
                    SecurityGroupId=sg.SecurityGroupId
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
                SecurityGroupId=self.sg1.SecurityGroupId)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8004')

    def test_T2728_invalid_parameters_composition(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupId=self.sg1.SecurityGroupId)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg3)]:
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
                    SecurityGroupId=sg.SecurityGroupId
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2729_inbound_rules_array_1_element(self):
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Inbound',
            Rules=[
                {
                    'SecurityGroupsMembers': [{
                        'AccountId': self.a1_r1.config.account.account_id,
                        'SecurityGroupName': self.sg1.SecurityGroupName,
                    }],
                    'IpProtocol': 'tcp',
                    'FromPortRange': 45,
                    'ToPortRange': 7890,
                    'IpRanges': ['10.0.0.12/32']}],
            SecurityGroupId=self.sg1.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_rule_inbound_rules_array_1_element.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')

    def test_T2942_outbound_rules_array_1_element(self):
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Outbound', Rules=[
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 45,
                    'ToPortRange': 7890,
                    'IpRanges': ['10.0.0.12/32']
                }],
            SecurityGroupId=self.sg3.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_rule_outbound_rules_array_1_element.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')

    def test_T2730_rules_invalid_array_combination(self):
        for flow, sg in [('Inbound', self.sg1), ('Outbound', self.sg3)]:
            try:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    Flow=flow,
                    Rules=[
                        {
                            'SecurityGroupsMembers': [{
                                'SecurityGroupName': sg.SecurityGroupName,
                                'SecurityGroupId': sg.SecurityGroupId,
                            }],
                            'IpProtocol': 'icmp',
                            'FromPortRange':-1,
                            'ToPortRange':-1,
                            'IpRanges': ['10.0.0.12/32']}],
                    SecurityGroupId=sg.SecurityGroupId)
                self.a1_r1.oapi.DeleteSecurityGroupRule(
                    Flow=flow,
                    Rules=[
                        {
                            'SecurityGroupsMembers': [{
                                'SecurityGroupId': sg.SecurityGroupId,
                            }],
                            'IpProtocol': 'icmp',
                            'FromPortRange':-1,
                            'ToPortRange':-1,
                            'IpRanges': ['10.0.0.12/32'],
                        }
                    ],
                    SecurityGroupId=sg.SecurityGroupId
                )
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2731_inbound_rules_array_many_element(self):
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Inbound',
            Rules=[
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 1234,
                    'ToPortRange': 1235,
                    'IpRanges': ['10.0.0.11/32'],
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 4325,
                    'ToPortRange': 6587,
                    'IpRanges': ['10.0.0.12/32'],
                },
                {
                    'IpProtocol': 'icmp',
                    'FromPortRange':-1,
                    'ToPortRange':-1,
                    'IpRanges': ['10.0.0.13/32']
                },
                {
                    'SecurityGroupsMembers': [{
                        'AccountId': self.a1_r1.config.account.account_id,
                        'SecurityGroupId': self.sg3.SecurityGroupId,
                    }],
                    'IpProtocol': 'udp',
                    'FromPortRange': 56,
                    'ToPortRange': 78,
                    'IpRanges': ['10.0.0.14/32']
                }
            ],
            SecurityGroupId=self.sg4.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_rule_inbound_rules_array_many_element.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')
        finally:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                    Flow='Inbound',
                    SecurityGroupId=self.sg4.SecurityGroupId,
                    Rules=[
                        {'IpProtocol': 'tcp',
                         'FromPortRange': 1234,
                         'ToPortRange': 1235,
                         'IpRanges': ['10.0.0.11/32'],
                         },
                        {
                         'IpProtocol': 'udp',
                         'FromPortRange': 4325,
                         'ToPortRange': 6587,
                         'IpRanges': ['10.0.0.12/32'],
                        },
                        {
                         'IpProtocol': 'icmp',
                         'FromPortRange':-1,
                         'ToPortRange':-1,
                         'IpRanges': ['10.0.0.13/32']
                        },
                        {
                         'SecurityGroupsMembers': [{
                             'AccountId': self.a1_r1.config.account.account_id,
                             'SecurityGroupId': self.sg3.SecurityGroupId,
                         }],
                         'IpProtocol': 'udp',
                         'FromPortRange': 56,
                         'ToPortRange': 78,
                         'IpRanges': ['10.0.0.14/32']
                        }]
                )

    def test_T5476_outbound_rules_array_many_element(self):
        ret = self.a1_r1.oapi.CreateSecurityGroupRule(
            Flow='Outbound',
            Rules=[
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 1234,
                    'ToPortRange': 1235,
                    'IpRanges': ['10.0.0.11/32'],
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 4325,
                    'ToPortRange': 6587,
                    'IpRanges': ['10.0.0.12/32'],
                },
                {
                    'IpProtocol': 'icmp',
                    'FromPortRange':-1,
                    'ToPortRange':-1,
                    'IpRanges': ['10.0.0.13/32']
                },
                {
                    'SecurityGroupsMembers': [{
                        'AccountId': self.a1_r1.config.account.account_id,
                        'SecurityGroupId': self.sg3.SecurityGroupId,
                    }],
                    'IpProtocol': 'udp',
                    'FromPortRange': 56,
                    'ToPortRange': 78,
                    'IpRanges': ['10.0.0.14/32']
                }
            ],
            SecurityGroupId=self.sg4.SecurityGroupId)
        ret.check_response()
        try:
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_rule_outbound_rules_array_many_element.json'),
                            self.hints)
            assert False, 'Remove known error'
        except OscTestException:
            known_error('API-173', 'Protocols and ip ranges are incorrect.')
        finally:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                SecurityGroupId=self.sg4.SecurityGroupId,

                Rules=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPortRange': 1234,
                        'ToPortRange': 1235,
                        'IpRanges': ['10.0.0.11/32'],
                    },
                    {
                        'IpProtocol': 'udp',
                        'FromPortRange': 4325,
                        'ToPortRange': 6587,
                        'IpRanges': ['10.0.0.12/32'],
                    },
                    {
                        'IpProtocol': 'icmp',
                        'FromPortRange':-1,
                        'ToPortRange':-1,
                        'IpRanges': ['10.0.0.13/32']
                    },
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupId': self.sg3.SecurityGroupId,
                        }],
                        'IpProtocol': 'udp',
                        'FromPortRange': 56,
                        'ToPortRange': 78,
                        'IpRanges': ['10.0.0.14/32']
                    }
                ]
            )

    def test_T4386_with_bad_parameters(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='icmp',
                FromPortRange=-1,
                ToPortRange=-1,
                SecurityGroupId=self.sg1.SecurityGroupId)
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
                SecurityGroupId=self.sg1.SecurityGroupId)
            assert False, 'Call should not have been successful'
        except OscTestException as error:
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
                SecurityGroupId=self.sg1.SecurityGroupId)
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
                SecurityGroupId=self.sg1.SecurityGroupId)
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
