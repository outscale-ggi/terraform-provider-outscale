import pytest

from qa_sdk_common.config import DefaultAccount, DefaultRegion
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_sdk_pub.osc_api import DefaultPubConfig
from qa_sdk_pub.osc_api.osc_icu_api import OscIcuApi
from qa_sdk_pub.osc_api.osc_pub_api import OscPubApi
from qa_test_tools import misc
from qa_test_tools.account_tools import create_account, delete_account
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_Keys_Recovery(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_Keys_Recovery, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_Keys_Recovery, cls).teardown_class()

    @pytest.mark.region_admin
    def test_T2862_recover_ak_sk_for_new_account(self):
        pid = None
        try:
            email = '{}@outscale.com'.format(id_generator(prefix='qa+T2862+'))
            password = misc.id_generator(size=20)
            pid = create_account(self.a1_r1, account_info={'email_address': email, 'password': password})
            self.a1_r1.icu.SendResetPasswordEmail(Email=email)
            rettoken = self.a1_r1.identauth.IdauthPasswordToken.createAccountPasswordToken(accountEmail=email, account_id=pid)
            config = DefaultPubConfig(account=DefaultAccount(login=email, password=password),
                                      region=DefaultRegion(name=self.a1_r1.config.region.name))
            icu = OscIcuApi(service='icu', config=config)
            try:
                icu.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                         Token=rettoken.response.passwordToken, Password='toto')
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'PasswordPolicyViolation', 'Password strength score (0) is too low: at least 4 '
                                                                    'out of 4 level is expected. Warning: Repeats like'
                                                                    ' "abcabcabc" are only slightly harder to guess '
                                                                    'than "abc".. Suggestions: [Add another word or two.'
                                                                    ' Uncommon words are better.|Avoid repeated words and characters.]')
            new_password = id_generator(size=20)
            icu.ResetAccountPassword(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty},
                                     Token=rettoken.response.passwordToken, Password=new_password)
            config = DefaultPubConfig(account=DefaultAccount(login=email, password=new_password),
                                      region=DefaultRegion(name=self.a1_r1.config.region.name))
            icu = OscIcuApi(service='icu', config=config)
            listkey = icu.ListAccessKeys(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword})
            config = DefaultPubConfig(account=DefaultAccount(ak=listkey.response.accessKeys[0].accessKeyId,
                                                             sk=listkey.response.accessKeys[0].secretAccessKey),
                                      region=DefaultRegion(name=self.a1_r1.config.region.name))
            fcu = OscPubApi(service='fcu', config=config)
            fcu.DescribeImages()
        finally:
            if pid:
                delete_account(self.a1_r1, pid)
