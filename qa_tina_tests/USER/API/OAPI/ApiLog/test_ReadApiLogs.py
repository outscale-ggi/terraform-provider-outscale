import time
from datetime import datetime, timedelta
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException, OscSdkException
from specs import check_oapi_error
from qa_test_tools import misc
from qa_test_tools.misc import assert_dry_run, id_generator
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina.info_keys import PUBLIC
from qa_tina_tools.tools.tina.create_tools import generate_key

param = [
    'AccountId',
    'CallDuration',
    'QueryAccessKey',
    'QueryApiName',
    'QueryApiVersion',
    'QueryCallName',
    'QueryDate',
    'QueryHeaderRaw',
    'QueryHeaderSize',
    'QueryIpAddress',
    'QueryPayloadRaw',
    'QueryPayloadSize',
    'QueryUserAgent',
    'RequestId',
    'ResponseSize',
    'ResponseStatusCode',
]


@pytest.mark.region_cloudtrace
class Test_ReadApiLogs(OscTinaTest):
    @classmethod
    def setup_class(cls):
        super(Test_ReadApiLogs, cls).setup_class()
        cls.request_id = None
        cls.request_id_a2 = None
        ret = cls.a1_r1.oapi.ReadTags()
        cls.request_id= ret.response.ResponseContext.RequestId
        cls.a1_r1.oapi.ReadSubnets()
        if hasattr(cls, "a2_r1"):
            cls.request_id_a2 = cls.a2_r1.oapi.ReadTags().response.ResponseContext.RequestId
            cls.a2_r1.oapi.ReadSubnets()
        cls.a1_r1.oapi.ReadNics()
        cls.a1_r1.oapi.ReadKeypairs()
        cls.a1_r1.oapi.ReadVms()
        cls.a1_r1.oapi.ReadVms()
        if cls.a1_r1.config.region.name in ["in-west-1", "in-west-2"]:
            cls.a1_r1.fcugtw.DescribeImages()
            cls.a1_r1.directlinkgtw.DescribeConnections()
            # KNOWN ERROR OPS-13949 IN T2810
        time.sleep(120)
        ret = None
        try:
            cls.keypair_name = id_generator(prefix='keypair_')
            generated_key = generate_key(cls.keypair_name)
            with open(generated_key[PUBLIC].encode(), 'r') as key:
                pub_key = key.read()
            ret = cls.a1_r1.oapi.CreateKeypair(KeypairName=cls.keypair_name, PublicKey=pub_key).response.Keypair
            assert ret.KeypairName == cls.keypair_name
            assert ret.KeypairFingerprint is not None
            try:
                cls.a1_r1.oapi.CreateKeypair(KeypairName=cls.keypair_name, PublicKey=pub_key)
                assert False, 'Call should not have been successful'
            except OscApiException as error:
                check_oapi_error(error, 9011)
        finally:
            if ret:
                cls.a1_r1.oapi.DeleteKeypair(KeypairName=cls.keypair_name)


    @classmethod
    def teardown_class(cls):
        super(Test_ReadApiLogs, cls).teardown_class()

    def test_T2810_valid_params(self):
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=3)
        ret.check_response()
        self.logger.debug(ret.response.display())
        assert len(ret.response.Logs) >= 1
        account_ids = {log.AccountId for log in ret.response.Logs}
        assert len(account_ids) == 1 and self.a1_r1.config.account.account_id in account_ids, 'incorrect account id(s)'
        if self.a1_r1.config.region.name == "cloudgouv-eu-west-1":
            try:
                self.a1_r1.fcugtw.DescribeImages()
                assert False, 'Remove known error'
            except OscSdkException:
                known_error('OPS-13949', 'fcu-gtw endpoint not available on SEC1')

    def test_T2823_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadApiLogs(DryRun=True)
        assert_dry_run(ret)

    def test_T3200_invalid_ResultsPerPage_value(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=1001)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4113)
        try:
            self.a1_r1.oapi.ReadApiLogs(ResultsPerPage='1001')
        except OscApiException as err:
            check_oapi_error(err, 4110)
        try:
            self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=0)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4113)

    def test_T3203_invalid_NextPageToken_value(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(NextPageToken=123456)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4110)
        try:
            self.a1_r1.oapi.ReadApiLogs(NextPageToken='')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4117)

    def test_T3204_verify_calls_on_log(self):
        call = [
            'ReadDhcpOptions',
            'ReadImages',
            'ReadNics',
            'ReadApiLogs',
            'ReadTags',
            'ReadSubnets',
            'ReadKeypairs',
            'ReadVms',
            'DescribeImages',
            'ListAccessKeys',
        ]
        ret = self.a1_r1.oapi.ReadApiLogs(
            ResultsPerPage=3, Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=200)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
        )
        assert len(ret.response.Logs) == 3
        assert ret.response.Logs[0].QueryCallName in call
        assert ret.response.Logs[1].QueryCallName in call
        assert ret.response.Logs[2].QueryCallName in call
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3205_verify_fcu_call(self):
        self.a1_r1.fcugtw.DescribeInstances()
        time.sleep(30)
        ret = self.a1_r1.oapi.ReadApiLogs(
            ResultsPerPage=100, Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=100)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
        )
        assert 'DescribeInstances' in [call.QueryCallName for call in ret.response.Logs]
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3206_valid_filter_QueryCallNames(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryCallNames": ["ReadVms"]}, ResultsPerPage=2)
        assert len(ret.response.Logs) == 2
        assert "ReadVms" in {call.QueryCallName for call in ret.response.Logs}
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3207_valid_filter_QueryAccessKeys(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryAccessKeys": [self.a1_r1.config.account.ak]})
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.ak} == {call.QueryAccessKey for call in ret.response.Logs}
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3208_valid_filter_QueryApiNames(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryApiNames": ["oapi", "aws_direct_connect", "aws_ec2"]}, ResultsPerPage=1000)
        assert len(ret.response.Logs) != 0
        assert {"oapi", "aws_direct_connect", "aws_ec2"} == {call.QueryApiName for call in ret.response.Logs}
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3209_invalid_QueryApiNames_value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryApiNames": ["fcu", "lbu", "directlink", "eim", "icu"]})
        assert not ret.response.Logs

    def test_T3210_valid_filter_QueryIpAddresses(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryIpAddresses": [misc.get_nat_ips(self.a1_r1.config.region)[0].split('/')[0]]})
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3211_valid_filter_QueryUserAgents(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryUserAgents": ["UNKNOWN"]})
        assert len(ret.response.Logs) == 0

    def test_T3213_valid_filter_ResponseStatusCodes(self):
        try:
            self.a1_r1.oapi.ReadVm()
        except Exception as error:
            check_oapi_error(error, 12000, invalid_action='ReadVm')
        time.sleep(20)
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"ResponseStatusCodes": [409, 200, ]}, ResultsPerPage=1000)
        assert len(ret.response.Logs) != 0
        assert {409, 200} == {call.ResponseStatusCode for call in ret.response.Logs}

    def test_T3214_valid_filter_QueryDateBefore(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateBefore': (datetime.utcnow()).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateBefore': (datetime.utcnow()).strftime('%Y-%m-%d')})
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3215_valid_filter_QueryDateAfter(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=50)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(seconds=50)).strftime('%Y-%m-%d')})
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3216_valid_filter_combination(self):
        ret = self.a1_r1.oapi.ReadApiLogs(
            ResultsPerPage=5, Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
        )
        if len(ret.response.Logs) == 0:
            known_error("API-347", "ReadApiLogs")
        assert False, "Remove known error"
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        assert len(ret.response.Logs) == 5
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=5, Filters={"QueryApiNames": ["oapi"], "QueryAccessKeys": [self.a1_r1.config.account.ak]})
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        assert len(ret.response.Logs) == 5
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=5, Filters={"QueryApiNames": ["oapi"], "ResponseStatusCodes": [200]})
        assert len(ret.response.Logs) == 5
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3217_invalid_filter_QueryDateAfter(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={'QueryDateAfter': '2017'})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4110)

    def test_T4179_invalid_filter_incorrect_date_order(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(
                ResultsPerPage=5,
                Filters={
                    'QueryDateAfter': (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'QueryDateBefore': (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                },
            )
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4098)

    def test_T3218_invalid_filter_ResponseStatusCodes(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={"ResponseStatusCodes": ['700']})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4110)

    def test_T3219_invalid_filter_QueryIpAddresses(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={"QueryIpAddresses": ['0.1']})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4112)

    def test_T3220_invalid_filter_QueryApiNames(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(Filters={"QueryApiNames": [1]})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 4110)

    def test_T3221_invalid_params(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(titi='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 3001)

    def test_T3222_valid_With_Value(self):
        for attr in param:
            ret = self.a1_r1.oapi.ReadApiLogs(With={attr: True}, ResultsPerPage=5)
            assert hasattr(ret.response.Logs[0], attr)
            assert hasattr(ret.response.Logs[0], "AccountId")
            assert hasattr(ret.response.Logs[0], "RequestId")
            assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3223_invalid_With_Value(self):
        try:
            self.a1_r1.oapi.ReadApiLogs(With={'toto': True}, ResultsPerPage=1)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 3001)

    def test_T3229_verify_response_of_With_Value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(
            With={
                'QueryAccessKey': True,
                'QueryIpAddress': True,
                'QueryUserAgent': True,
                'QueryCallName': True,
                'QueryApiName': True,
                'QueryApiVersion': True,
                'QueryDate': True,
                'QueryHeaderRaw': True,
                'QueryHeaderSize': True,
                'QueryPayloadRaw': True,
                'ResponseStatusCode': True,
                'ResponseSize': True,
                'CallDuration': True,
                'AccountId': True,
                'QueryPayloadSize': True,
            },
            Filters={'QueryDateAfter': (datetime.utcnow() - timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')},
            ResultsPerPage=1,
        )
        if len(ret.response.Logs) == 0:
            known_error("API-347", "ReadApiLogs")
        assert False, "Remove known error"
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        assert not ret.response.ResponseContext.RequestId == ret.response.Logs[0].RequestId
        for attr in param:
            assert hasattr(ret.response.Logs[0], attr)

    def test_T3201_valid_ResultsPerPage_value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=100)
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T3202_valid_NextPageToken_value(self):
        ret = self.a1_r1.oapi.ReadApiLogs(ResultsPerPage=2)
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        assert len(ret.response.Logs) <= 2
        ret1 = self.a1_r1.oapi.ReadApiLogs(NextPageToken=ret.response.NextPageToken, ResultsPerPage=2)
        assert len(ret.response.Logs) <= 2
        assert ret.response.Logs[0].RequestId != ret1.response.Logs[0].RequestId
        assert ret.response.Logs[0].RequestId != ret1.response.Logs[1].RequestId
        assert ret.response.Logs[1].RequestId != ret1.response.Logs[0].RequestId
        assert ret.response.Logs[1].RequestId != ret1.response.Logs[1].RequestId
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret1.response.Logs}

    def test_T5550_valid_filter_multiple_QueryCallNames(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryCallNames": ["ReadVms", "DescribeConnections"]})
        assert len(ret.response.Logs) != 0
        assert {"ReadVms", "DescribeConnections"} == {call.QueryCallName for call in ret.response.Logs}
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T5551_valid_filter_multiple_QueryAccessKeys(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"QueryAccessKeys": [self.a1_r1.config.account.ak, self.a2_r1.config.account.ak]})
        assert len(ret.response.Logs) != 0
        assert {self.a1_r1.config.account.ak} == {call.QueryAccessKey for call in ret.response.Logs}

    def test_T5552_empty_With(self):
        ret = self.a1_r1.oapi.ReadApiLogs(With={}, ResultsPerPage=1)
        assert hasattr(ret.response.Logs[0], "AccountId")
        assert hasattr(ret.response.Logs[0], "RequestId")

    def test_T5553_With_AccountId(self):
        ret = self.a1_r1.oapi.ReadApiLogs(With={'RequestId': False}, ResultsPerPage=1)
        assert hasattr(ret.response.Logs[0], "AccountId")
        assert not hasattr(ret.response.Logs[0], "RequestId")
        assert {self.a1_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}

    def test_T5554_With_RequestId(self):
        ret = self.a1_r1.oapi.ReadApiLogs(With={'AccountId': False}, ResultsPerPage=1)
        assert not hasattr(ret.response.Logs[0], "AccountId")
        assert hasattr(ret.response.Logs[0], "RequestId")

    def test_T5561_valid_filter_RequestId(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"RequestIds": [self.request_id]})
        assert len(ret.response.Logs) == 1
        assert ret.response.Logs[0].QueryCallName == "ReadTags"
        assert {self.a1_r1.config.account.ak} == {call.QueryAccessKey for call in ret.response.Logs}

    def test_T5820_with_other_AccountId(self):
        ret = self.a2_r1.oapi.ReadApiLogs()
        assert len(ret.response.Logs) != 0
        assert {self.a2_r1.config.account.account_id} == {call.AccountId for call in ret.response.Logs}
        assert {"ReadTags", "ReadSubnets"} == {call.QueryCallName for call in ret.response.Logs}

    def test_T5821_valid_filter_RequestId_with_other_account(self):
        ret = self.a1_r1.oapi.ReadApiLogs(Filters={"RequestIds": [self.request_id_a2]})
        assert len(ret.response.Logs) == 0
