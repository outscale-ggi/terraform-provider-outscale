
import os

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import known_error
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.compare_objects import verify_response
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.FCU.Security_Groups.test_RevokeSecurityGroupIngress import to_dict
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import SecurityGroup


def cleanup_sg(osc_sdk, sg_id):
    try:
        ret = osc_sdk.fcu.DescribeSecurityGroups(GroupId=[sg_id])
        if ret.response.securityGroupInfo:
            for group in ret.response.securityGroupInfo:
                if group.ipPermissions:
                    perm_list = [to_dict(perm) for perm in group.ipPermissions]
                    osc_sdk.fcu.RevokeSecurityGroupIngress(GroupId=group.groupId, IpPermissions=perm_list)
                if group.ipPermissionsEgress:
                    perm_list = []
                    for perm in group.ipPermissionsEgress:
                        if perm.ipProtocol == '-1':
                            continue
                        perm_list.append(to_dict(perm))
                    osc_sdk.fcu.RevokeSecurityGroupEgress(GroupId=group.groupId, IpPermissions=perm_list)
    except Exception as error:
        raise error


class Test_DeleteSecurityGroupRule(SecurityGroup):

    def test_T2737_without_param(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(Flow='Inbound')
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

    def test_T2739_valid_public_inbound(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg1.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2739_valid_case_inbound_full.json'),
                            self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1.SecurityGroupId)
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2739_valid_case_inbound_empty.json'),
                            self.hints)
        finally:
            cleanup_sg(self.a1_r1, self.sg1.SecurityGroupId)

    def test_T2740_valid_private_inbound(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg3.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg3.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2740_valid_case_outbound_full.json'),
                            self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg3.SecurityGroupId)
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2740_valid_case_outbound_empty.json'),
                            self.hints)
        finally:
            cleanup_sg(self.a1_r1, self.sg3.SecurityGroupId)

    def test_T2741_valid_private_outbound(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg3.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg3.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2741_valid_private_outbound_full.json'),
                            self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg3.SecurityGroupId)
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2741_valid_private_outbound_empty.json'),
                            self.hints)
        finally:
            cleanup_sg(self.a1_r1, self.sg3.SecurityGroupId)

    def test_T2748_valid_private_sg_outbound(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                SecurityGroupNameToLink=self.sg3.SecurityGroupId,
                SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg4.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg4.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2748_valid_private_sg_outbound_full.json'),
                            self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                SecurityGroupNameToUnlink=self.sg3.SecurityGroupId,
                SecurityGroupAccountIdToUnlink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg4.SecurityGroupId)
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2748_valid_private_sg_outbound_empty.json'),
                            self.hints)
        finally:
            cleanup_sg(self.a1_r1, self.sg4.SecurityGroupId)

    def test_T2749_valid_private_sg_inbound(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=self.sg3.SecurityGroupId,
                SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg4.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg4.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2749_valid_private_sg_inbound_full.json'),
                            self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToUnlink=self.sg3.SecurityGroupId,
                SecurityGroupAccountIdToUnlink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg4.SecurityGroupId)
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T2749_valid_private_sg_inbound_empty.json'),
                            self.hints)
        finally:
            cleanup_sg(self.a1_r1, self.sg4.SecurityGroupId)

    def test_T5477_valid_public_sg_inbound_by_id(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=self.sg1.SecurityGroupId,
                SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg2.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg2.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5477_valid_public_sg_inbound_by_id_full.json'),
                            self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToUnlink=self.sg1.SecurityGroupId,
                SecurityGroupAccountIdToUnlink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg2.SecurityGroupId)
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5477_valid_public_sg_inbound_by_id_empty.json'),
                            self.hints)
        finally:
            cleanup_sg(self.a1_r1, self.sg2.SecurityGroupId)

    def test_T5478_valid_public_sg_inbound_by_name(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=self.sg1.SecurityGroupId,
                SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg2.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg2.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5478_valid_public_sg_inbound_by_name_full.json'),
                            self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToUnlink=self.sg1.SecurityGroupName,
                SecurityGroupAccountIdToUnlink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg2.SecurityGroupId)

            try:
                verify_response(ret.response,
                                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5478_valid_public_sg_inbound_by_name_empty.json'),
                                self.hints)
                assert False, 'Remove known error code'
            except OscTestException:
                known_error('API-331', 'Could not delete rule using sg name')
        finally:
            cleanup_sg(self.a1_r1, self.sg2.SecurityGroupId)

    def test_T5657_rules_inbound(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg2.SecurityGroupId)
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=self.sg1.SecurityGroupId,
                SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg2.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg2.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5657_rules_inbound_full.json'), self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                Rules=[
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupName': self.sg1.SecurityGroupName,
                        }]
                    },
                    {
                        'IpProtocol': "tcp",
                        'FromPortRange':1234,
                        'ToPortRange':1234,
                        'IpRanges': ["10.0.0.12/32"]
                    }
                ],
                SecurityGroupId=self.sg2.SecurityGroupId)
            try:
                verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                           'T5657_rules_inbound_empty.json'), self.hints)
                assert False, 'Remove known error code'
            except OscTestException:
                known_error('API-331', 'Could not delete rule using sg name')
        finally:
            cleanup_sg(self.a1_r1, self.sg2.SecurityGroupId)

    def test_T5658_rules_outbound(self):
        try:
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg4.SecurityGroupId)
            self.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                SecurityGroupNameToLink=self.sg3.SecurityGroupId,
                SecurityGroupAccountIdToLink=self.a1_r1.config.account.account_id,
                SecurityGroupId=self.sg4.SecurityGroupId)
            ret = self.a1_r1.oapi.ReadSecurityGroups(Filters={'SecurityGroupIds': [self.sg4.SecurityGroupId]})
            verify_response(ret.response,
                            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'T5658_rules_outbound_full.json'), self.hints)
            ret = self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                Rules=[
                    {
                        'SecurityGroupsMembers': [{
                            'AccountId': self.a1_r1.config.account.account_id,
                            'SecurityGroupName': self.sg3.SecurityGroupName,
                        }]
                    },
                    {
                        'IpProtocol': "tcp",
                        'FromPortRange':1234,
                        'ToPortRange':1234,
                        'IpRanges': ["10.0.0.12/32"]
                    }
                ],
                SecurityGroupId=self.sg4.SecurityGroupId)

            try:
                verify_response(ret.response, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                           'T5658_rules_outbound_empty.json'), self.hints)
                assert False, 'Remove known error code'
            except OscTestException:
                known_error('API-331', 'Could not delete rule using sg name')

        finally:
            cleanup_sg(self.a1_r1, self.sg4.SecurityGroupId)

    def test_T2742_invalid_ip_range(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='Hello',
                SecurityGroupId=self.sg3.SecurityGroupId
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
                SecurityGroupId=self.sg1.SecurityGroupId
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
                SecurityGroupId=self.sg3.SecurityGroupId
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='new_protocol',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1.SecurityGroupId
            )
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2744_invalid_port_range_inbound(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1237,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg3.SecurityGroupId
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
                SecurityGroupId=self.sg1.SecurityGroupId
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
                SecurityGroupId=self.sg1.SecurityGroupId)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'OperationNotSupported', '8004')

    def test_T2746_missing_port_spec(self):
        try:
            self.a1_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupId=self.sg1.SecurityGroupId)
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
                SecurityGroupId=self.sg1.SecurityGroupId
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
                            'SecurityGroupId': self.sg1.SecurityGroupId,
                            'Name': self.sg1.SecurityGroupName,
                        }],
                        'IpProtocol': 'udp',
                        'FromPortRange': 45,
                        'ToPortRange': 60,
                        'IpRanges': ['10.0.0.12/32']}],
                SecurityGroupId=self.sg1.SecurityGroupId)
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
                            'SecurityGroupId': self.sg3.SecurityGroupId,
                            'Name': self.sg3.SecurityGroupName,
                        }],
                        'IpProtocol': 'udp',
                        'FromPortRange': 45,
                        'ToPortRange': 60,
                        'IpRanges': ['10.0.0.12/32']}],
                SecurityGroupId=self.sg3.SecurityGroupId)

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
                SecurityGroupId=self.sg3.SecurityGroupId
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
                            "SecurityGroupName": self.sg1.SecurityGroupName,
                        }],
                        'IpProtocol': "tcp",
                        'FromPortRange': 45,
                        'ToPortRange': 7890,
                        'IpRanges': ["10.0.0.12/32"]}],
                SecurityGroupId=self.sg1.SecurityGroupId)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'DefaultError', '0')

    @pytest.mark.tag_sec_confidentiality
    def test_T3532_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=self.sg1.SecurityGroupId)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5020')
