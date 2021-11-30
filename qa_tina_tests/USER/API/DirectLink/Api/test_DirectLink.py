from time import sleep
import datetime

import re
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException, OscCheckException
import qa_sdk_pub.osc_api as osc_api
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools import misc
from qa_test_tools.config import OscConfig
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from specs.check_tools import check_directlink_error, check_oapi_error, CheckErrorType

MIN_OVERTIME = 4

class Test_DirectLink(OscTinaTest):

    @pytest.mark.tag_sec_traceability
    def test_T3844_check_request_id(self):
        ret = self.a1_r1.directlink.DescribeLocations()
        ret.check_response()
        assert re.search("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", ret.response.requestId)

    def test_T3845_invalid_call(self):
        try:
            self.a1_r1.directlink.foo()
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            try:
                check_directlink_error(error, 12000, invalid_action='foo')
            except OscCheckException as check_error:
                if check_error.info == CheckErrorType.MissingMessage:
                    known_error('PQA-????', 'Check directlink error mapping')
                raise check_error

    def test_T3846_invalid_param(self):
        try:
            self.a1_r1.directlink.DescribeLocations(foo='bar')
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            check_directlink_error(error, 3001)

    def test_T3847_method_get(self):
        try:
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_METHOD: 'GET'})
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            check_directlink_error(error, 4000)

    @pytest.mark.tag_sec_confidentiality
    def test_T3849_without_authentication(self):
        try:
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_AUTHENTICATION: osc_api.AuthMethod.Empty})
            assert False, 'Call not should have been successful'
        except OscApiException as error:
            check_directlink_error(error, 9)

    @pytest.mark.tag_sec_confidentiality
    def test_T3850_invalid_authentication(self):
        sk_bkp = self.a1_r1.config.account.sk
        self.a1_r1.config.account.sk = "foo"
        try:
            self.a1_r1.directlink.DescribeLocations()
            assert False, 'Call not should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 4144)
        finally:
            self.a1_r1.config.account.sk = sk_bkp

    @pytest.mark.tag_sec_availability
    def test_T3851_throttling(self):
        osc_api.disable_throttling()
        nb_ok = 0
        nb_ko = 0
        for _ in range(10):
            try:
                self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                nb_ok += 1
            except OscApiException as error:
                if error.status_code == 503:
                    nb_ko += 1
                else:
                    raise
        osc_api.enable_throttling()
        assert nb_ok != 0
        assert nb_ko != 0

    def test_T4577_with_eim_user(self):
        user_name = misc.id_generator(prefix='T4577')
        policy_name = misc.id_generator(prefix='T4577')
        account_sdk = None
        attach_policy = None
        user_info = None
        policy_response = None
        accesskey_info = None
        try:
            user_info = self.a1_r1.eim.CreateUser(UserName=user_name)
            policy_response = self.a1_r1.eim.CreatePolicy(
                PolicyName=policy_name,
                PolicyDocument='{"Statement": [{"Action": ["directconnect:*"], "Resource": ["*"], "Effect": "Allow"}]}')
            attach_policy = self.a1_r1.eim.AttachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=user_name)
            accesskey_info = self.a1_r1.eim.CreateAccessKey(UserName=user_name)
            account_sdk = OscSdk(config=OscConfig.get_with_keys(
                az_name=self.a1_r1.config.region.az_name, ak=accesskey_info.response.CreateAccessKeyResult.AccessKey.AccessKeyId,
                sk=accesskey_info.response.CreateAccessKeyResult.AccessKey.SecretAccessKey))
            ret = account_sdk.directlink.DescribeLocations()
            assert ret.status_code == 200
            try:
                account_sdk.fcu.DescribeDhcpOptions()
            except OscApiException as error:
                misc.assert_error(error, 400, 'UnauthorizedOperation', None)
            try:
                account_sdk.eim.ListAccessKeys()
            except OscApiException as error:
                misc.assert_error(error, 400, 'AccessDenied', None)
            try:
                account_sdk.lbu.DescribeLoadBalancers()
            except OscApiException as error:
                misc.assert_error(error, 400, 'AccessDenied', None)
            try:
                account_sdk.icu.ReadCatalog()
            except OscApiException as error:
                misc.assert_error(error, 400, 'NotImplemented', None)
            try:
                account_sdk.oapi.ReadVms()
            except OscApiException as error:
                check_oapi_error(error, 4)
        finally:
            if attach_policy:
                self.a1_r1.eim.DetachUserPolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn, UserName=user_name)
            if policy_response:
                self.a1_r1.eim.DeletePolicy(PolicyArn=policy_response.response.CreatePolicyResult.Policy.Arn)
            if accesskey_info:
                self.a1_r1.eim.DeleteAccessKey(AccessKeyId=accesskey_info.response.CreateAccessKeyResult.AccessKey.AccessKeyId, UserName=user_name)
            if user_info:
                self.a1_r1.eim.DeleteUser(UserName=user_name)

    def test_T6037_before_date_time_stamp(self):
        try:
            date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 15, timestamp=date_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6038_before_date_stamp(self):
        date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6039_before_stamps(self):
        try:
            date_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = date_time.strftime('%Y%m%d')
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                          osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 15, timestamp=date_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

        date_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=800)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6040_incorrect_date_time_stamp(self):
        try:
            date_time_stamp = 'toto'
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            try:
                check_directlink_error(error, 4166, header_date='Date')
            except OscCheckException as check_error:
                if check_error.info == CheckErrorType.MessageMismatch:
                    known_error('PQA-????', 'Check directlink error mapping')
                raise check_error

    def test_T6041_incorrect_date_stamp(self):
        date_stamp = 'toto'
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6042_empty_date_time_stamp(self):
        try:
            date_time_stamp = ''
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            try:
                check_directlink_error(error, 7009, header_name='Date')
            except OscCheckException as check_error:
                if check_error.info == CheckErrorType.MessageMismatch:
                    known_error('PQA-????', 'Check directlink error mapping')
                raise check_error


    def test_T6043_empty_date_stamp(self):
        try:
            date_stamp = ''
            self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_DATE_STAMP: date_stamp})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 9)

    def test_T6044_after_date_time_stamp(self):
        try:
            date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=MIN_OVERTIME)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            ret = self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                                osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            known_error("TINA-6773", "No error raised when sending request with date header in the future")
            assert False, 'Call should not have been successful : {}'.format(ret.response.requestId)
        except OscApiException as error:
            assert False, "remove known error code"
            check_directlink_error(error, 15, timestamp=date_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})

    def test_T6045_after_date_stamp(self):
        sleep(2)
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=MIN_OVERTIME)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp})
        sleep(2)
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp})

    def test_T6046_after_stamps(self):
        sleep(2)
        try:
            date_time = datetime.datetime.utcnow() + datetime.timedelta(days=MIN_OVERTIME)
            date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
            date_stamp = date_time.strftime('%Y%m%d')
            ret = self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                                osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                                osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
            known_error("TINA-6773", "No error raised when sending request with date header in the future")
            assert False, 'Call should not have been successful : {}'.format(ret.response.requestId)
        except OscApiException as error:
            assert False, "remove known error code"
            check_directlink_error(error, 15, timestamp=date_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'))

        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
        date_time_stamp = date_time.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = date_time.strftime('%Y%m%d')
        self.a1_r1.directlink.DescribeLocations(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0,
                                                      osc_api.EXEC_DATA_DATE_STAMP: date_stamp,
                                                      osc_api.EXEC_DATA_DATE_TIME_STAMP: date_time_stamp})
