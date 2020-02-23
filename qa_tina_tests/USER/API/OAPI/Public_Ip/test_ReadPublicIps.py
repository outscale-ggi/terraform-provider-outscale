# -*- coding:utf-8 -*-
import pytest

from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.misc import assert_dry_run


class Test_ReadPublicIps(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadPublicIps, cls).setup_class()
        cls.ret = None
        try:
            cls.ret = cls.a1_r1.oapi.CreatePublicIp()
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.ret.response.PublicIp.PublicIpId], Tags=[{'Key': 'key', 'Value': 'value'}])

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret.response.PublicIp.PublicIp:
                cls.a1_r1.oapi.DeletePublicIp(PublicIp=cls.ret.response.PublicIp.PublicIp)
        finally:
            super(Test_ReadPublicIps, cls).teardown_class()

    def test_T2014_basic(self):
        ret = self.a1_r1.oapi.ReadPublicIps().response.PublicIps
        assert len(ret) == 1
        assert hasattr(ret[0], 'PublicIp')
        assert hasattr(ret[0], 'PublicIpId')
        assert ret[0].PublicIpId.startswith('eipalloc')
        assert len(ret[0].Tags) == 1

    def test_T2266_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadPublicIps(DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3408_other_account(self):
        ret = self.a2_r1.oapi.ReadPublicIps().response.PublicIps
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3409_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadPublicIps(Filters={'PublicIps': [self.ret.response.PublicIp.PublicIp]}).response.PublicIps
        assert not ret

    def test_T4427_with_tagkeys_filter(self):
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagKeys': ['foo']})
        assert len(ret.response.PublicIps) == 0
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagKeys': ['key']})
        assert len(ret.response.PublicIps) == 1

    def test_T4428_with_tagvalues_filter(self):
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagValues': ['bar']})
        assert len(ret.response.PublicIps) == 0
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'TagValues': ['value']})
        assert len(ret.response.PublicIps) == 1

    def test_T4429_with_tags_filter(self):
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'Tags': ['foo=bar']})
        assert len(ret.response.PublicIps) == 0
        ret = self.a1_r1.oapi.ReadPublicIps(Filters={'Tags': ['key=value']})
        assert len(ret.response.PublicIps) == 1
