from qa_tina_tools.test_base import OscTinaTest


class Test_ReadAccounts(OscTinaTest):

    def test_T4761_valid_call(self):
        ret = self.a1_r1.oapi.ReadAccounts()
        ret.check_response()
        assert ret.response.Accounts[0].AccountId
        assert ret.response.Accounts[0].City
        assert ret.response.Accounts[0].CompanyName
        assert ret.response.Accounts[0].Country
        assert ret.response.Accounts[0].Email
        assert ret.response.Accounts[0].FirstName
        assert ret.response.Accounts[0].LastName
        assert ret.response.Accounts[0].ZipCode
