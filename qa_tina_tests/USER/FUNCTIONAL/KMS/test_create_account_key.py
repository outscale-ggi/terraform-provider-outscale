from qa_common_tools.test_base import OscTestSuite, known_error
from osc_common.exceptions.osc_exceptions import OscApiException
import pytest
from osc_sdk_pub.osc_api import disable_throttling
from qa_common_tools.error import load_errors, error_type
from qa_common_tools.osc_sdk import OscSdk
from qa_common_tools.config import OscConfig
from qa_common_tools.account_tools import create_account, delete_account


@pytest.mark.region_kms
class Test_create_account_key(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_account_key, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_account_key, cls).teardown_class()

    def test_T4528_create_account_with_key(self):

        disable_throttling()
        errs = load_errors()
        for _ in range(40):
            pid = None
            osc_sdk = None
            try:
                pid = create_account(self.a1_r1)
                ret = self.a1_r1.intel.accesskey.find_by_user(owner=pid)
                keys = ret.response.result[0]
                osc_sdk = OscSdk(config=OscConfig.get_with_keys(az_name=self.a1_r1.config.region.az_name,
                                                                ak=keys.name, sk=keys.secret, account_id=pid))
            except OscApiException as error:
                errs.handle_api_exception(error, error_type.Create)
            except Exception as error:
                errs.add_unexpected_error(error)
            if osc_sdk:
                try:
                    osc_sdk.kms.CreateKey(Description='description', KeyUsage='ENCRYPT_DECRYPT', Origin='EXTERNAL')
                except OscApiException as error:
                    errs.handle_api_exception(error, error_type.Key)
                except Exception as error:
                    errs.add_unexpected_error(error)
            if pid:
                try:
                    delete_account(self.a1_r1, pid)
                except OscApiException as error:
                    errs.handle_api_exception(error, error_type.Delete)
                except Exception as error:
                    errs.add_unexpected_error(error)

        err_dict = errs.get_dict()
        print(err_dict)
        assert err_dict['key_failure'] == 0
        assert err_dict['internal_error_num'] == 0
        assert err_dict['error_num'] == 0
        assert err_dict['create_failure'] == 0
        assert err_dict['delete_failure'] == 0
