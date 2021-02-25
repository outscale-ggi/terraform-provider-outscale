# -*- coding:utf-8 -*-

import time

from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.compare_objects import create_hints
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID


class SecurityGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.sg1 = None
        cls.sg2 = None
        cls.sg3 = None
        cls.sg4 = None
        cls.sg5 = None
        cls.sg6 = None
        super(SecurityGroup, cls).setup_class()
        try:
            cls.sg1 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_1",
                                                         SecurityGroupName='TEST_SG_NAME_1').response.SecurityGroup
            cls.sg2 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_2",
                                                         SecurityGroupName='TEST_SG_NAME_2').response.SecurityGroup
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=0, igw=False)
            cls.sg3 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_3",
                                                         SecurityGroupName='TEST_SG_NAME_3', NetId=cls.vpc_info[VPC_ID]).response.SecurityGroup
            cls.sg4 = cls.a1_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_4",
                                                         SecurityGroupName='TEST_SG_NAME_4', NetId=cls.vpc_info[VPC_ID]).response.SecurityGroup
            cls.sg5 = cls.a2_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_1",
                                                         SecurityGroupName='TEST_SG_NAME_5').response.SecurityGroup
            cls.sg6 = cls.a2_r1.oapi.CreateSecurityGroup(Description="TEST_SG_DESC_2",
                                                         SecurityGroupName='TEST_SG_NAME_6').response.SecurityGroup
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
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            teardown_error = None
            for sg in [cls.sg1, cls.sg2, cls.sg3, cls.sg4]:
                if sg:
                    try:
                        cls.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg.SecurityGroupId)
                    except Exception as error:
                        if not teardown_error:
                            teardown_error = error
            for sg in [cls.sg5, cls.sg6]:
                if sg:
                    try:
                        cls.a2_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg.SecurityGroupId)
                    except Exception as error:
                        if not teardown_error:
                            teardown_error = error
            time.sleep(10)
            delete_vpc(cls.a1_r1, cls.vpc_info)
            if teardown_error:
                raise teardown_error
        finally:
            super(SecurityGroup, cls).teardown_class()
