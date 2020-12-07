from qa_test_tools.test_base import OscTestSuite
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs


class Test_CreateRouteTable(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateRouteTable, cls).setup_class()
        cls.net = None
        try:
            cls.net = cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response.Net.NetId
            wait_vpcs_state(cls.a1_r1, [cls.net], state='available')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.net:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.net], force=True)
        finally:
            super(Test_CreateRouteTable, cls).teardown_class()

    def test_T2758_without_param(self):
        try:
            self.a1_r1.oapi.CreateRouteTable()
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2759_with_valid_params(self):
        ret = self.a1_r1.oapi.CreateRouteTable(NetId=self.net)
        ret.check_response()

    def test_T2820_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateRouteTable(NetId=self.net, DryRun=True)
        assert_dry_run(ret)

    def test_T2760_with_invalid_net_id(self):
        try:
            self.a1_r1.oapi.CreateRouteTable(NetId='vpc-toto')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2761_with_unknown_net_id(self):
        try:
            self.a1_r1.oapi.CreateRouteTable(NetId='vpc-76ce8cb1')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5065')
