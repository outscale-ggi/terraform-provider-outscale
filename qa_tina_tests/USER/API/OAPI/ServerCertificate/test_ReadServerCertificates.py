import os

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import create_tools


#Parameter     In      Type       Required
#DryRun        body    boolean    false
#FirstResult   body    integer    false
#MaxResults    body    integer    false
#Path          body    string     false
class Test_ReadServerCertificates(OscTestSuite):

    @classmethod
    def setup_class(cls):
        def create_sc(osc_sdk, cert, key, path):
            name = misc.id_generator('sc_')
            osc_sdk.oapi.CreateServerCertificate(Name=name, Body=cert, PrivateKey=key, Path=path)
            return name
            
        super(Test_ReadServerCertificates, cls).setup_class()
        cls.crtpath, cls.keypath = create_tools.create_self_signed_cert()
        cls.key = open(cls.keypath).read()
        cls.cert = open(cls.crtpath).read()
        cls.a1_cert_names = []
        cls.a2_cert_names = []
        cls.a1_cert_names.append(create_sc(cls.a1_r1, cls.cert, cls.key, '/path1/'))
        cls.a1_cert_names.append(create_sc(cls.a1_r1, cls.cert, cls.key, '/path1/'))
        cls.a1_cert_names.append(create_sc(cls.a1_r1, cls.cert, cls.key, '/path2/'))
        cls.a2_cert_names.append(create_sc(cls.a2_r1, cls.cert, cls.key, '/path1/'))

    @classmethod
    def teardown_class(cls):
        try:
            for name in cls.a1_cert_names:
                cls.a1_r1.oapi.DeleteServerCertificate(Name=name)
            for name in cls.a2_cert_names:
                cls.a2_r1.oapi.DeleteServerCertificate(Name=name)
            if cls.crtpath:
                os.remove(cls.crtpath)
            if cls.keypath:
                os.remove(cls.keypath)
        finally:    
            super(Test_ReadServerCertificates, cls).teardown_class()

    def test_T4868_valid_params(self):
        ret = self.a1_r1.oapi.ReadServerCertificates()
        ret.check_response()
        assert len(ret.response.ServerCertificates) == 3

    def test_Txxx_filters_paths(self):
        ret = self.a1_r1.oapi.ReadServerCertificates(Filters={'Paths': ['/path1/']})
        ret.check_response()
        assert len(ret.response.ServerCertificates) == 2

    def test_T4869_with_first_result(self):
        try:
            self.a1_r1.oapi.ReadServerCertificates(FirstResult=1).response
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameter', 3001)

    @pytest.mark.tag_sec_confidentiality
    def test_T4879_other_account(self):
        if not hasattr(self, 'a2_r1'):
            pytest.skip('This test requires two users')
        resp = self.a2_r1.oapi.ReadServerCertificates().response
        assert len(resp.ServerCertificates) == 1
