import string

from qa_sdk_as import OscSdkAs
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.config import config_constants as constants
from qa_test_tools.error import load_errors, error_type
from qa_test_tools.test_base import OscTestSuite


class Test_create_account(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_account, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_account, cls).teardown_class()

    def test_T4526_create_many_accounts(self):
        #disable_throttling()
        errs = load_errors()
        osc_sdk_as = OscSdkAs(service='identauth', config=self.a1_r1.config)
        for _ in range(20):
            pid = None
            try:
                email = 'qa+{}@outscale.com'.format(misc.id_generator(prefix='test_xsub_create_account_').lower())
                password = misc.id_generator(size=20, chars=string.digits+string.ascii_letters)
                account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France',
                                'email_address': email, 'firstname': 'Test_user', 'lastname': 'Test_Last_name',
                                'password': password, 'zipcode': '92210'}
                ret = self.a1_r1.xsub.create_account(account_data=account_info, force=False,
                                                     creator=self.a1_r1.config.region.get_info(constants.AS_IDAUTH_ID))

                pid = ret.response.result.pid
            except OscApiException as error:
                errs.handle_api_exception(error, error_type.Create)
            except Exception as error:
                errs.add_unexpected_error(error)
            if pid:
                try:
                    self.a1_r1.xsub.terminate_account(pid=pid)
                    self.a1_r1.intel.user.delete(username=pid)
                    self.a1_r1.intel.user.gc(username=pid)
                    osc_sdk_as.IdauthAccountAdmin.deleteAccount(account_id=self.a1_r1.config.
                        region.get_info(constants.AS_IDAUTH_ID), principal={"accountPid": pid}, forceRemoval="true")
                except OscApiException as error:
                    errs.handle_api_exception(error, error_type.Delete)
                except Exception as error:
                    errs.add_unexpected_error(error)

        err_dict = errs.get_dict()
        print(err_dict)
        assert err_dict['error_num'] == 0
        assert err_dict['internal_error_num'] == 0
