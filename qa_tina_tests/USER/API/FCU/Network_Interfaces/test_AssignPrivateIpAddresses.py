from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.config.configuration import Configuration
from qa_tina_tools.tools.tina.delete_tools import delete_subnet
import random
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error


class Test_AssignPrivateIpAddresses(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.subnet_id = None
        cls.vpc_id = None
        cls.ni_id = None
        super(Test_AssignPrivateIpAddresses, cls).setup_class()
        try:
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId
            # create subnet 1
            res_snet = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet_id = res_snet.response.subnet.subnetId
            res_ni = cls.a1_r1.fcu.CreateNetworkInterface(SubnetId=cls.subnet_id, PrivateIpAddress=Configuration.get('ipaddress', '10_0_1_4'))
            cls.ni_id = res_ni.response.networkInterface.networkInterfaceId
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
            if cls.ni_id:
                try:
                    cls.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=cls.ni_id)
                except Exception as error:
                    err = error  
            if cls.subnet_id:
                try:
                    delete_subnet(cls.a1_r1, cls.subnet_id)
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
            super(Test_AssignPrivateIpAddresses, cls).teardown_class()

    def test_T4096_valid_params_with_private_ip(self):
        private_ip = '10.0.1.{}'.format(*random.sample(range(10, 100), 1))
        try:
            res = self.a1_r1.fcu.AssignPrivateIpAddresses(NetworkInterfaceId=self.ni_id, PrivateIpAddress=private_ip)
            assert res.response.osc_return
        finally:
            self.a1_r1.fcu.UnassignPrivateIpAddresses(NetworkInterfaceId=self.ni_id, PrivateIpAddress=private_ip)
            
    def test_T4097_valid_params_with_second_ip_in_range(self):
        res = self.a1_r1.fcu.AssignPrivateIpAddresses(NetworkInterfaceId=self.ni_id, SecondaryPrivateIpAddressCount=2)
        assert res.response.osc_return

    def test_T4098_without_params(self):
        try:
            self.a1_r1.fcu.AssignPrivateIpAddresses()
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: NetworkInterfaceId")

    def test_T4099_only_network_interface_id(self):
        try:
            self.a1_r1.fcu.AssignPrivateIpAddresses(NetworkInterfaceId=self.ni_id)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter",
                         "Insufficient parameters provided out of: IpsCount, privateIpAddresses. Expected at least: 1")
