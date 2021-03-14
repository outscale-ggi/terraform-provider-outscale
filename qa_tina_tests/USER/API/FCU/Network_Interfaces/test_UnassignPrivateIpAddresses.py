import random

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.delete_tools import delete_subnet


class Test_UnassignPrivateIpAddresses(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.subnet_id = None
        cls.vpc_id = None
        cls.ni_id = None
        super(Test_UnassignPrivateIpAddresses, cls).setup_class()
        try:
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId
            # create subnet 1
            res_snet = cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_1_0_24'), VpcId=cls.vpc_id)
            cls.subnet_id = res_snet.response.subnet.subnetId
            res_ni = cls.a1_r1.fcu.CreateNetworkInterface(SubnetId=cls.subnet_id,
                                                       PrivateIpAddress=Configuration.get('ipaddress', '10_0_1_4'))
            cls.ni_id = res_ni.response.networkInterface.networkInterfaceId
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

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
            super(Test_UnassignPrivateIpAddresses, cls).teardown_class()

    def test_T4100_valid_params(self):
        private_ip = '10.0.1.{}'.format(*random.sample(list(range(10, 100)), 1))
        self.a1_r1.fcu.AssignPrivateIpAddresses(NetworkInterfaceId=self.ni_id, PrivateIpAddress=private_ip)
        res = self.a1_r1.fcu.UnassignPrivateIpAddresses(NetworkInterfaceId=self.ni_id, PrivateIpAddress=private_ip)
        assert res.response.osc_return

    def test_T4101_without_params(self):
        try:
            self.a1_r1.fcu.UnassignPrivateIpAddresses()
        except OscApiException as error:
            assert_error(error, 400, "MissingParameter", "Parameter cannot be empty: NetworkInterfaceId")
