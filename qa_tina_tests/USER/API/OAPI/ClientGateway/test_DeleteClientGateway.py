
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteClientGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteClientGateway, cls).setup_class()
        cls.cg_id = cls.a1_r1.oapi.CreateClientGateway(
            BgpAsn=65000, PublicIp='172.10.8.9', ConnectionType='ipsec.1').response.ClientGateway.ClientGatewayId

    @classmethod
    def teardown_class(cls):
        try:
            if cls.cg_id:
                cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cls.cg_id)
        finally:
            super(Test_DeleteClientGateway, cls).teardown_class()

    def test_T3315_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteClientGateway()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3316_invalid_client_gateway_id(self):
        try:
            self.a1_r1.oapi.DeleteClientGateway(ClientGatewayId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')
        try:
            self.a1_r1.oapi.DeleteClientGateway(ClientGatewayId='cgw-1234567')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')
        try:
            self.a1_r1.oapi.DeleteClientGateway(ClientGatewayId='cgw-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T3317_unknown_client_gateway_id(self):
        try:
            self.a1_r1.oapi.DeleteClientGateway(ClientGatewayId='cgw-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5015')

    def test_T3695_dry_run(self):
        ret = self.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=self.cg_id, DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3696_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteClientGateway(ClientGatewayId=self.cg_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5015')

    def test_T3318_valid_case(self):
        self.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=self.cg_id)
        self.cg_id = None
