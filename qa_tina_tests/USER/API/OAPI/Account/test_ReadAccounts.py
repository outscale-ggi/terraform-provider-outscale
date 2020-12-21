from qa_test_tools.test_base import OscTestSuite


class Test_ReadAccounts(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadAccounts, cls).setup_class()
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_ReadAccounts, cls).teardown_class()

    def test_T4761_valid_call(self):
        ret = self.a1_r1.oapi.ReadAccounts()
        ret.check_response()
