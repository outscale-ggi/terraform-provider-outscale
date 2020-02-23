from qa_common_tools.test_base import OscTestSuite


class Kms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Kms, cls).setup_class()
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
            super(Kms, cls).teardown_class()
