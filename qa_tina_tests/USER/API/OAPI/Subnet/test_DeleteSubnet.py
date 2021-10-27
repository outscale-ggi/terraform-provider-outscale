from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import SUBNETS, SUBNET_ID, VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state


class Test_DeleteSubnet(OscTinaTest):

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
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info[VPC_ID]], force=True)
        finally:
            super(Test_DeleteSubnet, cls).teardown_class()

    def test_T2260_valid_params(self):
        self.a1_r1.oapi.DeleteSubnet(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID])

    def test_T2261_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.DeleteSubnet(SubnetId=self.vpc_info[SUBNETS][0][SUBNET_ID], DryRun=True)
        assert_dry_run(ret)

    def test_T2571_missing_resource_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2572_invalid_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId='subnet-toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4105, given_id='subnet-toto')

    def test_T2573_invalid_prefix_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId='titi-toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='titi-toto', prefixes='subnet-')

    def test_T2574_inexistant_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId='subnet-0246d185')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 5057, id='subnet-0246d185')

    def test_T2575_incorrect_id_type(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(SubnetId=True)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4110)

    def test_T2576_too_many_subnet_id(self):
        try:
            self.a1_r1.oapi.DeleteSubnet(
                SubnetId=[self.vpc_info[SUBNETS][1][SUBNET_ID], self.vpc_info[SUBNETS][2][SUBNET_ID]])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4110)

    def test_T2577_subnet_from_diffrent_user(self):
        try:
            self.a2_r1.oapi.DeleteSubnet(SubnetId=self.vpc_info[SUBNETS][3][SUBNET_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 5057, id=self.vpc_info[SUBNETS][3][SUBNET_ID])
