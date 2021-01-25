import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances


class Test_DeleteSecurityGroup(OscTestSuite):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_DeleteSecurityGroup, cls).setup_class()
        cls.instance_info_a1 = None
        try:
            cls.instance_info_a1 = create_instances(cls.a1_r1)
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            raise error1

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteSecurityGroup, cls).teardown_class()
        try:
            if cls.instance_info_a1:
                delete_instances(cls.a1_r1, cls.instance_info_a1)
        finally:
            super(Test_DeleteSecurityGroup, cls).teardown_class()
#     @classmethod
#     def setup_class(cls):
#         super(Test_DeleteSecurityGroup, cls).setup_class()
#
#     @classmethod
#     def teardown_class(cls):
#         super(Test_DeleteSecurityGroup, cls).teardown_class()

    def test_T981_using_id(self):
        sg_name = 'test_sg'
        sg_response = self.conns[0].fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
        sg_id = sg_response.response.groupId
        # check if group is created
        assert sg_response.response.osc_return == 'true'
        # check if group is deleted
        del_group = self.conns[0].fcu.DeleteSecurityGroup(GroupId=sg_id)
        assert del_group.response.osc_return == 'true'
        assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", del_group.response.requestId)
        assert del_group.response.obj_name == 'DeleteSecurityGroupResponse'

    def test_T982_using_name(self):
        sg_name = 'test_sg'
        sg_response = self.conns[0].fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
        assert sg_response.response.osc_return == 'true'
        del_group = self.conns[0].fcu.DeleteSecurityGroup(GroupName=sg_name)
        assert del_group.response.osc_return == 'true'
        assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", del_group.response.requestId)
        assert del_group.response.obj_name == 'DeleteSecurityGroupResponse'

    def test_T983_using_name_and_id(self):
        sg_name = 'test_sg'
        sg_response = self.conns[0].fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
        sg_id = sg_response.response.groupId
        assert sg_response.response.osc_return == 'true'
        del_group = self.conns[0].fcu.DeleteSecurityGroup(GroupId=sg_id, GroupName=sg_name)
        assert del_group.response.osc_return == 'true'
        assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", del_group.response.requestId)
        assert del_group.response.obj_name == 'DeleteSecurityGroupResponse'

    def test_T2623_reserved_for_vpc(self):
        vpc_id = None
        sg_id = None
        try:
            vpc_id = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16')).response.vpc.vpcId
            sg_id = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name' : 'vpc-id', 'Value': vpc_id}]).response.securityGroupInfo[0].groupId
            self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, None, None)
        finally:
            if vpc_id:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
                except:
                    pass
