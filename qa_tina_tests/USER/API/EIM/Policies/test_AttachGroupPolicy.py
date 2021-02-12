from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_AttachGroupPolicy(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AttachGroupPolicy, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_AttachGroupPolicy, cls).teardown_class()

    def test_T3234_nonexisting_policyarn(self):
        group_name = id_generator(prefix='user_')
        path = id_generator(prefix='/') + '/'
        ret_create_group = None
        ret_attach_policy = None
        try:
            ret_create_group = self.a1_r1.eim.CreateGroup(GroupName=group_name, Path=path)

            ret_attach_policy = self.a1_r1.eim.AttachGroupPolicy(GroupName=group_name, PolicyArn='toto')
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'ARN toto is not valid.')
        finally:
            if ret_attach_policy:
                self.a1_r1.eim.DetachGroupPolicy(GroupName=group_name, PolicyArn='toto')
            if ret_create_group:
                self.a1_r1.eim.DeleteGroup(GroupName=group_name)
