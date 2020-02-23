import os

from osc_common.exceptions import OscApiException
from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_self_signed_cert


class Test_UploadServerCertificate(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UploadServerCertificate, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_UploadServerCertificate, cls).teardown_class()

    def test_T4538_with_future_certificate(self):
        crtpath = None
        keypath = None
        name = None
        try:
            crtpath, keypath = create_self_signed_cert(not_before=3600)
            key = open(keypath).read()
            cert = open(crtpath).read()
            ret_up = self.a1_r1.eim.UploadServerCertificate(ServerCertificateName=id_generator(prefix='cc-'), CertificateBody=cert, PrivateKey=key)
            name = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.ServerCertificateName
            assert False, 'remove known error'
        except OscApiException as err:
            if err.status_code == 500 and err.error_code == 'InternalError':
                known_error('TINA-5290', 'future certificate is not accepted')
            assert False, 'remove known error'
        finally:
            if name:
                try:
                    self.a1_r1.eim.DeleteServerCertificate(ServerCertificateName=name)
                except:
                    pass
            if crtpath:
                os.remove(crtpath)
            if keypath:
                os.remove(keypath)