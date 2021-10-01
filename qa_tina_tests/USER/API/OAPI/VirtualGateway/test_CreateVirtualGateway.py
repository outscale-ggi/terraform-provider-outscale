
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


class Test_CreateVirtualGateway(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_CreateVirtualGateway, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateVirtualGateway, cls).teardown_class()

    def test_T2367_valid_params(self):
        vgw_id = None
        try:
            vgw_id = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId
        finally:
            if vgw_id:
                try:
                    self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                except:
                    print('Could not delete virtual gateway')

    def test_T2368_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1', DryRun=True)
        assert_dry_run(ret)

    def test_T5943_exceeding_quota(self):
        vgw_ids = []
        try:
            for _ in range(6):
                vgw_ids.append(self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId)
        except OscApiException as error:
            if error.status_code  == 400 and error.message == "DefaultError":
                known_error("API-387", "CreateVirtualGateway: DefaultError instead of TooManyResources (QuotaExceded)")
            assert False, 'Remove known error code'
        finally:
            if vgw_ids:
                try:
                    for vgw_id in vgw_ids:
                        self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                except:
                    print('Could not delete virtual gateway')
