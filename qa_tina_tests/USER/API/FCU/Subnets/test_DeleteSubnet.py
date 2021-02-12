import string

import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc_old, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_subnet, delete_vpc
from qa_tina_tools.tools.tina.info_keys import SUBNETS, SUBNET_ID, VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_subnets_state, wait_security_groups_state


class Test_DeleteSubnet(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        super(Test_DeleteSubnet, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=0, igw=False)
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DeleteSubnet, cls).teardown_class()

    def test_T1304_with_security_group(self):
        vpc_id = None
        subnet_id = None
        sg_id = None
        try:
            ret = create_vpc_old(self.a1_r1, Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            subnet_id = self.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=vpc_id).response.subnet.subnetId
            wait_subnets_state(self.a1_r1, [subnet_id], state='available')
            sg_id = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='sg1', GroupName='sg1', VpcId=vpc_id).response.groupId
            time.sleep(5)
            self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
            wait_security_groups_state(self.a1_r1, [sg_id], cleanup=True)
            sg_id = None
            delete_subnet(self.a1_r1, subnet_id)
            wait_subnets_state(self.a1_r1, [subnet_id], cleanup=True)
            subnet_id = None
            self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
            vpc_id = None
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pass
            if subnet_id:
                try:
                    self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)
                except Exception:
                    pass
            if vpc_id:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
                except Exception:
                    pass

    def test_T1946_with_subnet_id_list(self):
        try:
            self.vpc_info = create_vpc(self.a1_r1, igw=False)
            subnet_id = self.vpc_info[SUBNETS][0][SUBNET_ID]
            try:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=[subnet_id])
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'InvalidParameterType',
                             "Value of parameter 'SubnetID' must be of type: string. Received: {'1': '" + subnet_id + "'}")
        finally:
            if self.vpc_info:
                delete_vpc(self.a1_r1, self.vpc_info)

    def test_T4046_without_params(self):
        try:
            self.a1_r1.fcu.DeleteSubnet()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
                assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: SubnetID")

    def test_T4047_with_another_account(self):
        vpc_info = None
        try:
            vpc_info = create_vpc(self.a1_r1, igw=False)
            subnet_id = vpc_info[SUBNETS][0][SUBNET_ID]
            try:
                self.a2_r1.fcu.DeleteSubnet(SubnetId=[subnet_id][0])
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'InvalidSubnetID.NotFound', "The subnet ID '{}' does not exist".format([subnet_id][0]))
        finally:
            if vpc_info:
                delete_vpc(self.a1_r1, vpc_info)
                
    def test_T4048_empty_subnet_id(self):
        try:
            self.a1_r1.fcu.DeleteSubnet(SubnetId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
                assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: SubnetID")
                
    def test_T4049_none_subnet_id(self):
        try:
            self.a1_r1.fcu.DeleteSubnet(SubnetId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
                assert_error(error, 400, 'MissingParameter', "Parameter cannot be empty: SubnetID")
                
    def test_T4050_non_existent_subnet_id(self):
        subnet_id = id_generator("subnet-", 8, chars=(string.hexdigits).lower())
        try:
            self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
                assert_error(error, 400, 'InvalidSubnetID.NotFound', "The subnet ID '{}' does not exist".format(subnet_id))

    def test_T4051_with_valid_params(self):
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId=self.vpc_info[VPC_ID], CidrBlock='10.0.1.0/24').response.subnet.subnetId
            self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)
        finally:
            pass
