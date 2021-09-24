from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_certificate_setup
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_ReadCas(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_ReadCas, cls).setup_class()
        cls.tmp_file_paths = None
        cls.ca1 = cls.ca2 = cls.ca3 = None
        cls.ca1files = cls.ca2files = None
        cls.ca1files, cls.ca2files, cls.ca3files, _, _, _, _, cls.tmp_file_paths = create_certificate_setup()
        with open(cls.ca1files[1]) as cafile:
            cls.ca1 = cls.a1_r1.oapi.CreateCa(CaPem=cafile.read(), Description='test ca1')

        with open(cls.ca3files[1]) as cafile:
            cls.ca3 = cls.a1_r1.oapi.CreateCa(CaPem=cafile.read(), Description='test ca3')

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ca1:
                cls.a1_r1.oapi.DeleteCa(CaId=cls.ca1.response.Ca.CaId)
            if cls.ca3:
                cls.a1_r1.oapi.DeleteCa(CaId=cls.ca3.response.Ca.CaId)
            if cls.ca2:
                cls.a2_r1.oapi.DeleteCa(CaId=cls.ca2.response.Ca.CaId)
        finally:
            super(Test_ReadCas, cls).teardown_class()

    def test_T5309_without_params(self):
        resp = self.a1_r1.oapi.ReadCas().response
        assert len(resp.Cas) == 2

    def test_T5310_dry_run(self):
        ret = self.a1_r1.oapi.ReadCas(DryRun=True)
        misc.assert_dry_run(ret)

    def test_T5311_with_CaFingerprints_filters(self):
        ret = self.a1_r1.oapi.ReadCas(Filters={'CaFingerprints': [self.ca1.response.Ca.CaFingerprint]})
        assert len(ret.response.Cas) == 1

    def test_T5312_with_non_existent_CaFingerprints_filters(self):
        ret = self.a1_r1.oapi.ReadCas(Filters={'CaFingerprints': ["test"]})
        assert len(ret.response.Cas) == 0

    def test_T5313_with_Descriptions_filters(self):
        ret = self.a1_r1.oapi.ReadCas(Filters={'Descriptions': ["test ca1"]})
        assert len(ret.response.Cas) == 1

    def test_T5314_with_non_existent_Descriptions_filters(self):
        ret = self.a1_r1.oapi.ReadCas(Filters={'Descriptions': ["test"]})
        assert len(ret.response.Cas) == 0

    def test_T5315_with_CaIds_filters(self):
        ret = self.a1_r1.oapi.ReadCas(Filters={'CaIds': [self.ca1.response.Ca.CaId, self.ca3.response.Ca.CaId]})
        assert len(ret.response.Cas) == 2

    def test_T5316_with_non_existent_CaIds_filters(self):
        ret = self.a2_r1.oapi.ReadCas()
        assert len(ret.response.Cas) == 0

    def test_T5724_login_password(self):
        resp = self.a1_r1.oapi.ReadCas(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword}).response
        assert len(resp.Cas) == 2

    def test_T6005_login_password_incorrect(self):
        try:
            self.a1_r1.oapi.ReadCas(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                                               osc_api.EXEC_DATA_LOGIN: 'foo', osc_api.EXEC_DATA_PASSWORD: 'bar'})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4120)
            known_error('API-400', 'Incorrect error message')
            misc.assert_oapi_error(error, 401, 'AccessDenied', 1)
