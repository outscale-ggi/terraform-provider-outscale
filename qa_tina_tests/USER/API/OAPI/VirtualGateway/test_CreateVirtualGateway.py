from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import OscTestSuite


class Test_CreateVirtualGateway(OscTestSuite):

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
                    pass

    def test_T2368_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateVirtualGateway(ConnectionType='ipsec.1', DryRun=True)
        assert_dry_run(ret)
