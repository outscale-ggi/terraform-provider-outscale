import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.delete_tools import delete_subnet
from qa_tina_tools.tools.tina.wait_tools import wait_subnets_state


class Test_CreateNetworkInterface(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.subnet1_id = None
        cls.vpc_id = None
        super(Test_CreateNetworkInterface, cls).setup_class()
        try:
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId
            # create subnet 1
            ret = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet1_id = ret.response.subnet.subnetId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            err = None
            if cls.subnet1_id:
                try:
                    delete_subnet(cls.a1_r1, cls.subnet1_id)
                except Exception as error:
                    err = error
            if cls.vpc_id:
                try:
                    cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)
                except Exception as error:
                    err = error
            if err:
                raise err
        finally:
            super(Test_CreateNetworkInterface, cls).teardown_class()

    def test_T568_no_param(self):
        try:
            self.a1_r1.fcu.CreateNetworkInterface()
            assert False, 'CreatenetworkInterface should have not succeeded'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'MissingParameter'

    def test_T569_private_ip_in_range(self):
        try:
            ret = self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id, PrivateIpAddress=Configuration.get('ipaddress', '10_0_1_4'))
            fni_id = ret.response.networkInterface.networkInterfaceId
        except Exception as error:
            self.logger.exception(error)
            pytest.fail('An unexpected error happened')
        finally:
            self.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=fni_id)

    def test_T570_private_ip_out_of_range(self):
        try:
            self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id, PrivateIpAddress=Configuration.get('ipaddress', '99_99_99_99'))
            assert False, 'CreatenetworkInterface should have not succeeded'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Address does not fall within the subnet's address range")

    def test_T1305_with_non_vpc_security_group(self):
        sg_id = None
        vpc_id = None
        subnet_id = None
        genid = id_generator()
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='desc' + genid, GroupName='name' + genid)
            sg_id = ret.response.groupId
            ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            ret = self.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=vpc_id)
            subnet_id = ret.response.subnet.subnetId
            wait_subnets_state(self.a1_r1, [subnet_id], state='available')
            self.a1_r1.fcu.CreateNetworkInterface(SubnetId=self.subnet1_id, SecurityGroupId=[sg_id])
            assert False, 'CreateNetworkInterface should not have succeeded'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group '{0}' does not exist in this VPC.".format(sg_id))
        finally:
            if subnet_id:
                try:
                    delete_subnet(self.a1_r1, self.subnet_id)
                except Exception:
                    pass
            if vpc_id:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
                except Exception:
                    pass
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pass
