from qa_common_tools.test_base import OscTestSuite


class Test_DeleteRoute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteRoute, cls).setup_class()
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
            super(Test_DeleteRoute, cls).teardown_class()
