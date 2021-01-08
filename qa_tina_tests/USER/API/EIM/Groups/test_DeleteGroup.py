from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteGroup(OscTestSuite):

    def test_T1463_required_param(self):
        ret = self.a1_r1.eim.CreateGroup(GroupName=misc.id_generator(prefix='group_'))
        ret = self.a1_r1.eim.DeleteGroup(GroupName=ret.response.CreateGroupResult.Group.GroupName)

    def test_T1464_without_group_name(self):
        try:
            self.a1_r1.eim.DeleteGroup()
            assert False, "DeleteGroup must fail without GroupName"
        except OscApiException as error:
            misc.assert_error(error, 400, 'ValidationError', 'GroupName may not be empty')

    def test_T1465_invalid_group_name(self):
        try:
            self.a1_r1.eim.DeleteGroup(GroupName='foo')
            assert False, "DeleteGroup must fail with not existing GroupName"
        except OscApiException as error:
            misc.assert_error(error, 404, 'NoSuchEntity', 'The group with name foo cannot be found.')

    def test_T3806_with_user_name_from_other_account(self):
        group_name = misc.id_generator(prefix='group_')
        self.a1_r1.eim.CreateGroup(GroupName=group_name)
        try:
            self.a2_r1.eim.DeleteGroup(GroupName=group_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc. assert_error(error, 404, "NoSuchEntity", "The group with name {} cannot be found.".format(group_name))
        finally:
            self.a1_r1.eim.DeleteGroup(GroupName=group_name)
