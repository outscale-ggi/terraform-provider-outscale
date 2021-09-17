
import pytest

from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest

NUM_PUB_IPS = 4

class Test_ReadPublicIps(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.public_ips = []
        cls.public_ip_ids = []
        super(Test_ReadPublicIps, cls).setup_class()
        try:
            for _ in range(NUM_PUB_IPS):
                resp = cls.a1_r1.oapi.CreatePublicIp().response
                cls.public_ips.append(resp.PublicIp.PublicIp)
                cls.public_ip_ids.append(resp.PublicIp.PublicIpId)
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.public_ip_ids[0]], Tags=[{'Key': 'toto', 'Value': 'titi'}])

        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            for pub_ip in cls.public_ips:
                cls.a1_r1.oapi.DeletePublicIp(PublicIp=pub_ip)
        finally:
            super(Test_ReadPublicIps, cls).teardown_class()

    def test_T2014_basic(self):
        ret = self.a1_r1.oapi.ReadPublicIps().response.PublicIps
        assert len(ret) == 4
        assert hasattr(ret[0], 'PublicIp')
        assert hasattr(ret[0], 'PublicIpId')
        assert ret[0].PublicIpId.startswith('eipalloc')
        assert len(ret[0].Tags) == 1

    def test_T2266_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadPublicIps(DryRun=True)
        misc.assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3408_other_account(self):
        ret = self.a2_r1.oapi.ReadPublicIps().response.PublicIps
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3409_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadPublicIps(Filters={'PublicIps': [self.public_ips[0]]}).response.PublicIps
        assert not ret

    def test_T4427_with_tagkeys_filter(self):
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagKeys': ['foo']})
        assert len(ret.response.PublicIps) == 0
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagKeys': ['toto']})
        assert len(ret.response.PublicIps) == 1

    def test_T4428_with_tagvalues_filter(self):
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagValues': ['bar']})
        assert len(ret.response.PublicIps) == 0
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagValues': ['titi']})
        assert len(ret.response.PublicIps) == 1

    def test_T4429_with_tags_filter(self):
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'Tags': ['foo=bar']})
        assert len(ret.response.PublicIps) == 0
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'Tags': ['toto=titi']})
        assert len(ret.response.PublicIps) == 1

    def test_T5976_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'PublicIp', self.public_ip_ids, 'oapi.ReadPublicIps', 'PublicIps.PublicIpId')
        assert indexes == [3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 19, 20, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'Read calls do not support wildcards in tag filtering')
