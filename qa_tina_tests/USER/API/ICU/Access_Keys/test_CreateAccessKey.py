import re

from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_CreateAccessKey(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'accesskey_limit': 10}
        super(Test_CreateAccessKey, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateAccessKey, cls).teardown_class()

    def test_T3966_non_authenticated(self):
        sleep(30)
        ret_create = None
        try:
            tag = [{'Key': 'Name', 'Value': 'Marketplace'}]
            ret_create = self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty}, Tag=tag)
            ak = ret_create.response.accessKey.accessKeyId
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'IcuClientException', 'Field AuthenticationMethod is required')
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T344_without_param(self):
        sleep(30)
        ret_create = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            sk = ret_create.response.accessKey.secretAccessKey
            assert ret_create.response.accessKey.ownerId
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.accessKey.status == 'ACTIVE'
            if self.a1_r1.config.account.account_id:
                assert ret_create.response.accessKey.ownerId == self.a1_r1.config.account.account_id
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T352_valid_tags(self):
        sleep(30)
        ret_create = None
        try:
            tag = [{'Key': 'Name', 'Value': 'Marketplace'}]
            ret_create = self.a1_r1.icu.CreateAccessKey(Tag=tag)
            ak = ret_create.response.accessKey.accessKeyId
            sk = ret_create.response.accessKey.secretAccessKey
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.accessKey.status == 'ACTIVE'
            assert ret_create.response.accessKey.ownerId == self.a1_r1.config.account.account_id
            assert ret_create.response.accessKey.tags != [], 'Tags list is empty, an tag was expected'
        except AssertionError as error:
            known_error('TINA-3930', str(error))
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
        assert False, 'Remove known error code'

    # TODO to be checked
    def test_T353_not_supported_tags(self):
        sleep(30)
        ret_create = None
        try:
            tag = [{'Key': 'test', 'Value': 'test'}]
            ret_create = self.a1_r1.icu.CreateAccessKey(Tag=tag)
            ak = ret_create.response.accessKey.accessKeyId
            sk = ret_create.response.accessKey.secretAccessKey
            assert re.search(r"([A-Z0-9]{20})", ak), "AK format is not correct"
            assert re.search(r"([A-Z0-9]{40})", sk), "SK format is not correct"
            assert ret_create.response.accessKey.status == 'ACTIVE'
            assert ret_create.response.accessKey.ownerId == self.a1_r1.config.account.account_id
            # TODO: verify tags
            assert ret_create.response.accessKey.tags != [], 'Tags list is empty, an tag was expected'
        except AssertionError as error:
            known_error('TINA-3930', str(error))
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)
        assert False, 'Remove known error code'

    def test_T354_param_ak_sk(self):
        sleep(30)
        ret_create = None
        try:
            ak = id_generator(size=20)
            sk = id_generator(size=40)
            ret_create = self.a1_r1.icu.CreateAccessKey(AccessKeyId=ak, SecretAccessKey=sk)
            assert ak == ret_create.response.accessKey.accessKeyId, "AccesskeyID created does not correspond AccesskeyID passed"
            assert sk == ret_create.response.accessKey.secretAccessKey, "SecrretAccesskey created does not correspond SecrretAccesskey passed"
        except AssertionError as error:
            known_error('TINA-3930', str(error))
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create.response.accessKey.accessKeyId)
        assert False, 'Remove known error code'

    def test_T3972_param_method_authAkSk(self):
        sleep(30)
        ret_create = None
        try:
            ak = id_generator(size=20)
            sk = id_generator(size=40)
            ret_create = self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.AkSk})
            assert ak == ret_create.response.accessKey.accessKeyId, "AccesskeyID created does not correspond AccesskeyID passed"
            assert sk == ret_create.response.accessKey.secretAccessKey, "SecrretAccesskey created does not correspond SecrretAccesskey passed"
        except AssertionError as error:
            known_error('TINA-3930', str(error))
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create.response.accessKey.accessKeyId)
        assert False, 'Remove known error code'

    def test_T3971_param_method_authPassword(self):
        sleep(30)
        ret_create = None
        try:
            ak = id_generator(size=20)
            sk = id_generator(size=40)
            ret_create = self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
            assert ak == ret_create.response.accessKey.accessKeyId, "AccesskeyID created does not correspond AccesskeyID passed"
            assert sk == ret_create.response.accessKey.secretAccessKey, "SecrretAccesskey created does not correspond SecrretAccesskey passed"
        except AssertionError as error:
            known_error('TINA-3930', str(error))
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create.response.accessKey.accessKeyId)
        assert False, 'Remove known error code'

    def test_T360_param_ak_sk_already_existing(self):
        sleep(30)
        ret_create = None
        try:
            ret_create = self.a1_r1.icu.CreateAccessKey()
            ak = ret_create.response.accessKey.accessKeyId
            sk = ret_create.response.accessKey.secretAccessKey
            sleep(30)
            ret_create_bis = self.a1_r1.icu.CreateAccessKey(AccessKeyId=ak, SecretAccessKey=sk)
            try:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create_bis.response.accessKey.accessKeyId)
                known_error('TINA-3930', "Call should not have been successful, existing ak sk")
            except OscApiException as error:
                assert False, 'Remove known error code'
                assert error.status_code == 400
                assert error.message == "xxx"
        finally:
            if ret_create:
                sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak)

    def test_T355_param_ak_without_sk(self):
        sleep(30)
        ret_create = None
        try:
            ak = id_generator(size=20)
            ret_create = self.a1_r1.icu.CreateAccessKey(AccessKeyId=ak)
            ak_after_reply = ret_create.response.accessKey.accessKeyId
            assert ak == ak_after_reply, "AccesskeyID created does not correspond AccesskeyID passed"
        except AssertionError as error:
            known_error('TINA-3930', str(error))
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ak_after_reply)
        assert False, 'Remove known error code'

    def test_T356_param_without_ak_sk(self):
        sleep(30)
        ret_create = None
        try:
            sk = id_generator(size=40)
            ret_create = self.a1_r1.icu.CreateAccessKey(SecretAccessKey=sk)
            sk_after_reply = ret_create.response.accessKey.secretAccessKey
            assert sk == sk_after_reply, "SecretkeyID created does not correspond SecretkeyID passed"
        except AssertionError as error:
            known_error('TINA-3930', str(error))
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create.response.accessKey.accessKeyId)
        assert False, 'Remove known error code'

    def test_T357_param_wrong_format_ak_wrong_format_sk(self):
        sleep(30)
        ret_create = None
        try:
            sk = id_generator(size=30)
            ak = id_generator(size=10)
            ret_create = self.a1_r1.icu.CreateAccessKey(SecretAccessKey=sk, AccessKeyId=ak)
            known_error('TINA-3930', 'test should have failed')
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert error.status_code == '400'
            assert error.message == 'xxx'
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create.response.accessKey.accessKeyId)

    def test_T358_param_wrong_format_ak_sk(self):
        sleep(30)
        ret_create = None
        try:
            sk = id_generator(size=40)
            ak = id_generator(size=10)
            ret_create = self.a1_r1.icu.CreateAccessKey(SecretAccessKey=sk, AccessKeyId=ak)
            known_error('TINA-3930', 'test should have failed')
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert error.status_code == '400'
            assert error.message == 'xxx'
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create.response.accessKey.accessKeyId)

    def test_T359_param_ak_wrong_format_sk(self):
        sleep(30)
        ret_create = None
        try:
            sk = id_generator(size=30)
            ak = id_generator(size=20)
            ret_create = self.a1_r1.icu.CreateAccessKey(SecretAccessKey=sk, AccessKeyId=ak)
            # sk_after_reply = ret_create.response.accessKey.secretAccessKey
            # ak_after_reply = ret_create.response.accessKey.accessKeyId
            known_error('TINA-3930', 'test should have failed')
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert error.status_code == '400'
            assert error.message == 'xxx'
        finally:
            if ret_create:
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=ret_create.response.accessKey.accessKeyId)

    def test_T3772_check_throttling(self):
        sleep(30)
        found_error = False
        key_id_list = []
        osc_api.disable_throttling()
        try:
            key_id_list.append(self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.accessKey.accessKeyId)
            for _ in range(3):
                try:
                    key_id_list.append(self.a1_r1.icu.CreateAccessKey(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.accessKey.accessKeyId)
                except OscApiException as error:
                    if error.status_code == 503:
                        found_error = True
                    else:
                        raise error
            assert found_error, "Throttling did not happen"
        finally:
            osc_api.enable_throttling()
            for key_id in key_id_list:
                if key_id != key_id_list[0]:
                    sleep(30)
                self.a1_r1.icu.DeleteAccessKey(AccessKeyId=key_id)
