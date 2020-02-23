from qa_common_tools.test_base import OscTestSuite


class Test_SetLoadBalancerListenerSSLCertificate(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_SetLoadBalancerListenerSSLCertificate, cls).setup_class()
        try:
            pass
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_SetLoadBalancerListenerSSLCertificate, cls).teardown_class()
