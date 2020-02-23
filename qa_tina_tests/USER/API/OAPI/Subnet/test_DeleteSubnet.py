from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import assert_dry_run, assert_oapi_error
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import SUBNETS, SUBNET_ID, VPC_ID


class Test_DeleteSubnet(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteSubnet, cls).setup_class()
        cls.vpc_info = {}
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=4)
            wait_vpcs_state(cls.a1_r1, [cls.vpc_info[VPC_ID]], state='available')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info[VPC_ID]], force=True)
        except:
            pass
        finally:
            super(Test_DeleteSubnet, cls).teardown_class()

    def test_T2260_valid_params(self):
        self.a1_r1.oapi.DeleteSubnet(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])

    def test_T2261_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.DeleteSubnet(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], DryRun=True)
        assert_dry_run(ret)

    def test_T2571_missing_resource_id(self):
        try:
            ret = self.a1_r1.oapi.DeleteSubnet()
            assert False, 'Call should not have been successful'
            assert_dry_run(ret)
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T2572_invalid_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId='subnet-toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4105')

    def test_T2573_invalid_prefix_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId='titi-toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4104')

    def test_T2574_inexistant_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId='subnet-0246d185')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5057')

    def test_T2575_incorrect_id_type(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId=True)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4110')

    def test_T2576_too_many_subnet_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(
                SubnetId=[self.vpc_info[SUBNETS][1][SUBNET_ID], self.vpc_info[SUBNETS][2][SUBNET_ID]])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4110')

    def test_T2577_subnet_from_diffrent_user(self):
        try:
            self.a2_r1.oapi.DeleteSubnet(SubnetId=self.vpc_info[SUBNETS][3][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidResource', '5057')
