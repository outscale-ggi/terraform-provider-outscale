import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state



class Test_DeleteRouteTable(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.info = None
        cls.route_table_id = None
        cls.net = None
        super(Test_DeleteRouteTable, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteRouteTable, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteRouteTable, self).setup_method(method)
        try:
            self.net = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response.Net.NetId
            wait_vpcs_state(self.a1_r1, [self.net], state='available')
            self.route_table_id = self.a1_r1.oapi.CreateRouteTable(NetId=self.net).response.RouteTable.RouteTableId
        except:
            try:
                self.teardown_method(method)
            finally:
                raise

    def teardown_method(self, method):
        try:
            if self.net:
                cleanup_vpcs(self.a1_r1, vpc_id_list=[self.net], force=True)
        finally:
            super(Test_DeleteRouteTable, self).teardown_method(method)

    def test_T2762_with_valid_params(self):
        try:
            ret = self.a1_r1.oapi.DeleteRouteTable(RouteTableId=self.route_table_id)
            ret.check_response()
        except OscApiException as error:
            check_oapi_error(error)

    def test_T2821_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.DeleteRouteTable(RouteTableId=self.route_table_id, DryRun=True)
        assert_dry_run(ret)

    def test_T2763_with_inexistante_route_table_id(self):
        try:
            self.a1_r1.oapi.DeleteRouteTable(RouteTableId='rtb-9b0bbbfb')
        except OscApiException as error:
            check_oapi_error(error, 5046, id='rtb-9b0bbbfb')

    def test_T2764_with_invalid_prefix_route_table_id(self):
        try:
            self.a1_r1.oapi.DeleteRouteTable(RouteTableId='toto')
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='toto', prefixes='rtb-')

    @pytest.mark.tag_sec_confidentiality
    def test_T3490_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteRouteTable(RouteTableId=self.route_table_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5046, id=self.route_table_id)

    def test_T3491_invalid_dry_run(self):
        try:
            ret = self.a1_r1.oapi.DeleteRouteTable(DryRun=True)
            assert_dry_run(ret)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
