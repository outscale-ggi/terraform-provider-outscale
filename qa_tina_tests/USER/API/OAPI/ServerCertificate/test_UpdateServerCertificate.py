import os

from qa_test_tools import misc
import pytest
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.specs.check_tools import check_oapi_response
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.tools.tina import create_tools
from qa_tina_tools.tina import wait


#Parameter    In      Type      Required
#DryRun       body    boolean   false
#Name         body    string    false
#NewName      body    string    false
#NewPath      body    string    false


class Test_UpdateServerCertificate(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateServerCertificate, cls).setup_class()
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
            super(Test_UpdateServerCertificate, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        self.sc_name = misc.id_generator(prefix='sc-')
        self.sc_path = '/test/'
        self.sc_resp = self.a1_r1.oapi.CreateServerCertificate(Name=self.sc_name, Body=self.cert, PrivateKey=self.key, Path=self.sc_path).response
        wait.wait_ServerCertificates_state(self.a1_r1, [self.sc_name])

    def teardown_method(self, method):
        try:
            if self.sc_resp:
                try:
                    self.a1_r1.oapi.DeleteServerCertificate(Name=self.sc_name)
                except:
                    pass
        finally:
            OscTestSuite.teardown_method(self, method)

    def test_T4880_valid_params_new_name(self):
        new_name = misc.id_generator(prefix='sc-')
        resp = self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewName=new_name).response
        self.sc_name = new_name
        check_oapi_response(resp, 'UpdateServerCertificateResponse')
        assert resp.ServerCertificate.Name == new_name

    def test_T4881_valid_params_new_path(self):
        resp = self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewPath='/toto/').response
        check_oapi_response(resp, 'UpdateServerCertificateResponse')
        assert resp.ServerCertificate.Path == '/toto/'

    def test_T4882_valid_params_new_name_and_path(self):
        new_name = misc.id_generator(prefix='sc-')
        resp = self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewName=new_name, NewPath='/toto/').response
        self.sc_name = new_name
        check_oapi_response(resp, 'UpdateServerCertificateResponse')
        assert resp.ServerCertificate.Name == new_name
        assert resp.ServerCertificate.Path == '/toto/'

    def test_T4883_missing_name(self):
        new_name = misc.id_generator(prefix='sc-')
        try:
            self.a1_r1.oapi.UpdateServerCertificate(NewName=new_name, NewPath='/toto/').response
            self.sc_name = new_name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.status_code == 400 and error.message == 'InvalidParameterValue':
                known_error('GTW-1371', 'Incorrect error message in CheckAuthentication')
            assert False, ('Remove known error')
            misc.assert_error(error, 400, '3001', 'InvalidParameter')

    def test_T4884_invalid_name(self):
        invalid_name = '@&é"(§è!çà)'
        new_name = misc.id_generator(prefix='sc-')
        try:
            self.a1_r1.oapi.UpdateServerCertificate(Name=invalid_name, NewName=new_name, NewPath='/toto/').response
            self.sc_name = new_name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4122)

    def test_T4885_invalid_name_type(self):
        new_name = misc.id_generator(prefix='sc-')
        try:
            self.a1_r1.oapi.UpdateServerCertificate(Name=[self.sc_name], NewName=new_name, NewPath='/toto/').response
            self.sc_name = new_name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4886_incorrect_name(self):
        incorrect_name = 'incorrect_name'
        new_name = misc.id_generator(prefix='sc-')
        try:
            self.a1_r1.oapi.UpdateServerCertificate(Name=incorrect_name, NewName=new_name, NewPath='/toto/').response
            self.sc_name = new_name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4122)

    def test_T4887_missing_new_param(self):
        resp = self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name).response
        assert resp.ServerCertificate.Name == self.sc_name
        assert resp.ServerCertificate.Path == self.sc_path

    def test_T4888_invalid_new_name(self):
        new_name = '@&é"(§è!çà)'
        try:
            self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewName=new_name, NewPath='/toto/').response
            self.sc_name = new_name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4118)

    def test_T4889_invalid_new_name_type(self):
        new_name = misc.id_generator(prefix='sc-')
        try:
            self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewName=[new_name], NewPath='/toto/').response
            self.sc_name = new_name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4890_invalid_new_path(self):
        new_name = misc.id_generator(prefix='sc-')
        try:
            self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewName=new_name, NewPath='/toto').response
            self.sc_name = new_name
            assert False, 'Remove known error'
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4118)

    def test_T4891_invalid_new_path_type(self):
        new_name = misc.id_generator(prefix='sc-')
        try:
            self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewName=new_name, NewPath=['/toto/']).response
            self.sc_name = new_name
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4110)

    def test_T4892_dry_run(self):
        dr_ret = self.a1_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewPath='/toto/', DryRun=True)
        misc.assert_dry_run(dr_ret)

    def test_T4893_other_account(self):
        if not hasattr(self, 'a2_r1'):
            pytest.skip('This test requires two users')
        try:
            self.a2_r1.oapi.UpdateServerCertificate(Name=self.sc_name, NewPath='/toto/').response
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4122)
