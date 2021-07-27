from qa_test_tools.misc import assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.wait_tools import wait_internet_gateways_state


class Test_CreateInternetService(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_CreateInternetService, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateInternetService, cls).teardown_class()

    def test_T2238_valid_params(self):
        net_id = None
        try:
            ret = self.a1_r1.oapi.CreateInternetService()
            ret.check_response()
            net_id = ret.response.InternetService.InternetServiceId
            wait_internet_gateways_state(self.a1_r1, [net_id], state='available')
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id)
                except:
                    print('Could not delete internet service')

    def test_T2239_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateInternetService(DryRun=True)
        assert_dry_run(ret)
