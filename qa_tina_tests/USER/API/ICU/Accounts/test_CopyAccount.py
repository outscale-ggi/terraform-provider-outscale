from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_test_tools.config import OscConfig
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.misc import id_generator
import string
import pytest
from qa_tina_tools.constants import TWO_REGIONS_NEEDED
from qa_test_tools.account_tools import create_account, delete_account


class Test_CopyAccount(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CopyAccount, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CopyAccount, cls).teardown_class()

    def test_T548_no_param(self):
        try:
            self.a1_r1.icu.CopyAccount()
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'IcuClientException'

    def test_T550_invalid_region(self):
        try:
            self.a1_r1.icu.CopyAccount(DestinationRegion='foo')
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidRegion.NotFound'
            assert error.message == "Region 'foo' does not exist."

    def test_T551_required_param(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        try:
            email = 'qa+{}@outscale.com'.format(id_generator(prefix="test-copyAccount"))
            password = id_generator(size=20, chars=string.digits)
            account_info = {'city': 'Saint_Cloud', 'company_name': 'Outscale', 'country': 'France', 'email_address': email, 'firstname': 'Test_user',
                            'lastname': 'Test_Last_name', 'password': password, 'zipcode': '92210'}
            pid = create_account(self.a1_r1, account_info=account_info)
            ret = self.a1_r1.intel.accesskey.find_by_user(owner=pid)
            keys = ret.response.result[0]
            osc_sdk = OscSdk(config=OscConfig.get_with_keys(az_name=self.a1_r1.config.region.az_name,
                                                            ak=keys.name, sk=keys.secret, account_id=pid, login=email, password=password))
            ret = osc_sdk.icu.CopyAccount(DestinationRegion=self.a1_r2.config.region.name)
            assert False, "Remove known error"
            # TODO assert ret.... == ??? (check accoutn on r2... ?)
        except OscApiException as error:
            if error.status_code == 500 and error.message == "InternalError":
                known_error("TINA-5699", "CopyAccount fail with 'InternalError'")
            assert False, "Remove known error"
        finally:
            if pid:
                delete_account(self.a1_r1, pid)
            # TODO: terminate account on r2

    def test_T549_invalid_profile(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        try:
            self.a1_r1.icu.CopyAccount(DestinationRegion=self.a1_r2.config.region.name, profile='foo')
        except OscApiException as error:
            if error.status_code == 500 and error.message == "InternalError":
                assert known_error("TINA-5699", "CopyAccount fail with 'InternalError'")
            else:
                assert False, "Remove known error"
