# -*- coding:utf-8 -*-
import pytest
from qa_tina_tests.USER.API.OAPI.SecurityGroup.SecurityGroup import SecurityGroup, validate_sg


class Test_ReadSecurityGroups(SecurityGroup):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSecurityGroups, cls).setup_class()
        try:
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                SecurityGroupNameToLink=cls.sg1['name'],
                SecurityGroupAccountIdToLink=cls.a1_r1.config.account.account_id,
                SecurityGroupId=cls.sg1['id'])
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Inbound',
                IpProtocol='udp',
                FromPortRange=1,
                ToPortRange=535,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg1['id'])
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
                            'SecurityGroupId': cls.sg1['id'],
                        }],
                        'IpProtocol': 'tcp',
                        'FromPortRange': 45,
                        'ToPortRange': 4609,
                        'IpRanges': ['10.0.0.12/32']
                    }
                ],
                SecurityGroupId=cls.sg1['id'])
            cls.a1_r1.oapi.CreateSecurityGroupRule(
                Flow='Outbound',
                IpProtocol='tcp',
                FromPortRange=1234,
                ToPortRange=1234,
                IpRange='10.0.0.12/32',
                SecurityGroupId=cls.sg2['id'])
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    def test_T2750_empty_filters(self):
        ret = self.a1_r1.oapi.ReadSecurityGroups().response.SecurityGroups
        assert len(ret) > 3
        is_sg = False
        for sg in ret:
            if sg.SecurityGroupId == self.sg1['id']:
                validate_sg(
                    sg,
                    expected_sg={'Description': 'test_desc', 'SecurityGroupName': self.sg1['name']},
                    in_rules=[
                        {
                            'IpProtocol': 'icmp',
                            'FromPortRange':-1,
                            'IpRanges': ['10.0.0.12/32'],
                            'SecurityGroupsMembers': [{
                                'SecurityGroupId': self.sg1['id'],
                                'SecurityGroupName': self.sg1['name'],
                                'AccountId': self.a1_r1.config.account.account_id,
                            }],
                            'ToPortRange':-1,
                        },
                        {
                            'IpProtocol': 'tcp',
                            'FromPortRange': 45,
                            'SecurityGroupsMembers': [{
                                'SecurityGroupId': self.sg1['id'],
                                'SecurityGroupName': self.sg1['name'],
                                'AccountId': self.a1_r1.config.account.account_id,
                            }],
                            'ToPortRange': 4609,
                        },
                        {
                            'IpProtocol': 'tcp',
                            'FromPortRange': 0,
                            'SecurityGroupsMembers': [{
                                'SecurityGroupId': self.sg1['id'],
                                'SecurityGroupName': self.sg1['name'],
                                'AccountId': self.a1_r1.config.account.account_id,
                            }],
                            'ToPortRange': 65535,
                        },
                        {
                            'IpProtocol': 'udp',
                            'FromPortRange': 0,
                            'SecurityGroupsMembers': [{
                                'SecurityGroupId': self.sg1['id'],
                                'SecurityGroupName': self.sg1['name'],
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
                is_sg = True
            elif sg.SecurityGroupId == self.sg2['id']:
                validate_sg(
                    sg,
                    expected_sg={'Description': 'test_desc', 'SecurityGroupName': self.sg2['name']},
                    out_rules=[{
                        'IpProtocol': 'tcp', 'FromPortRange': 1234,
                        'ToPortRange': 1234, 'IpRanges': ['10.0.0.12/32'],
                    },
                        {
                            'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
                    }], net_id=self.vpc['vpc_id'])
            elif sg.SecurityGroupId == self.sg3['id']:
                validate_sg(
                    sg, description='test_desc', name=self.sg3['name'],
                    net_id=self.vpc['vpc_id'],
                    out_rules=[{
                        'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
                    }])
        assert is_sg

    def test_T2751_filters_account_ids(self):
        filters = {'AccountIds': [self.a1_r1.config.account.account_id]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) > 1
        assert ret[0].AccountId == self.a1_r1.config.account.account_id

    def test_T2752_filters_sg_id1(self):
        filters = {'SecurityGroupIds': [self.sg1['id']]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg1['id'],
                'Description': 'test_desc',
                'SecurityGroupName': self.sg1['name']},
            in_rules=[
                {
                    'IpProtocol': 'icmp',
                    'FromPortRange':-1,
                    'IpRanges': ['10.0.0.12/32'],
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1['id'],
                        'SecurityGroupName': self.sg1['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange':-1,
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 45,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1['id'],
                        'SecurityGroupName': self.sg1['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 4609,
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPortRange': 0,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1['id'],
                        'SecurityGroupName': self.sg1['name'],
                        'AccountId': self.a1_r1.config.account.account_id,
                    }],
                    'ToPortRange': 65535,
                },
                {
                    'IpProtocol': 'udp',
                    'FromPortRange': 0,
                    'SecurityGroupsMembers': [{
                        'SecurityGroupId': self.sg1['id'],
                        'SecurityGroupName': self.sg1['name'],
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
        filters = {'SecurityGroupIds': [self.sg2['id']]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg2['id'],
                'Description': 'test_desc',
                'SecurityGroupName': self.sg2['name']},
            out_rules=[{
                'IpProtocol': 'tcp', 'FromPortRange': 1234,
                'ToPortRange': 1234, 'IpRanges': ['10.0.0.12/32'],
            },
                {
                    'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
            }], net_id=self.vpc['vpc_id'])

    def test_T2754_filters_sg_rule_set_id3(self):
        filters = {'SecurityGroupIds': [self.sg3['id']]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg3['id'],
                'Description': 'test_desc',
                'SecurityGroupName': self.sg3['name'],
                'NetId': self.vpc['vpc_id'],
            },
            out_rules=[{
                'IpProtocol': '-1', 'IpRanges': ['0.0.0.0/0'],
            }])

    def test_T2755_filters_sg_rule_set_name3(self):
        filters = {'SecurityGroupNames': [self.sg3['name']]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 1
        validate_sg(
            ret[0],
            expected_sg={
                'SecurityGroupId': self.sg3['id'],
                'Description': 'test_desc',
                'SecurityGroupName': self.sg3['name'],
                'NetId': self.vpc['vpc_id'],
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
        filters = {'SecurityGroupIds': [self.sg3['id']]}
        ret = self.a2_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert not ret

    def test_T5064_with_NetIds_filters(self):
        filters = {'NetIds': [self.vpc['vpc_id']]}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 3

        filters = {'NetIds': ['vpc-123456789']}
        ret = self.a1_r1.oapi.ReadSecurityGroups(Filters=filters).response.SecurityGroups
        assert len(ret) == 0
        
