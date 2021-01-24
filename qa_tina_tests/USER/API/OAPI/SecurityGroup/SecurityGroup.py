# -*- coding:utf-8 -*-

import time

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_test_tools.compare_objects import create_hints


# def validate_sg(sg, **kwargs):
#     """
# 
#     :param sg:
#     :param kwargs:
#             dict(str) expected_sg
#             list(dict) in_rules
#             list(dict) out_rules
#     :return:
#     """
#     expected_sg = kwargs.get('expected_sg', {})
#     for k, v in expected_sg.items():
#         assert getattr(sg, k) == v, (
#             'In Snapshot, {} is different of expected value {} for key {}'.format(getattr(sg, k), v, k))
#     in_rules = kwargs.get('in_rules', [])
#     out_rules = kwargs.get('out_rules', [])
#     assert hasattr(sg, "Description")
#     assert sg.SecurityGroupId.startswith('sg')
#     assert hasattr(sg, "SecurityGroupName")
#     assert not sg.SecurityGroupName.startswith('sg')
#     assert hasattr(sg, "AccountId")
#     assert hasattr(sg, "OutboundRules")
#     if len(out_rules):
#         for out_rule in sg.OutboundRules:
#             index = 0
#             for rule in out_rules:
#                 try:
#                     for k, v in rule.items():
#                         if k == 'SecurityGroupsMembers':
#                             validate_security_groups_members(out_rule.SecurityGroupsMembers, v)
#                         else:
#                             assert getattr(out_rule, k) == v, (
#                                 'In OutboundRules[], {} is different of expected value {} for key {}'.format(getattr(out_rule, k), v, k))
#                     break
#                 except AssertionError as error:
#                     if index == len(out_rules):
#                         assert False, 'not found into expected rules. error: {}'.format(error)
#                     else:
#                         pass
#                 index += 1
#     assert hasattr(sg, "InboundRules")
#     if len(in_rules):
#         for in_rule in sg.InboundRules:
#             index = 0
#             for rule in in_rules:
#                 try:
#                     for k, v in rule.items():
#                         if k == 'SecurityGroupsMembers':
#                             validate_security_groups_members(in_rule.SecurityGroupsMembers, v)
#                         else:
#                             assert getattr(in_rule, k) == v, (
#                                 'In InboundRules[], {} is different of expected value {} for key {}'.format(getattr(in_rule, k), v, k))
#                     break
#                 except AssertionError as error:
#                     if index == len(in_rules):
#                         assert False, 'not found into expected rules. error: {}'.format(error)
#                     else:
#                         pass
#                 index += 1
# 
# 
# def validate_security_groups_members(sg_members, expected_sg_members):
#     for sg_member in sg_members:
#         index = 0
#         for e_sg_mb in expected_sg_members:
#             index += 1
#             try:
#                 for k, v in e_sg_mb.items():
#                     assert getattr(sg_member, k) == v, (
#                         'In SecurityGroupMembers[], {} is different of expected value {} for key {}'.format(getattr(sg_member, k), v, k))
#             except AssertionError as error:
#                 if index == len(expected_sg_members):
#                     assert False, 'not found into expected sg_members. error: {}'.format(error)
#                 else:
#                     pass


class SecurityGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.sg1 = None
        cls.sg2 = None
        cls.sg3 = None
        cls.sg4 = None
        cls.sg5 = None
        super(SecurityGroup, cls).setup_class()
        try:
            cls.sg1 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_1", SecurityGroupName='TEST_SG_NAME_1').response.SecurityGroup
            cls.sg2 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_2", SecurityGroupName='TEST_SG_NAME_2').response.SecurityGroup
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=0, igw=False)
            cls.sg3 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_3", SecurityGroupName='TEST_SG_NAME_3', NetId=cls.vpc_info[VPC_ID]).response.SecurityGroup
            cls.sg4 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_4", SecurityGroupName='TEST_SG_NAME_4', NetId=cls.vpc_info[VPC_ID]).response.SecurityGroup
            cls.sg5 = cls.a2_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_1", SecurityGroupName='TEST_SG_NAME_1').response.SecurityGroup
            cls.sg6 = cls.a2_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_2", SecurityGroupName='TEST_SG_NAME_2').response.SecurityGroup
            cls.hints = create_hints([cls.a1_r1.config.account.account_id,
                                      cls.a2_r1.config.account.account_id,
                                      cls.vpc_info[VPC_ID],
                                      cls.sg1.SecurityGroupId,
                                      cls.sg1.SecurityGroupName,
                                      cls.sg1.Description,
                                      cls.sg2.SecurityGroupId,
                                      cls.sg2.SecurityGroupName,
                                      cls.sg2.Description,
                                      cls.sg3.SecurityGroupId,
                                      cls.sg3.SecurityGroupName,
                                      cls.sg3.Description,
                                      cls.sg4.SecurityGroupId,
                                      cls.sg4.SecurityGroupName,
                                      cls.sg4.Description,
                                      cls.sg5.SecurityGroupId,
                                      cls.sg5.SecurityGroupName,
                                      cls.sg5.Description,
                                      cls.sg6.SecurityGroupId,
                                      cls.sg6.SecurityGroupName,
                                      cls.sg6.Description])
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
            for sg in [cls.sg1, cls.sg2, cls.sg3, cls.sg4]:
                if sg:
                    try:
                        cls.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg.SecurityGroupId)
                    except:
                        pass
            for sg in [cls.sg5, cls.sg6]:
                if sg:
                    try:
                        cls.a2_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg.SecurityGroupId)
                    except:
                        pass
            time.sleep(10)
            delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(SecurityGroup, cls).teardown_class()
