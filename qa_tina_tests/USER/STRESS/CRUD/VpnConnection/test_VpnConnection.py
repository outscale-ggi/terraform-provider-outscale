
import time
import pytest

from qa_test_tools.config.configuration import Configuration
from qa_test_tools.test_base import known_error
from qa_test_tools.exceptions.test_exceptions import OscTestException

from qa_tina_tools.tina import wait, cleanup
from qa_tina_tools.test_base import OscTinaTest


@pytest.mark.region_admin
class Test_VpnConnection(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_VpnConnection, cls).setup_class()
        cls.loop = 20
        ret = cls.a1_r1.oapi.CreateClientGateway(BgpAsn=12, PublicIp=Configuration.get('ipaddress', 'cgw_ip'), ConnectionType='ipsec.1')
        cls.cgw_id = ret.response.ClientGateway.ClientGatewayId
        wait.wait_ClientGateways_state(cls.a1_r1, [cls.cgw_id], state='available')

    @classmethod
    def teardown_class(cls):
        try:
            cleanup.cleanup_ClientGateways(cls.a1_r1, force=True)
        finally:
            super(Test_VpnConnection, cls).teardown_class()


    def test_T5986_create_delete_vpn_connection(self):
        vpn_ids = []
        vgw_ids = []
        vpn_id = None
        vgw_id = None
        errors = []
        for _ in range(self.loop):
            try:
                ret = self.a1_r1.fcu.CreateVpnGateway(Type="ipsec.1")
                vgw_id = ret.response.vpnGateway.vpnGatewayId
                vgw_ids.append(vgw_id)
                ret = self.a1_r1.fcu.CreateVpnConnection(CustomerGatewayId=self.cgw_id, Type='ipsec.1', VpnGatewayId=vgw_id)
                vpn_id = ret.response.vpnConnection.vpnConnectionId
                vpn_ids.append(vpn_id)
            except Exception as error:
                errors.append(error)
            finally:
                if vpn_id:
                    self.a1_r1.fcu.DeleteVpnConnection(VpnConnectionId=vpn_id)
                    wait.wait_VpnConnections_state(self.a1_r1, vpn_connection_ids=[vpn_id], state="deleted", wait_time=5, threshold=40, cleanup=True)
                if vgw_id:
                    self.a1_r1.fcu.DeleteVpnGateway(VpnGatewayId=vgw_id)
        time.sleep(300)
        print(vpn_ids)
        print(vgw_ids)
        error_call_ids = []
        pending_call_ids = []
        try:
            # check calls
            ret = self.a1_r1.intel.call.find(with_details=True)
            # print(ret.response.display())
            for pending_call in ret.response.result:
                found = False
                if not found:
                    for vpn_id in vpn_ids:
                        if vpn_id in pending_call.callback:
                            found = True
                            break
                if not found:
                    for vgw_id in vgw_ids:
                        if vgw_id in pending_call.callback:
                            found = True
                            break
                if found:
                    if pending_call.state == 'error':
                        error_call_ids.append(pending_call.id)
                    else:
                        pending_call_ids.append(pending_call.id)
        except Exception as error:
            print(error)
            raise error
        if pending_call_ids or error_call_ids:
            print(pending_call_ids)
            print(error_call_ids)
            for call_id in pending_call_ids:
                self.a1_r1.intel.core.async_cancel(id=call_id)
            for call_id in error_call_ids:
                self.a1_r1.intel.core.async_cancel(id=call_id)
            known_error('TINA-6764', 'Pending calls remain when actions are done to close together')
            raise OscTestException('{} calls detected.'.format(len(pending_call_ids) + len(error_call_ids)))
        assert False, 'Remove known error code'
        if errors:
            print(errors)
            raise OscTestException('{} errors occurred.'.format(len(errors)))
