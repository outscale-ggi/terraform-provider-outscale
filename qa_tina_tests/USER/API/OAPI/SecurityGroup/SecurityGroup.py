# -*- coding:utf-8 -*-
import random
import string
import time

from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc


def validate_sg(sg, **kwargs):
    """

    :param sg:
    :param kwargs:
            dict(str) expected_sg
            list(dict) in_rules
            list(dict) out_rules
    :return:
    """
    expected_sg = kwargs.get('expected_sg', {})
    for k, v in expected_sg.items():
        assert getattr(sg, k) == v, (
            'In Snapshot, {} is different of expected value {} for key {}'.format(getattr(sg, k), v, k))
    in_rules = kwargs.get('in_rules', [])
    out_rules = kwargs.get('out_rules', [])
    assert hasattr(sg, "Description")
    assert sg.SecurityGroupId.startswith('sg')
    assert hasattr(sg, "SecurityGroupName")
    assert not sg.SecurityGroupName.startswith('sg')
    assert hasattr(sg, "AccountId")
    assert hasattr(sg, "OutboundRules")
    if len(out_rules):
        for out_rule in sg.OutboundRules:
            index = 0
            for rule in out_rules:
                try:
                    for k, v in rule.items():
                        if k == 'SecurityGroupsMembers':
                            validate_security_groups_members(out_rule.SecurityGroupsMembers, v)
                        else:
                            assert getattr(out_rule, k) == v, (
                                'In OutboundRules[], {} is different of expected value {} for key {}'.format(getattr(out_rule, k), v, k))
                    break
                except AssertionError as error:
                    if index == len(out_rules):
                        assert False, 'not found into expected rules. error: {}'.format(error)
                    else:
                        pass
                index += 1
    assert hasattr(sg, "InboundRules")
    if len(in_rules):
        for in_rule in sg.InboundRules:
            index = 0
            for rule in in_rules:
                try:
                    for k, v in rule.items():
                        if k == 'SecurityGroupsMembers':
                            validate_security_groups_members(in_rule.SecurityGroupsMembers, v)
                        else:
                            assert getattr(in_rule, k) == v, (
                                'In InboundRules[], {} is different of expected value {} for key {}'.format(getattr(in_rule, k), v, k))
                    break
                except AssertionError as error:
                    if index == len(in_rules):
                        assert False, 'not found into expected rules. error: {}'.format(error)
                    else:
                        pass
                index += 1


def validate_security_groups_members(sg_members, expected_sg_members):
    for sg_member in sg_members:
        index = 0
        for e_sg_mb in expected_sg_members:
            index += 1
            try:
                for k, v in e_sg_mb.items():
                    assert getattr(sg_member, k) == v, (
                        'In SecurityGroupMembers[], {} is different of expected value {} for key {}'.format(getattr(sg_member, k), v, k))
            except AssertionError as error:
                if index == len(expected_sg_members):
                    assert False, 'not found into expected sg_members. error: {}'.format(error)
                else:
                    pass


class SecurityGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(SecurityGroup, cls).setup_class()
        cls.sg1 = None
        cls.sg2 = None
        try:
            name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))
            cls.sg1 = {'id': cls.a1_r1.oapi.CreateSecurityGroup(
                Description="test_desc", SecurityGroupName=name
            ).response.SecurityGroup.SecurityGroupId, 'name': name}
            cls.vpc = create_vpc(cls.a1_r1, nb_subnet=0, igw=False)
            name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))
            cls.sg2 = {'id': cls.a1_r1.oapi.CreateSecurityGroup(
                Description="test_desc", SecurityGroupName=name, NetId=cls.vpc['vpc_id']
            ).response.SecurityGroup.SecurityGroupId, 'name': name}
            name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))
            cls.sg3 = {'id': cls.a1_r1.oapi.CreateSecurityGroup(
                Description="test_desc", SecurityGroupName=name, NetId=cls.vpc['vpc_id']
            ).response.SecurityGroup.SecurityGroupId, 'name': name}
            time.sleep(4)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.sg3:
                cls.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=cls.sg3['id'])
            if cls.sg1:
                cls.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=cls.sg1['id'])
            if cls.sg2:
                cls.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=cls.sg2['id'])
            delete_vpc(cls.a1_r1, cls.vpc)
        finally:
            super(SecurityGroup, cls).teardown_class()
