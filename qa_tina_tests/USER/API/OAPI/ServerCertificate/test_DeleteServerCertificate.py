import os
from qa_test_tools import misc
import pytest
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import create_tools
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


#Parameter    In      Type       Required
#DryRun       body    boolean    false
#Name         body    string     false

class Test_DeleteServerCertificate(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteServerCertificate, cls).setup_class()
        cls.crtpath, cls.keypath = create_tools.create_self_signed_cert()
        cls.key = open(cls.keypath).read()
        cls.cert = open(cls.crtpath).read()

    @classmethod
    def teardown_class(cls):
        try:
            if cls.crtpath:
                os.remove(cls.crtpath)
            if cls.keypath:
                os.remove(cls.keypath)
        finally:    
            super(Test_DeleteServerCertificate, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.sc_name = misc.id_generator(prefix='sc-')
        self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key).response

    def teardown_method(self, method):
        try:
            if self.sc_resp:
                self.a1_r1.oapi.DeleteServerCertificate(Name=self.sc_name)
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T4861_valid_params(self):
        ret = self.a1_r1.oapi.DeleteServerCertificate(Name=self.sc_name)
        ret.check_response()
        self.sc_resp = None

    def test_T4862_missing_name(self):
        try:
            self.a1_r1.oapi.DeleteServerCertificate()
            self.sc_resp = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)
            

    def test_T4863_unexisting_name(self):
        try:
            self.a1_r1.oapi.DeleteServerCertificate(Name='toto')
            self.sc_resp = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4122)

    def test_T4864_invalid_name(self):
        try:
            self.a1_r1.oapi.DeleteServerCertificate(Name='#&é"(§è!ç)')
            self.sc_resp = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4122)

    def test_T4865_incorrect_name_type(self):
        try:
            self.a1_r1.oapi.DeleteServerCertificate(Name=[self.sc_name])
            self.sc_resp = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4866_dry_run(self):
        dr_ret = self.a1_r1.oapi.DeleteServerCertificate(Name=self.sc_name, DryRun=True)
        misc.assert_dry_run(dr_ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T4867_with_other_account(self):
        if not hasattr(self, 'a2_r1'):
            pytest.skip('This test requires two users')
        try:
            self.a2_r1.oapi.DeleteServerCertificate(Name=self.sc_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4122)
