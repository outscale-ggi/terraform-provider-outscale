from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID


class Test_CreateSubnet(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'subnet_limit': 5}
        cls.vpc_info = None
        super(Test_CreateSubnet, cls).setup_class()
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
            super(Test_CreateSubnet, cls).teardown_class()

    def test_T1713_with_valid_params(self):
        subnet_id = None
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId=self.vpc_info[VPC_ID], CidrBlock='10.0.1.0/24').response.subnet.subnetId
        finally:
            if subnet_id:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)

    def test_T1714_missing_vpc_id(self):
        subnet_id = None
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(CidrBlock='10.0.1.0/24').response.subnet.subnetId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', None)
        finally:
            if subnet_id:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)

    def test_T1715_incorrect_vpc_id(self):
        subnet_id = None
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId='xxx-12345678', CidrBlock='10.0.1.0/24').response.subnet.subnetId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.Malformed', "Invalid ID received: xxx-12345678. Expected format: vpc-")
        finally:
            if subnet_id:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)

    def test_T1716_unknown_vpc_id(self):
        subnet_id = None
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId='vpc-12345678', CidrBlock='10.0.1.0/24').response.subnet.subnetId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcID.NotFound', "The vpc ID 'vpc-12345678' does not exist")
        finally:
            if subnet_id:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)

    def test_T1717_missing_cidr_block(self):
        subnet_id = None
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId=self.vpc_info[VPC_ID]).response.subnet.subnetId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: CidrBlock')
        finally:
            if subnet_id:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)

    def test_T1718_incorrect_cidr_block(self):
        subnet_id = None
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId=self.vpc_info[VPC_ID], CidrBlock='10.0.1.0').response.subnet.subnetId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid IPv4 network: 10.0.1.0")
        finally:
            if subnet_id:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)

    def test_T1719_unknown_az(self):
        subnet_id = None
        try:
            subnet_id = self.a1_r1.fcu.CreateSubnet(VpcId=self.vpc_info[VPC_ID], CidrBlock='10.0.1.0/24',
                                                    AvailabilityZone='toto').response.subnet.subnetId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid availability zone: [toto]")
        finally:
            if subnet_id:
                self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)

    def test_T1720_too_many_subnets(self):
        subnet_ids = []
        try:
            for i in range(10):
                subnet_ids.append(self.a1_r1.fcu.CreateSubnet(VpcId=self.vpc_info[VPC_ID],
                                                              CidrBlock='10.0.{}.0/24'.format(i + 1)).response.subnet.subnetId)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'SubnetLimitExceeded', None)
        finally:
            if subnet_ids:
                for subnet_id in subnet_ids:
                    self.a1_r1.fcu.DeleteSubnet(SubnetId=subnet_id)
