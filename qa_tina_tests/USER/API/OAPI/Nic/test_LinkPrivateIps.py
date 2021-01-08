# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic


class Test_LinkPrivateIps(Nic):

    @classmethod
    def setup_class(cls):
        super(Test_LinkPrivateIps, cls).setup_class()
        cls.nic_id = None
        cls.nic_id2 = None
        try:
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_id = ret.NicId
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_id2 = ret.NicId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.nic_id2:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id2)
            if cls.nic_id:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id)
        finally:
            super(Test_LinkPrivateIps, cls).teardown_class()

    def test_T2662_with_empty_param(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2663_with_empty_nic_id(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2664_with_invalid_nic_id(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2665_with_unknown_nic_id(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId='eni-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2666_with_valid_nic_id_but_missing_other_param(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2667_with_invalid_private_ip(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2668_with_invalid_private_ip2(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['295.0.1.35'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2669_with_valid_combination(self):
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.35'])

    def test_T2670_with_invalid_secondary_ip_count(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, SecondaryPrivateIpCount=-2)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2671_with_too_much_ip(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, SecondaryPrivateIpCount=50000)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'TooManyResources (QuotaExceded)', '10021')

    def test_T2672_with_valid_combination2(self):
        calls = 0
        while calls < 10:
            calls += 1
            try:
                ret = self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, SecondaryPrivateIpCount=2)
                ret.check_response()
                calls = 10
            except OscApiException as error:
                assert_oapi_error(error, 400, 'TooManyResources (QuotaExceded)', '10021')
                assert False, 'Call should not have been failed'

    def test_T2673_with_invalid_combination(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.35'], SecondaryPrivateIpCount=2)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2674_with_valid_combination_allow_relink(self):
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id2, PrivateIps=['10.0.1.136'], AllowRelink=True)
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.136'], AllowRelink=True)

    def test_T2675_with_valid_combination2_allow_relink(self):
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, SecondaryPrivateIpCount=2, AllowRelink=True)

    def test_T2676_with_valid_combination_not_allow_relink(self):
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.145'], AllowRelink=True)
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id2, PrivateIps=['10.0.1.145'], AllowRelink=False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T3488_dry_run(self):
        ret = self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.36'], DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3489_other_account(self):
        try:
            self.a2_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.37'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5036')
