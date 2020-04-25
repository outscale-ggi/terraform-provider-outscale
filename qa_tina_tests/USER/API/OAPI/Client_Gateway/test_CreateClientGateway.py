# -*- coding:utf-8 -*-

from qa_test_tools.test_base import OscTestSuite, known_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.API.OAPI.Client_Gateway.ClientGateway import validate_client_gateway
from qa_test_tools.misc import assert_oapi_error, assert_dry_run


class Test_CreateClientGateway(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateClientGateway, cls).setup_class()
        cls.cg_id = None

    @classmethod
    def teardown_class(cls):
        try:
            if cls.cg_id:
                cls.a1_r1.oapi.DeleteClientGateway(ClientGatewayId=cls.cg_id)
        finally:
            super(Test_CreateClientGateway, cls).teardown_class()

    def test_T3310_empty_param(self):
        try:
            self.a1_r1.oapi.CreateClientGateway()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateClientGateway(ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateClientGateway(ConnectionType='ipsec.1', BgpAsn=10)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateClientGateway(ConnectionType='ipsec.1', PublicIp='172.10.8.9')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=10, PublicIp='172.10.8.9')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T3311_invalid_connection_type(self):
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=10, PublicIp='172.10.8.9', ConnectionType='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T3312_invalid_bgp_asn(self):
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=-1, PublicIp='172.10.8.9', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4010')
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=4294967296, PublicIp='172.10.8.9', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4010')

    def test_T3313_invalid_public_ip(self):
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=0, PublicIp='tata', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=0, PublicIp='10.0.0.1', ConnectionType='ipsec.1')
            known_error('GTW-1306', 'Could create ClientGateway with private ip')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4030')
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=0, PublicIp='2001:0db8:0000:85a3:0000:0000:ac1f:8001', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=0, PublicIp='241.491.144.2', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T3314_valid_case(self):
        ret = self.a1_r1.oapi.CreateClientGateway(
            BgpAsn=65000, PublicIp='172.10.8.9', ConnectionType='ipsec.1').response.ClientGateway
        validate_client_gateway(ret, expected_cg={
            'PublicIp': '172.10.8.9',
            'BgpAsn': 65000,
            'ConnectionType': 'ipsec.1',
        })

    def test_T3694_dry_run(self):
        ret = self.a1_r1.oapi.CreateClientGateway(BgpAsn=65000, PublicIp='172.10.8.9', ConnectionType='ipsec.1', DryRun=True)
        assert_dry_run(ret)
