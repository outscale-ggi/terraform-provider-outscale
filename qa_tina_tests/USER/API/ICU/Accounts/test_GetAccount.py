
from specs.check_tools import check_response
from qa_test_tools.test_base import OscTestSuite

class Test_GetAccount(OscTestSuite):

    def test_T5751_without_params(self):
        resp = self.a1_r1.icu.GetAccount().response
        check_response(resp, "icu.GetAccountResponse")

    def test_T5752_with_extra_param(self):
        resp = self.a1_r1.icu.GetAccount(Foo='Bar').response
        check_response(resp, "icu.GetAccountResponse")
