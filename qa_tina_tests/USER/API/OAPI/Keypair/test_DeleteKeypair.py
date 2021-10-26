
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import  assert_dry_run
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina.info_keys import NAME
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_keypair
from specs import check_oapi_error


class Test_DeleteKeypair(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteKeypair, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteKeypair, cls).teardown_class()

    def test_T2350_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteKeypair()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T2351_valid_name(self):
        kp_info = None
        try:
            kp_info = create_keypair(self.a1_r1)
            self.a1_r1.oapi.DeleteKeypair(KeypairName=kp_info[NAME])
            kp_info = None
        finally:
            if kp_info:
                delete_keypair(self.a1_r1, kp_info)

    @pytest.mark.tag_sec_confidentiality
    def test_T3462_valid_name_other_account(self):
        kp_info = None
        try:
            kp_info = create_keypair(self.a1_r1)
            self.a2_r1.oapi.DeleteKeypair(KeypairName=kp_info[NAME])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 5071)
        finally:
            if kp_info:
                delete_keypair(self.a1_r1, kp_info)

    def test_T3463_valid_params_dry_run(self):
        try:
            kp_info = create_keypair(self.a1_r1)
            ret = self.a1_r1.oapi.DeleteKeypair(KeypairName=kp_info[NAME], DryRun=True)
            assert_dry_run(ret)
        finally:
            if kp_info:
                try:
                    delete_keypair(self.a1_r1, kp_info)
                except:
                    print('Could not delete keypair')

    def test_T3465_invalid_dry_run(self):
        try:
            kp_info = create_keypair(self.a1_r1)
            ret = self.a1_r1.oapi.DeleteKeypair(DryRun=True)
            assert_dry_run(ret)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        finally:
            if kp_info:
                try:
                    delete_keypair(self.a1_r1, kp_info)
                except:
                    print('Could not delete keypair')
