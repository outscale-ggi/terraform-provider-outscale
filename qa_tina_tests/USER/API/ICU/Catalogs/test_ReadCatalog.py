import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_test_tools.misc import assert_error
from qa_sdk_pub import osc_api


class Test_ReadCatalog(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadCatalog, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadCatalog, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T1331_with_authent(self):
        try:
            ret = self.a1_r1.icu.ReadCatalog()
            if self.a1_r1.config.region.name in ['top-west-1', 'ap-northeast-1']:
                assert False, 'Remove known error code'
        except OscApiException as error:
            if self.a1_r1.config.region.name in ['top-west-1']:
                known_error('NO-TICKET', 'Import catalog on TOP1')
            elif self.a1_r1.config.region.name in ['ap-northeast-1']:
                known_error('OPS-11545', 'No catalog on ap-northeast-1')
            raise error
        # Attributes
        if ret.response.Catalog.Attributes:
            assert len(ret.response.Catalog.Attributes) >= 1, 'Catalog attribute size is incorrect'
            assert hasattr(ret.response.Catalog.Attributes[0], 'Key')
            assert hasattr(ret.response.Catalog.Attributes[0], 'Value')
        # entries
        if ret.response.Catalog.Entries:
            assert len(ret.response.Catalog.Entries) >= 1, 'Catalog entries size is incorrect'
            assert hasattr(ret.response.Catalog.Entries[0], 'Attributes')
            assert hasattr(ret.response.Catalog.Entries[0], 'Key')
            assert hasattr(ret.response.Catalog.Entries[0], 'Title')
            assert hasattr(ret.response.Catalog.Entries[0], 'Value')

    def test_T1422_without_authent(self):
        try:
            self.a1_r1.icu.ReadCatalog(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
            assert False, 'Should not have succeeded'
        except OscApiException as error:
            assert_error(error, 401, 'AuthFailure', 'Outscale was not able to validate the provided access credentials. Invalid login/password or password has expired.')
