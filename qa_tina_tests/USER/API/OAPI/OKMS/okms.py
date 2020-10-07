from qa_test_tools.test_base import OscTestSuite


class OKMS(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(OKMS, cls).setup_class()
        try:
            cls.account_id = cls.a1_r1.config.account.account_id
            cls.account2_id = cls.a2_r1.config.account.account_id
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
            super(OKMS, cls).teardown_class()
