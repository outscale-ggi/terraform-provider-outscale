from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import id_generator, assert_error
from osc_common.exceptions.osc_exceptions import OscApiException


class Test_UpdateGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateGroup, cls).setup_class()
        cls.group = None

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        group_name = id_generator(prefix='group_name_')
        path = '/FirstPath/'
        self.group = None
        try:
            self.group = self.a1_r1.eim.CreateGroup(GroupName=group_name, Path=path).response.CreateGroupResult.Group
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.group:
                self.a1_r1.eim.DeleteGroup(GroupName=self.group.GroupName)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T3932_with_only_group_name_param(self):
        tmpGroupName = self.group.GroupName
        tmpGroupPath = self.group.Path
        self.a1_r1.eim.UpdateGroup(GroupName=self.group.GroupName)
        assert self.group.GroupName == tmpGroupName
        assert self.group.Path == tmpGroupPath

    def test_T3934_with_new_path(self):
        newpath = '/SecondPath/'
        self.a1_r1.eim.UpdateGroup(GroupName=self.group.GroupName, NewPath=newpath)
        ret = self.a1_r1.eim.GetGroup(GroupName=self.group.GroupName)
        assert ret.response.GetGroupResult.Group.GroupName == self.group.GroupName
        assert ret.response.GetGroupResult.Group.Path == newpath

    def test_T3936_without_group_name(self):
        try:
            self.a1_r1.eim.UpdateGroup()
            assert False, "UpdateGroup must fail without GroupName"
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'GroupName may not be empty')

    def test_T3937_with_invalid_group_name(self):
        try:
            self.a1_r1.eim.UpdateGroup(GroupName='totitito')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', 'Cannot find group [path=*, name=totitito] for account [arn:aws:iam::{}:account]'
                         .format(self.a1_r1.config.account.account_id))

    def test_T3939_with_invalid_path(self):
        invalidpathname = '/InvalidPath'
        try:
            self.a1_r1.eim.UpdateGroup(GroupName=self.group.GroupName, NewPath=invalidpathname)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400,
                         'ValidationError', 'Path must begin and end with / and contain only alphanumeric characters and/or /_ characters')

    def test_T3940_with_invalid_new_group_name(self):
        invalidnewgroupname = id_generator(prefix='group_', size=130)
        try:
            self.a1_r1.eim.UpdateGroup(GroupName=self.group.GroupName, NewGroupName=invalidnewgroupname)
            self.group.GroupName = invalidnewgroupname
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'Name size must be between 1 and 128')

    def test_T3942_with_new_group_name_from_other_account(self):
        name = id_generator(prefix='other_group_name_')
        try:
            self.a2_r1.eim.UpdateGroup(GroupName=self.group.GroupName, NewGroupName=name)
            self.group.GroupName = name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 404, 'NoSuchEntity', 'Cannot find group [path=*, name={}] for account [arn:aws:iam::{}:account]'
                         .format(self.group.GroupName, self.a2_r1.config.account.account_id))

    def test_T4052_with_new_group_name_param(self):
        ret = self.a1_r1.eim.GetGroup(GroupName=self.group.GroupName)
        assert ret.response.GetGroupResult.Group.GroupName == self.group.GroupName
        newname = id_generator(prefix='new_group_name_')
        ret = self.a1_r1.eim.UpdateGroup(GroupName=self.group.GroupName, NewGroupName=newname)
        assert ret.response.ResponseMetadata.RequestId
        ret = self.a1_r1.eim.GetGroup(GroupName=newname)
        assert ret.response.GetGroupResult.Group.GroupName == newname
        self.group.GroupName = newname
