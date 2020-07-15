# from qa_tools.tools.test_base import OscTestSuite, known_error
# from qa_tools.tools.tina.create_tools import create_self_signed_cert
# import os
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina import create_tools
import os
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
# from qa_tools.specs.check_tools import check_oapi_response
# from osc_common.exceptions.osc_exceptions import OscApiException


#Parameter    In      Type       Required
#Body         body    string     true
#Chain        body    string     false
#DryRun       body    boolean    false
#Name         body    string     true
#Path         body    string     false
#PrivateKey   body    string     true

# Note: only tested with self signed certificates

class Test_CreateServerCertificate(OscTestSuite):
    
    @classmethod
    def setup_class(cls):
        super(Test_CreateServerCertificate, cls).setup_class()
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
            super(Test_CreateServerCertificate, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.sc_name = misc.id_generator(prefix='sc-')
        self.sc_resp = None

    def teardown_method(self, method):
        try:
            if self.sc_resp:
                self.a1_r1.oapi.DeleteServerCertificate(Name=self.sc_name)
        finally:
            OscTestSuite.teardown_method(self, method)
        
    def test_T4846_with_valid_param(self):
        self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key).response
        check_oapi_response(self.sc_resp, 'CreateServerCertificateResponse')
        assert self.sc_name == self.sc_resp.ServerCertificate.Name

    def test_T4847_missing_body(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, PrivateKey=self.key).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4848_invalid_body(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body="aaaaaaaaaa", PrivateKey=self.key).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4124)

    def test_T4849_incorrect_body_type(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=[self.cert], PrivateKey=self.key).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4850_missing_name(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Body=self.cert, PrivateKey=self.key).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4851_invalid_name(self):
        try:
            self.sc_name = '#&é"(§è!ç)'
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4118)

    def test_T4852_incorrect_name_type(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=[self.sc_name], Body=self.cert, PrivateKey=self.key).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4853_missing_private_key(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', 7000)

    def test_T4854_invalid_private_key(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey="aaaaaaaaaa").response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4124)

    def test_T4855_incorrect_private_key_type(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=[self.key]).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4856_dry_run(self):
        dr_ret = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key, DryRun=True)
        misc.assert_dry_run(dr_ret)

    def test_T4857_with_path(self):
        self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key, Path='/toto/').response
        check_oapi_response(self.sc_resp, 'CreateServerCertificateResponse')
        assert self.sc_name == self.sc_resp.ServerCertificate.Name

    def test_T4858_with_invalid_path(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key, Path='/toto').response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4118)

    def test_T4859_with_incorrect_path_type(self):
        try:
            self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key, Path=['/toto/']).response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)
    
    def test_T4860_twice_with_same_name(self):
        resp = None
        try:
            resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key).response
            try:
                self.resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key, Path='/test/').response
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                misc.assert_oapi_error(error, 409, 'ResourceConflict', 9073)
        finally:
            if resp:
                self.a1_r1.oapi.DeleteServerCertificate(Name=resp.ServerCertificate.Name)
