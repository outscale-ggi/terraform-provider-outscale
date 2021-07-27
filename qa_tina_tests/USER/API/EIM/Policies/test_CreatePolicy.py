from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_tina_tools.test_base import OscTinaTest


class Test_CreatePolicy(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_CreatePolicy, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreatePolicy, cls).teardown_class()

    def test_T2621_without_action(self):
        try:
            self.a1_r1.eim.CreatePolicy(PolicyName='test', PolicyDocument='{"Statement": [{"Action": [], "Resource": ["*"], "Effect": "Deny"}]}')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', None)
