
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest


class Test_CreateVirtualGateway(OscTinaTest):

    @classmethod
    def setup_class(cls):
        # TODO add quota on virtual gateway, do no rely on default quota
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
        misc.assert_dry_run(ret)

    def test_T5943_exceeding_quota(self):
        vgw_ids = []
        try:
            for _ in range(6):
                vgw_ids.append(self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1').response.VirtualGateway.VirtualGatewayId)
            assert False, 'Last call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 10039)
        finally:
            if vgw_ids:
                try:
                    for vgw_id in vgw_ids:
                        self.a1_r1.oapi.DeleteVirtualGateway(VirtualGatewayId=vgw_id)
                except:
                    print('Could not delete virtual gateway')
