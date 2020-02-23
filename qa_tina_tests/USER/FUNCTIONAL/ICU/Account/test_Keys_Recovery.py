from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import id_generator, assert_error
from qa_common_tools import misc
from osc_sdk_pub.default_config import DefaultPubConfig
from osc_sdk_pub.osc_api.osc_icu_api import OscIcuApi
from osc_sdk_pub.osc_api import AuthMethod
from osc_sdk_pub.osc_api.osc_pub_api import OscPubApi
from osc_common.exceptions.osc_exceptions import OscApiException
import pytest
from qa_common_tools.account_tools import create_account, delete_account


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
            config = DefaultPubConfig(None, None, login=email, password=password, region_name=self.a1_r1.config.region.name)
            icu = OscIcuApi(service='icu', config=config)
            try:
                icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=rettoken.response.passwordToken, Password='toto')
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                assert_error(error, 400, 'PasswordPolicyViolation', 'Password strength score (0) is too low: at least 4 '
                                                                    'out of 4 level is expected. Warning: Repeats like'
                                                                    ' "abcabcabc" are only slightly harder to guess '
                                                                    'than "abc".. Suggestions: [Add another word or two.'
                                                                    ' Uncommon words are better.|Avoid repeated words and characters.]')
            new_password = id_generator(size=20)
            icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=rettoken.response.passwordToken, Password=new_password)
            config = DefaultPubConfig(None, None, login=email, password=new_password, region_name=self.a1_r1.config.region.name)
            icu = OscIcuApi(service='icu', config=config)
            listkey = icu.ListAccessKeys(auth=AuthMethod.LoginPassword)
            config = DefaultPubConfig(ak=listkey.response.accessKeys[0].accessKeyId, sk=listkey.response.accessKeys[0].secretAccessKey,
                                      region_name=self.a1_r1.config.region.name)
            fcu = OscPubApi(service='fcu', config=config)
            fcu.DescribeImages()
        finally:
            if pid:
                delete_account(self.a1_r1, pid)
