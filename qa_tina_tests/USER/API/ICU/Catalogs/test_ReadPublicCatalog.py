from qa_test_tools.test_base import OscTestSuite
from qa_sdk_pub.osc_api import AuthMethod


class Test_ReadPublicCatalog(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadPublicCatalog, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadPublicCatalog, cls).teardown_class()

    def test_T1330_with_authent(self):
        ret = self.a1_r1.icu.ReadPublicCatalog()
        # Attributes
        assert len(ret.response.Catalog.Attributes) >= 1, 'Catalog attribute size is incorrect'
        assert hasattr(ret.response.Catalog.Attributes[0], 'Key')
        assert hasattr(ret.response.Catalog.Attributes[0], 'Value')
        # entries
        assert len(ret.response.Catalog.Entries) >= 1, 'Catalog entries size is incorrect'
        assert hasattr(ret.response.Catalog.Entries[0], 'Attributes')
        assert hasattr(ret.response.Catalog.Entries[0], 'Key')
        assert hasattr(ret.response.Catalog.Entries[0], 'Title')
        assert hasattr(ret.response.Catalog.Entries[0], 'Value')

    def test_T1423_without_authent(self):
        ret = self.a1_r1.icu.ReadPublicCatalog(auth=AuthMethod.Empty)
        # Attributes
        assert len(ret.response.Catalog.Attributes) >= 1, 'Catalog attribute size is incorrect'
        assert hasattr(ret.response.Catalog.Attributes[0], 'Key')
        assert hasattr(ret.response.Catalog.Attributes[0], 'Value')
        # entries
        assert len(ret.response.Catalog.Entries) >= 1, 'Catalog entries size is incorrect'
        assert hasattr(ret.response.Catalog.Entries[0], 'Attributes')
        assert hasattr(ret.response.Catalog.Entries[0], 'Key')
        assert hasattr(ret.response.Catalog.Entries[0], 'Title')
        assert hasattr(ret.response.Catalog.Entries[0], 'Value')
