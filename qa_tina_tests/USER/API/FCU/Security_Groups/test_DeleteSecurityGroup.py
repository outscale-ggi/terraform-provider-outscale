import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances, \
    create_load_balancer, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tina.info_keys import SECURITY_GROUP_ID, SUBNETS, SUBNET_ID
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.info_keys import VPC_ID


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
            sg_id = self.a1_r1.fcu.DescribeSecurityGroups(Filter=[{'Name': 'vpc-id', 'Value': vpc_id}]).response.securityGroupInfo[0].groupId
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

    def test_T5459_associated_with_vm(self):
        try:
            self.a1_r1.fcu.DeleteSecurityGroup(GroupId=self.instance_info_a1[SECURITY_GROUP_ID])
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.InUse", "There are active Instances or NetworkInterfaces using the security group: {}"
                         .format(self.instance_info_a1[SECURITY_GROUP_ID]))

    def test_T5460_associated_with_lbu(self):
        vpc_info = create_vpc(self.a1_r1)
        ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test', GroupName=id_generator(prefix='sg'), VpcId=vpc_info[VPC_ID])
        sg_id = ret.response.groupId
        lb_name = id_generator(prefix='lbu-')
        create_load_balancer(self.a1_r1, lb_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                              sg=[sg_id], subnets=[vpc_info[SUBNETS][0][SUBNET_ID]])
        try:
            self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.InUse", "There are active Instances or NetworkInterfaces using the security group: {}"
                         .format(sg_id))
        finally:
            if vpc_info:
                cleanup_vpcs(self.a1_r1, vpc_id_list=vpc_info[VPC_ID], force=True)
