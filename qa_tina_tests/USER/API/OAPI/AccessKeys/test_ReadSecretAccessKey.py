
import pytest

from specs import check_tools
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite


class Test_ReadSecretAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadSecretAccessKey, cls).setup_class()
        cls.ak = cls.a1_r1.config.account.ak

    @classmethod
    def teardown_class(cls):
        super(Test_ReadSecretAccessKey, cls).teardown_class()

    def test_T5667_missing_ak(self):
        try:
            self.a1_r1.oapi.ReadSecretAccessKey()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5668_valid_ak(self):
        ret = self.a1_r1.oapi.ReadSecretAccessKey(AccessKeyId=self.ak)
        check_tools.check_oapi_response(ret.response, 'ReadSecretAccessKeyResponse')
        assert ret.response.AccessKey
        assert ret.response.AccessKey.AccessKeyId == self.ak
        assert ret.response.AccessKey.SecretKey == self.a1_r1.config.account.sk

    def test_T5669_dry_run(self):
        ret = self.a1_r1.oapi.ReadSecretAccessKey(AccessKeyId=self.ak, DryRun=True)
        misc.assert_dry_run(ret)

    def test_T5670_only_unknown_param(self):
        try:
            self.a1_r1.oapi.ReadSecretAccessKey(Foo='Bar')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T5671_additional_unknown_param(self):
        try:
            self.a1_r1.oapi.ReadSecretAccessKey(AccessKeyId=self.ak, Foo='Bar')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T5672_invalid_ak(self):
        ret = self.a1_r1.oapi.ReadSecretAccessKey(AccessKeyId='foobar')
        assert not hasattr(ret.response, 'AccessKey')

    def test_T5673_unknown_ak(self):
        ret = self.a1_r1.oapi.ReadSecretAccessKey(AccessKeyId='12345678901234567890')
        assert not hasattr(ret.response, 'AccessKey')

    def test_T5674_invalid_ak_type(self):
        try:
            self.a1_r1.oapi.ReadSecretAccessKey(AccessKeyId=[self.ak])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5675_ak_other_account(self):
        if not hasattr(self, 'a2_r1'):
            pytest.fail('This test requires 2 accounts.')
        try:
            self.a2_r1.oapi.ReadSecretAccessKey(AccessKeyId=self.a2_r1.config.account.ak)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 401, 'AccessDenied', '1')
