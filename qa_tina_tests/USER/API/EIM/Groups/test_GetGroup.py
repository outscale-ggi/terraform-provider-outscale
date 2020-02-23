from datetime import datetime
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite


class Test_GetGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_GetGroup, cls).setup_class()
        cls.group = None
        cls.group_name = id_generator(prefix='group_')
        try:
            cls.group = cls.a1_r1.eim.CreateGroup(GroupName=cls.group_name)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.group:
                cls.a1_r1.eim.DeleteGroup(GroupName=cls.group_name)
        finally:
            super(Test_GetGroup, cls).teardown_class()

    def test_T3876_with_invalid_group_name(self):
        try:
            self.a1_r1.eim.GetGroup(GroupName='tiitii')
            assert False, 'GetGroup must fail with invalid GroupName'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', 'Cannot find group [path=*, name=tiitii] for account [arn:aws:iam::{}:account]'
                         .format(self.a1_r1.config.account.account_id))

    def test_T3877_with_group_name(self):
        ret = self.a1_r1.eim.GetGroup(GroupName=self.group_name)
        assert ret.response.GetGroupResult.Group.Arn == 'arn:aws:iam::{}:group/{}'.format(self.a1_r1.config.account.account_id, self.group_name)
        assert datetime.strptime(ret.response.GetGroupResult.Group.CreateDate, '%Y-%m-%dT%H:%M:%S.%fZ')
        assert ret.response.GetGroupResult.Group.GroupId
        assert ret.response.GetGroupResult.Group.GroupName == self.group_name
        assert ret.response.GetGroupResult.Group.Path == '/'

    def test_T3878_with_group_name_from_other_account(self):
        try:
            self.a2_r1.eim.GetGroup(GroupName=self.group_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', "Cannot find group [path=*, name={}] for account [arn:aws:iam::{}:account]"
                         .format(self.group_name, self.a2_r1.config.account.account_id))

    def test_T3879_without_params(self):
        try:
            self.a1_r1.eim.GetGroup()
            assert False, 'GetGroup must fail with no GroupName'
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'GroupName may not be empty')
