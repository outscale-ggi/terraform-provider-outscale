# pylint: disable=missing-docstring

import re

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.test_base import known_error


class Test_CreateUser(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateUser, cls).setup_class()
        cls.user_list = []

    @classmethod
    def teardown_class(cls):
        for user_name in cls.user_list:
            cls.a1_r1.eim.DeleteUser(UserName=user_name)
        super(Test_CreateUser, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T1427_required_param(self):
        user_list = [id_generator(prefix='user_0123456789'),
                     id_generator(prefix='user_abcdefghijklmnopqrstuvwxyz'),
                     id_generator(prefix='user_ABCDEFGHIJKLMNOPQRSTUVWXYZ+=,.@-_')
                    ]
        for user_name in user_list:
            ret = self.a1_r1.eim.CreateUser(UserName=user_name)
            self.user_list.append(user_name)
            assert ret.response.CreateUserResult.User.UserName == user_name
            pattern = re.compile('[A-Z0-9]{30,32}')
            assert re.match(pattern, ret.response.CreateUserResult.User.UserId) is not None
            assert ret.response.CreateUserResult.User.Path == "/"
            assert ret.response.CreateUserResult.User.Arn == "arn:aws:iam::{}:user/{}".format(self.a1_r1.config.account.account_id, user_name)

    def test_T1428_without_user_name(self):
        try:
            self.a1_r1.eim.CreateUser()
            assert False, "CreateUser must fail without UserName"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "Invalid arguments for createUser(): [arg0.userName: may not be empty]")
        known_error("TINA-4045", "Wrong error message")

    def test_T1429_invalid_user_name(self):
        try:
            user_name = id_generator(prefix='user_', size=60)
            self.a1_r1.eim.CreateUser(UserName=user_name)
            self.user_list.append(user_name)
            assert False, "CreateUser must fail with invalid UserName"
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "Invalid IdauthUser: [name: size must be between 1 and 64]")
        char_list = "!\"#$%&'()*/;<>?[\\]^`{|}~:"
        for char in char_list:
            try:
                user_name = id_generator(prefix='user_{}_'.format(char))
                self.a1_r1.eim.CreateUser(UserName=user_name)
                self.user_list.append(user_name)
                assert False, "CreateUser must fail with invalid UserName"
            except OscApiException as error:
                if char == ':':
                    assert_error(error, 400, "ValidationError", 'Invalid arguments for isAuthorized(): [arg0.resources[].relativeId: Invalid composite name part]')
                    known_error('TINA-5761', 'Unexpected error message')
                else:
                    assert_error(error, 400, "ValidationError",
                                 "Invalid IdauthUser: [name: must contain only alphanumeric characters and/or +=,.@-_ characters]")
        assert False, 'Remove known error code'

    def test_T1430_with_path(self):
        user_name = id_generator(prefix='user_')
        path = "/0123456789/ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz/"
        ret = self.a1_r1.eim.CreateUser(UserName=user_name, Path=path)
        self.user_list.append(user_name)
        assert ret.response.CreateUserResult.User.UserName == user_name
        pattern = re.compile('[A-Z0-9]{30,32}')
        assert re.match(pattern, ret.response.CreateUserResult.User.UserId) is not None
        assert ret.response.CreateUserResult.User.Path == path
        assert ret.response.CreateUserResult.User.Arn == "arn:aws:iam::{}:user{}{}".format(self.a1_r1.config.account.account_id, path, user_name)

    def test_T1431_invalid_path(self):
        try:
            user_name = id_generator(prefix='user_')
            path = "/" + id_generator(size=511) + "/"
            self.a1_r1.eim.CreateUser(UserName=user_name, Path=path)
            self.user_list.append(user_name)
            assert False, "CreateUser must fail with invalid Path {}".format(path)
        except OscApiException as error:
            assert_error(error, 400, "ValidationError", "Invalid IdauthUser: [path: size must be between 1 and 512]")
        path_list = ["test", "/test", "test/"]
        for path in path_list:
            try:
                user_name = id_generator(prefix='user_')
                self.a1_r1.eim.CreateUser(UserName=user_name, Path=path)
                self.user_list.append(user_name)
                assert False, "CreateUser must fail with invalid Path {}".format(path)
            except OscApiException as error:
                assert_error(error, 400, "ValidationError",
                            "Invalid IdauthUser: [path: must begin and end with / and contain only alphanumeric characters " \
                            +"and/or /_ characters]")
        char_list = "!\"#$%&'()*+,-.;<=>?@[\\]^`{|}~:"
        for char in char_list:
            try:
                user_name = id_generator(prefix='user_')
                path = "/{}/".format(char)
                self.a1_r1.eim.CreateUser(UserName=user_name, Path=path)
                self.user_list.append(user_name)
                assert False, "CreateUser must fail with invalid Path {}".format(path)
            except OscApiException as error:
                if char == ':':
                    assert_error(error, 400, "ValidationError", 'Invalid arguments for isAuthorized(): [arg0.resources[].relativeId: Invalid composite name part]')
                    known_error('TINA-5761', 'Unexpected error message')
                else:
                    assert_error(error, 400, "ValidationError",
                             "Invalid IdauthUser: [path: must begin and end with / and contain only alphanumeric characters " \
                             +"and/or /_ characters]")
        assert False, 'Remove known error code'
#                 if error.status_code == 500 and error.message == 'Internal Error':
#                     known_error('TINA-5530', 'EIM CreateGroup: Internal error when using a colon in group name')
#                 assert_error(error, 400, "ValidationError",
#                              "Invalid IdauthUser: [path: must begin and end with / and contain only alphanumeric characters " \
#                              +"and/or /_ characters]")
#         assert False, 'Remove known error code'
#         known_error("TINA-4045", "Wrong error message")

    def test_T3659_with_existing_user_name(self):
        user_name = id_generator(prefix='user_')
        self.a1_r1.eim.CreateUser(UserName=user_name)
        self.user_list.append(user_name)
        try:
            self.a1_r1.eim.CreateUser(UserName=user_name)
            self.user_list.append(user_name)
            assert False, "CreateUser must fail with invalid UserName"
        except OscApiException as error:
            assert_error(error, 409, 'EntityAlreadyExists', 'User with name {} already exists.'.format(user_name))
