import os
import string

from qa_sdks.osc_sdk import OscSdk
from qa_test_tools import misc
from qa_test_tools.account_tools import delete_account, create_account
from qa_test_tools.config import OscConfig
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_certificate_setup


class ApiAccessRule(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(ApiAccessRule, cls).setup_class()
        cls.account_pid = None
        cls.tmp_file_paths = []
        cls.ca_ids = []
        try:
            if os.getenv('OSC_CU', None):
                cls.osc_sdk = cls.a1_r1
            else:
                email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='create_api_access_rule').lower())
                password = misc.id_generator(size=20, chars=string.digits + string.ascii_letters)
                account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                                'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                                'password': password, 'zipcode': '92210'}
                cls.account_pid = create_account(cls.a1_r1, account_info=account_info)
                keys = cls.a1_r1.intel.accesskey.find_by_user(owner=cls.account_pid).response.result[0]
                cls.osc_sdk = OscSdk(config=OscConfig.get_with_keys(az_name=cls.a1_r1.config.region.az_name, ak=keys.name, sk=keys.secret,
                                                                    account_id=cls.account_pid, login=email, password=password))

            paths = create_certificate_setup()
            cls.ca1files = paths[0]
            cls.ca2files = paths[1]
            cls.ca3files = paths[2]
            cls.certfiles_ca1cn1 = paths[3]
            cls.certfiles_ca2cn1 = paths[4]
            cls.certfiles_ca1cn2 = paths[5]
            cls.certfiles_ca3cn1 = paths[6]
            cls.tmp_file_paths = paths[7]
            for cafile in [cls.ca1files[1], cls.ca2files[1], cls.ca3files[1]]:
                with open(cafile) as cafile:
                    cls.ca_ids.append(cls.osc_sdk.oapi.CreateCa(CaPem=cafile.read(), Description='description').response.Ca.CaId)
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for tmp_file_path in cls.tmp_file_paths:
                try:
                    os.remove(tmp_file_path)
                except:
                    print('Could not remove file')
            if cls.account_pid:
                delete_account(cls.a1_r1, cls.account_pid)
        finally:
            super(ApiAccessRule, cls).teardown_class()
