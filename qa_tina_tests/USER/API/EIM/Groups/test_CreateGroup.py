
import re
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools.test_base import OscTestSuite, known_error


class Test_CreateGroup(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateGroup, cls).setup_class()

        cls.group_list = []

    @classmethod
    def teardown_class(cls):
        try:
            for group_name in cls.group_list:
                cls.a1_r1.eim.DeleteGroup(GroupName=group_name)
        finally:
            super(Test_CreateGroup, cls).teardown_class()

    def test_T1456_required_param(self):
        group_list = [id_generator(prefix='group_0123456789'),
                      id_generator(prefix='group_abcdefghijklmnopqrstuvwxyz'),
                      id_generator(prefix='group_ABCDEFGHIJKLMNOPQRSTUVWXYZ+=,.@-_')]
        for group_name in group_list:
            ret = self.a1_r1.eim.CreateGroup(GroupName=group_name)
            self.group_list.append(group_name)

            assert ret.response.CreateGroupResult.Group.GroupName == group_name
            pattern = re.compile('[A-Z0-9]{30,32}')
            assert re.match(pattern, ret.response.CreateGroupResult.Group.GroupId) is not None
            assert ret.response.CreateGroupResult.Group.Path == "/"
            assert ret.response.CreateGroupResult.Group.Arn == "arn:aws:iam::{}:group/{}".format(
                self.a1_r1.config.account.account_id, group_name)

    def test_T1457_without_group_name(self):
        try:
            self.a1_r1.eim.CreateGroup()
            assert False, "CreateGroup must fail without GroupName"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "Invalid arguments for createGroup(): [arg0.groupName: may not be empty]")
            known_error("TINA-4045", "Wrong error message")

    def test_T1458_invalid_group_name(self):
        try:
            group_name = id_generator(prefix='group_', size=123)
            self.a1_r1.eim.CreateGroup(GroupName=group_name)
            self.group_list.append(group_name)
            assert False, "CreateGroup must fail with invalid GroupName"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "Invalid IdauthGroup: [name: size must be between 1 and 128]")
        char_list = "!\"#$%&'()*/:;<>?[\\]^`{|}~"
        for char in char_list:
            try:
                group_name = id_generator(prefix='group_{}_'.format(char))
                self.a1_r1.eim.CreateGroup(GroupName=group_name)
                self.group_list.append(group_name)
                assert False, "Creategroup must fail with invalid groupName"
            except OscApiException as error:
                if error.status_code == 500 and error.message == 'Internal Error':
                    known_error('TINA-5474', 'EIM CreateGroup: Internal error when using a colon in group name')
                assert_error(error, 400, "ValidationError",
                             "Invalid IdauthGroup: [name: must contain only alphanumeric characters and/or +=,.@-_ characters]")
        assert False, 'Remove known error code'
        known_error("TINA-4045", "Wrong error message")

    def test_T1459_with_path(self):
        group_name = id_generator(prefix='user_')
        path = "/0123456789/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz/"
        ret = self.a1_r1.eim.CreateGroup(GroupName=group_name, Path=path)
        self.group_list.append(group_name)

        assert ret.response.CreateGroupResult.Group.GroupName == group_name
        pattern = re.compile('[A-Z0-9]{30,32}')
        assert re.match(pattern, ret.response.CreateGroupResult.Group.GroupId) is not None
        assert ret.response.CreateGroupResult.Group.Path == path
        assert ret.response.CreateGroupResult.Group.Arn == "arn:aws:iam::{}:group{}{}".format(
            self.a1_r1.config.account.account_id, path, group_name)

    def test_T1461_invalid_path(self):
        try:
            group_name = id_generator(prefix='group_')
            path = "/" + id_generator(size=511) + "/"
            self.a1_r1.eim.CreateGroup(GroupName=group_name, Path=path)
            self.group_list.append(group_name)
            assert False, "Creategroup must fail with invalid Path {}".format(path)
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "Invalid IdauthGroup: [path: size must be between 1 and 512]")

        path_list = ["test", "/test", "test/"]
        for path in path_list:
            try:
                group_name = id_generator(prefix='group_')
                self.a1_r1.eim.CreateGroup(GroupName=group_name, Path=path)
                self.group_list.append(group_name)
                assert False, "CreateGroup must fail with invalid Path {}".format(path)
            except OscApiException as error:
                assert_error(error, 400, "ValidationError",
                             "Invalid IdauthGroup: [path: must begin and end with / and contain only alphanumeric characters " \
                             +"and/or /_ characters]")
        char_list = "!\"#$%&'()*+,-.:;<=>?@[\\]^`{|}~"
        for char in char_list:
            try:
                group_name = id_generator(prefix='group_')
                path = "/{}/".format(char)
                self.a1_r1.eim.CreateGroup(GroupName=group_name, Path=path)
                self.group_list.append(group_name)
                assert False, "CreateGroup must fail with invalid Path {}".format(path)
            except OscApiException as error:
                assert_error(error, 400, "ValidationError",
                            "Invalid IdauthGroup: [path: must begin and end with / and contain only alphanumeric characters " \
                            +"and/or /_ characters]")
            known_error("TINA-4045", "Wrong error message")
        assert False, 'Remove known error code.'

    def test_T3777_with_existing_group_name(self):
        group_name = id_generator(prefix='group_')
        self.a1_r1.eim.CreateGroup(GroupName=group_name)
        self.group_list.append(group_name)
        try:
            self.a1_r1.eim.CreateGroup(GroupName=group_name)
            self.group_list.append(group_name)
            assert False, "CreateGoup must fail with invalid GroupName"
        except OscApiException as error:
            assert_error(error, 409, "EntityAlreadyExists", "Group with name '{}' already exists.".format(group_name))
