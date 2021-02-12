# -*- coding:utf-8 -*-
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic


class Test_UnlinkPrivateIps(Nic):

    def setup_method(self, method):
        super(Test_UnlinkPrivateIps, self).setup_method(method)
        self.nic_id = None
        try:
            ret = self.a1_r1.oapi.CreateNic(SubnetId=self.subnet_id1).response.Nic
            self.nic_id = ret.NicId
            assert self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.35', '10.0.1.36', '10.0.1.37', '10.0.1.38'])
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.nic_id:
                self.a1_r1.oapi.DeleteNic(NicId=self.nic_id)
        finally:
            super(Test_UnlinkPrivateIps, self).teardown_method(method)

    def test_T2703_with_multiple_ips(self):
        self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.35', '10.0.1.36', '10.0.1.37', '10.0.1.38'])

    def test_T2692_with_empty_param(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2693_with_empty_nic_id(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(NicId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2694_with_invalid_nic_id(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(NicId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2695_with_unknown_nic_id(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(NicId='eni-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2696_with_missing_private_ips(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2697_with_missing_nic_id(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(PrivateIps=['10.0.1.35'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2698_with_invalid_ips_str(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['tata'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2699_with_unknown_ips_str(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['295.16.34.5'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2700_with_valid_combination(self):
        assert self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.35'])

    def test_T2701_with_2_ips(self):
        assert self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.36', '10.0.1.35'])

    def test_T2702_with_multiple_ip_one_valid_one_not_linked(self):
        try:
            self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.136', '10.0.1.35'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T3511_dry_run(self):
        ret = self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.36'], DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3512_other_account(self):
        try:
            self.a2_r1.oapi.UnlinkPrivateIps(NicId=self.nic_id, PrivateIps=['10.0.1.37'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5077')
