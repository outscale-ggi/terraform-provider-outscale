
from specs.check_tools import check_response
from qa_sdk_common.exceptions.osc_exceptions import OscSdkException
from qa_test_tools.test_base import OscTestSuite, known_error

class Test_GetAccount(OscTestSuite):

    def test_T5751_without_params(self):
        resp = self.a1_r1.icu.GetAccount().response
        try:
            check_response(resp, "icu.GetAccountResponse")
            assert False, 'Remove known error code'
        except OscSdkException:
            known_error('TINA-6598', 'Could not analyze response')

    def test_T5752_with_extra_param(self):
        resp = self.a1_r1.icu.GetAccount(Foo='Bar').response
        try:
            check_response(resp, "icu.GetAccountResponse")
            assert False, 'Remove known error code'
        except OscSdkException:
            known_error('TINA-6598', 'Could not analyze response')
