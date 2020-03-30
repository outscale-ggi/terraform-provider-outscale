from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_test_tools.misc import id_generator
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_CreateStickyCookiePolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.lb_name = id_generator(prefix='lb')
        cls.lb = None
        super(Test_CreateStickyCookiePolicy, cls).setup_class()
        try:
            cls.lb = create_load_balancer(cls.a1_r1, lb_name=cls.lb_name)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb:
                delete_lbu(cls.a1_r1, cls.lb_name)
        finally:
            super(Test_CreateStickyCookiePolicy, cls).teardown_class()
