import os
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.create_tools import create_certificate_setup


class Test_DeleteCa(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.tmp_file_paths = None
        cls.ca_id = None
        cls.ca_id_bis = None
        super(Test_DeleteCa, cls).setup_class()
        cls.ca1files, _, _, _, _, _, _, cls.tmp_file_paths = create_certificate_setup(root_name='ca')
        with open(cls.ca1files[1]) as cafile:
            cls.ca_id = cls.a1_r1.oapi.CreateCa(CaPem=cafile.read(), Description='test ca').response.Ca.CaId
        cls.ca1files, _, _, _, _, _, _, cls.tmp_file_paths_bis = create_certificate_setup(root_name='cabis')
        with open(cls.ca1files[1]) as cafile:
            cls.ca_id_bis = cls.a1_r1.oapi.CreateCa(CaPem=cafile.read(), Description='test ca bis').response.Ca.CaId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ca_id:
                cls.a1_r1.oapi.DeleteCa(CaId=cls.ca_id)
            if cls.ca_id_bis:
                cls.a1_r1.oapi.DeleteCa(CaId=cls.ca_id_bis)
            if cls.tmp_file_paths:
                for tmp_file_path in cls.tmp_file_paths:
                    os.remove(tmp_file_path)
            if cls.tmp_file_paths_bis:
                for tmp_file_path in cls.tmp_file_paths_bis:
                    os.remove(tmp_file_path)
        finally:
            super(Test_DeleteCa, cls).teardown_class()

    def test_T5305_without_params(self):
        try:
            self.a1_r1.oapi.DeleteCa()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T5306_invalid_CaId(self):
        try:
            self.a1_r1.oapi.DeleteCa(CaId='ca-test123456')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4118')

    @pytest.mark.tag_sec_confidentiality
    def test_T5307_with_other_account(self):
        try:
            self.a2_r1.oapi.DeleteCa(CaId=self.ca_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4122')
            known_error('GTW-1542', 'Incorrect error message on DeleteCa')

    def test_T5308_valid_params(self):
        ret = self.a1_r1.oapi.DeleteCa(CaId=self.ca_id)
        self.__class__.ca_id = None
        ret.check_response()

    def test_T5723_login_password(self):
        ret = self.a1_r1.oapi.DeleteCa(
            exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword},
            CaId=self.ca_id_bis)
        self.__class__.ca_id_bis = None
        ret.check_response()

    def test_T6004_login_password_incorrect(self):
        try:
            self.a1_r1.oapi.DeleteCa(
                exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.LoginPassword,
                           osc_api.EXEC_DATA_LOGIN: 'foo', osc_api.EXEC_DATA_PASSWORD: 'bar'},
                CaId=self.ca_id_bis)
            self.__class__.ca_id_bis = None
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4120)
            known_error('API-400', 'Incorrect error message')
            misc.assert_oapi_error(error, 401, 'AccessDenied', 1)
