from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_CreateLBCookieStickinessPolicy(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.lb_name = id_generator(prefix='lb')
        cls.lb = None
        super(Test_CreateLBCookieStickinessPolicy, cls).setup_class()
        try:
            cls.lb = create_load_balancer(cls.a1_r1, lb_name=cls.lb_name)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb:
                delete_lbu(cls.a1_r1, cls.lb_name)
        finally:
            super(Test_CreateLBCookieStickinessPolicy, cls).teardown_class()

    def test_T2757_valid_params(self):
        self.a1_r1.lbu.CreateLBCookieStickinessPolicy(LoadBalancerName=self.lb_name, PolicyName='policyname')
