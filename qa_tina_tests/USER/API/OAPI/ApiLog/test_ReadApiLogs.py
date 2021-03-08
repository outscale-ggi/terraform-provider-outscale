from datetime import datetime, timedelta

import time
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite, known_error


@pytest.mark.region_cloudtrace
class Test_ReadApiLogs(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadApiLogs, cls).setup_class()
        cls.a1_r1.oapi.ReadTags()
        cls.a1_r1.oapi.ReadSubnets()
        cls.a1_r1.oapi.ReadNics()
        cls.a1_r1.oapi.ReadKeypairs()
        cls.a1_r1.oapi.ReadVms()
        cls.a1_r1.oapi.ReadVms()
        cls.a1_r1.fcu.DescribeImages()
        cls.a1_r1.icu.ListAccessKeys()
        time.sleep(60)

    @classmethod
    def teardown_class(cls):
        super(Test_ReadApiLogs, cls).teardown_class()

    def test_T2810_valid_params(self):
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=3)
        ret.check_response()
        account_ids = {log.AccountId for log in ret.response.Logs}
        assert len(account_ids) == 1 and self.a1_r1.config.account.account_id in account_ids, 'incorrect account id(s)'

    def test_T2823_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadApiLogs(DryRun=True)
        assert_dry_run(ret)

    def test_T3200_invalid_ResultsPerPage_value(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=1001)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            if err.status_code == 500 and err.message == 'InternalError':
                known_error('CLV-271', 'Internal error when calling ReadApiLogs with incorrect parameter value')
            assert False, 'Remove known error code'
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4113', None)
        try:
            self.a1_r1.oapi.ReadApiLogs(ResultsPerPage='1001')
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4110', None)
        try:
            self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=0)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4114', None)

    def test_T3203_invalid_NextPageToken_value(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(NextPageToken=123456)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4110', None)
        try:
            self.a1_r1.oapi.ReadApiLogs(NextPageToken='')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            if err.status_code == 500 and err.message == 'InternalError':
                known_error('CLV-271', 'Internal error when calling ReadApiLogs with incorrect parameter value')
            assert False, 'Remove known error code'
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4114', None)

    def test_T3204_verify_calls_on_log(self):
        call = ['ReadDhcpOptions', 'ReadImages', 'ReadNics', 'ReadApiLogs', 'ReadTags',
                'ReadSubnets', 'ReadKeypairs', 'ReadVms', 'DescribeImages', 'ListAccessKeys']
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=3,
                                          Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=200)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        assert len(ret.response.Logs) == 3
        assert ret.response.Logs[0].QueryCallName in call
        assert ret.response.Logs[1].QueryCallName in call
        assert ret.response.Logs[2].QueryCallName in call

    def test_T3205_verify_fcu_call(self):
        self.a1_r1.fcu.DescribeInstances()
        time.sleep(15)
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=100,
                                          Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=100)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        assert 'DescribeInstances' in [call.QueryCallName for call in ret.response.Logs]

    def test_T3206_valid_filter_QueryCallNames(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryCallNames": ["ReadVms"]}, ResultsPerPage=2)
        assert len(ret.response.Logs) == 2

    def test_T3207_valid_filter_QueryAccessKeys(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryAccessKeys": [self.a1_r1.config.account.ak]})
        assert len(ret.response.Logs) != 0

    def test_T3208_valid_filter_QueryApiNames(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryApiNames": ["oapi"]})
        assert len(ret.response.Logs) != 0

    def test_T3209_invalid_QueryApiNames_value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryApiNames": ["fcu", "lbu", "directlink", "eim", "icu"]})
        assert ret.response.Logs

    def test_T3210_valid_filter_QueryIpAddresses(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryIpAddresses": ["169.254.232.245"]})
        assert len(ret.response.Logs) != 0

    def test_T3211_valid_filter_QueryUserAgents(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryUserAgents": ["UNKNOWN"]})
        assert len(ret.response.Logs) == 0

    def test_T3213_valid_filter_ResponseStatusCodes(self):
        try:
            self.a1_r1.oapi.ReadVm()
        except Exception as error:
            raise error
        time.sleep(15)
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"ResponseStatusCodes": [404]})
        assert len(ret.response.Logs) == 0

    def test_T3214_valid_filter_QueryDateBefore(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateBefore': (datetime.utcnow()).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        assert len(ret.response.Logs) != 0
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateBefore': (datetime.utcnow()).strftime('%Y-%m-%d')})
        assert len(ret.response.Logs) != 0

    def test_T3215_valid_filter_QueryDateAfter(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=50)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        assert len(ret.response.Logs) != 0
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=50)).strftime('%Y-%m-%d')})
        assert len(ret.response.Logs) != 0

    def test_T3216_valid_filter_combination(self):
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=5,
                                          Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        assert len(ret.response.Logs) == 5
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=5, Filters={"QueryApiNames": ["oapi"], "QueryAccessKeys": [self.a1_r1.config.account.ak]})
        assert len(ret.response.Logs) == 5
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=5, Filters={"QueryApiNames": ["oapi"], "ResponseStatusCodes": [200]})
        assert len(ret.response.Logs) == 5

    def test_T3217_invalid_filter_QueryDateAfter(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateAfter': '2017'})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', "4110")

    def test_T4179_invalid_filter_incorrect_date_order(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=5,
                                        Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                                 'QueryDateBefore': (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            if err.status_code == 500 and err.message == 'InternalError':
                known_error('CLV-271', 'Internal error when calling ReadApiLogs with incorrect parameter value')
            assert False, 'Remove known error code'
            assert_oapi_error(err, 400, 'InvalidParameterValue', "4098")

    def test_T3218_invalid_filter_ResponseStatusCodes(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={"ResponseStatusCodes": ['700']})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', "4110")

    def test_T3219_invalid_filter_QueryIpAddresses(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={"QueryIpAddresses": ['0.1']})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            if err.status_code == 500 and err.message == 'InternalError':
                known_error('CLV-271', 'Internal error when calling ReadApiLogs with incorrect parameter value')
            assert False, 'Remove known error code'
            assert_oapi_error(err, 400, 'InvalidParameterValue', "4112")

    def test_T3220_invalid_filter_QueryApiNames(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={"QueryApiNames": [1]})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', "4110")

    def test_T3221_invalid_params(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(titi='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', "3001")

    def test_T3222_valid_With_Value(self):
        param = ['QueryAccessKey', 'QueryIpAddress', 'QueryUserAgent', 'QueryCallName', 'QueryApiName', 'QueryApiVersion',
                 'QueryDate', 'QueryHeaderRaw', 'QueryHeaderSize', 'QueryPayloadRaw', 'ResponseStatusCode', 'ResponseSize', 'CallDuration',
                 'AccountId']
        for attr in param:
            ret = self.a1_r1.oapi.ReadApiLogs(With={attr: True}, ResultsPerPage=5)
            assert hasattr(ret.response.Logs[0], attr)

    def test_T3223_invalid_With_Value(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(With={'toto': True}, ResultsPerPage=1)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', "3001")

    def test_T3229_verify_response_of_With_Value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(With={'QueryAccessKey': True, 'QueryIpAddress': True, 'QueryUserAgent': True, 'QueryCallName': True,
                                                'QueryApiName': True, 'QueryApiVersion': True, 'QueryDate': True, 'QueryHeaderRaw': True,
                                                'QueryHeaderSize': True, 'QueryPayloadRaw': True, 'ResponseStatusCode': True, 'ResponseSize': True,
                                                'CallDuration': True, 'AccountId': True},
                                          Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')},
                                          ResultsPerPage=5)
        assert not ret.response.ResponseContext.RequestId == ret.response.Logs[0].RequestId

    def test_T3201_valid_ResultsPerPage_value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=100)
        assert len(ret.response.Logs) != 0
        # ret.check_response()

    def test_T3202_valid_NextPageToken_value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=2)
        assert len(ret.response.Logs) <= 2
        if hasattr(ret.response, 'NextPageToken'):
            ret1 = self.a1_r1.oapi.ReadApiLogs(NextPageToken=ret.response.NextPageToken, ResultsPerPage=2)
            assert len(ret.response.Logs) <= 2
            assert ret.response.Logs[0].RequestId != ret1.response.Logs[0].RequestId
            assert ret.response.Logs[0].RequestId != ret1.response.Logs[1].RequestId
            assert ret.response.Logs[1].RequestId != ret1.response.Logs[0].RequestId
            assert ret.response.Logs[1].RequestId != ret1.response.Logs[1].RequestId
