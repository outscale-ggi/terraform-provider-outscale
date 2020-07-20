# -*- coding:utf-8 -*-
from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_keypair
from qa_tina_tools.tina.info_keys import NAME, FINGERPRINT
import pytest
from qa_test_tools.misc import assert_dry_run, assert_oapi_error


class Test_ReadKeypairs(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadKeypairs, cls).setup_class()
        cls.kp_info1 = None
        cls.kp_info2 = None
        try:
            cls.kp_info1 = create_keypair(cls.a1_r1)
            cls.kp_info2 = create_keypair(cls.a1_r1)
            cls.fingerprint1 = cls.kp_info1[FINGERPRINT]
            cls.fingerprint2 = cls.kp_info2[FINGERPRINT]
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.kp_info1:
                delete_keypair(cls.a1_r1, cls.kp_info1)
            if cls.kp_info2:
                delete_keypair(cls.a1_r1, cls.kp_info2)
        finally:
            super(Test_ReadKeypairs, cls).teardown_class()

    def test_T2357_empty_param(self):
        self.a1_r1.oapi.ReadKeypairs()

    def test_T2358_filters_name1(self):
        ret = self.a1_r1.oapi.ReadKeypairs(Filters={'KeypairNames': [self.kp_info1[NAME]]}).response.Keypairs
        assert len(ret) == 1
        assert ret[0].KeypairName == self.kp_info1[NAME]
        assert ret[0].KeypairFingerprint == self.fingerprint1

    def test_T2359_filters_name2(self):
        ret = self.a1_r1.oapi.ReadKeypairs(Filters={'KeypairNames': [self.kp_info2[NAME]]}).response.Keypairs
        assert len(ret) == 1
        assert ret[0].KeypairName == self.kp_info2[NAME]
        assert ret[0].KeypairFingerprint == self.fingerprint2

    def test_T2360_filters_fingerprint1(self):
        ret = self.a1_r1.oapi.ReadKeypairs(Filters={'KeypairFingerprints': [self.fingerprint1]}).response.Keypairs
        assert len(ret) == 1
        assert ret[0].KeypairName == self.kp_info1[NAME]
        assert ret[0].KeypairFingerprint == self.fingerprint1

    def test_T3433_dry_run(self):
        self.a1_r1.oapi.ReadKeypairs(DryRun=True)
        assert_dry_run

    @pytest.mark.tag_sec_confidentiality
    def test_T3431_other_account(self):
        ret = self.a2_r1.oapi.ReadKeypairs().response.Keypairs
        assert not ret

    @pytest.mark.tag_sec_confidentiality
    def test_T3432_other_account_with_filter(self):
        ret = self.a2_r1.oapi.ReadKeypairs(Filters={'KeypairNames': [self.kp_info1[NAME]]}).response.Keypairs
        assert not ret

    def test_T5095_with_tags_filter(self):
        try:
            self.a1_r1.oapi.ReadKeypairs(Filters={"Tags": 'key_pair=key_pair_value'}).response.Keypairs
            assert False, 'Call should fail'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T5096_with_tagskey_filter(self):
        try:
            self.a1_r1.oapi.ReadKeypairs(Filters={"TagKeys": ['key_pair']}).response.Keypairs
            assert False, 'Call should fail'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    def test_T5097_with_tagsvalue_filter(self):
        try:
            self.a1_r1.oapi.ReadKeypairs(Filters={"TagValues": ['key_pair_value']}).response.Keypairs
            assert False, 'Call should fail'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')
