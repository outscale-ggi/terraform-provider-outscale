

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tests.USER.API.OAPI.ClientGateway.ClientGateway import validate_client_gateway
from specs import check_oapi_error


class Test_CreateClientGateway(OscTinaTest):

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
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateClientGateway(ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateClientGateway(ConnectionType='ipsec.1', BgpAsn=10)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateClientGateway(ConnectionType='ipsec.1', PublicIp='172.10.8.9')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=10, PublicIp='172.10.8.9')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 7000)

    def test_T3311_invalid_connection_type(self):
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=10, PublicIp='172.10.8.9', ConnectionType='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)

    def test_T3312_invalid_bgp_asn(self):
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=-1, PublicIp='172.10.8.9', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.data != 'The provided value (\'{bgpAsn}\') for the parameter \'BgpAsn\' is not in a valid range.':
                assert False, 'Remove known error'
                check_oapi_error(error, 4010, bgpAsn='-1')
            known_error('API-422', 'CreateClientGateway does not return the right error message')
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=4294967296, PublicIp='172.10.8.9', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if error.data != 'The provided value (\'{bgpAsn}\') for the parameter \'BgpAsn\' is not in a valid range.':
                assert False, 'Remove known error'
                check_oapi_error(error, 4010, bgpAsn='4294967296')
            known_error('API-422', 'CreateClientGateway does not return the right error message')

    def test_T3313_invalid_public_ip(self):
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=0, PublicIp='tata', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=0, PublicIp='2001:0db8:0000:85a3:0000:0000:ac1f:8001', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)
        try:
            self.a1_r1.oapi.CreateClientGateway(BgpAsn=0, PublicIp='241.491.144.2', ConnectionType='ipsec.1')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4047)

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
