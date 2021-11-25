
import string
import json

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdks.osc_sdk import OscSdk
from qa_tina_tools.test_base import OscTinaTest
from qa_test_tools import account_tools, misc
from qa_test_tools.config import OscConfig
from qa_test_tools.test_base import known_error


class Test_ReadAccessKeys(OscTinaTest):

    def test_T6064_check_eim_oapi_key_list(self):
        account_pid = None
        try:
            # create account
            email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='read_access_keys').lower())
            password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
            account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                            'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                            'password': password, 'zipcode': '92210'}
            account_pid = account_tools.create_account(self.a1_r1, account_info=account_info)
            keys = self.a1_r1.intel.accesskey.find_by_user(owner=account_pid).response.result[0]
            account_sdk = OscSdk(config=OscConfig.get_with_keys(az_name=self.a1_r1.config.region.az_name, ak=keys.name, sk=keys.secret,
                                                                account_id=account_pid, login=email, password=password))

            # create user for account
            username = misc.id_generator(prefix='user_')
            account_sdk.eim.CreateUser(UserName=username)
            policy = {"Statement": [{"Sid": "full_api", "Effect": "Allow", "Action": "*", "Resource": "*" }]}
            account_sdk.eim.PutUserPolicy(PolicyDocument=json.dumps(policy), PolicyName='full_api', UserName=username)
            user_key = account_sdk.eim.CreateAccessKey(UserName=username).response.CreateAccessKeyResult.AccessKey
            user_sdk = OscSdk(config=OscConfig.get_with_keys(az_name=self.a1_r1.config.region.az_name,
                                                             ak=user_key.AccessKeyId, sk=user_key.SecretAccessKey))

            ret = account_sdk.oapi.ReadAccessKeys()
            assert [key.AccessKeyId for key in ret.response.AccessKeys] == [keys.name]
            ret = account_sdk.icu.ListAccessKeys()
            assert [key.accessKeyId for key in ret.response.accessKeys] == [keys.name]
            ret = account_sdk.eim.ListAccessKeys()
            assert [key.AccessKeyId for key in ret.response.ListAccessKeysResult.AccessKeyMetadata] == [keys.name]

            try:
                ret = user_sdk.icu.ListAccessKeys()
                assert [key.accessKeyId for key in ret.response.accessKeys] == [user_key.AccessKeyId]
            except OscApiException as error:
                misc.assert_error(error, 400, 'NotImplemented', 'IAM authentication is not supported for ICU.')
            # print([key.accessKeyId for key in ret5.response.accessKeys])
            ret = user_sdk.eim.ListAccessKeys()
            assert [key.AccessKeyId for key in ret.response.ListAccessKeysResult.AccessKeyMetadata] == [user_key.AccessKeyId]

            ret = user_sdk.oapi.ReadAccessKeys()
            if [key.AccessKeyId for key in ret.response.AccessKeys] == [user_key.AccessKeyId]:
                assert False, 'Remove known error code'
            assert [key.AccessKeyId for key in ret.response.AccessKeys] == [keys.name]
            known_error('API-417', 'Incorrect return values.')


        except Exception as error:
            raise error
        finally:
            if account_pid:
                account_tools.delete_account(self.a1_r1, account_pid)
