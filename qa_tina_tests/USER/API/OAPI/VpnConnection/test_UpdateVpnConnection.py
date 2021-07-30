
from qa_tina_tools.test_base import OscTinaTest
# from qa_tina_tools.tina import oapi, wait


class Test_UpdateVpnConnection(OscTinaTest):
    pass

#     @classmethod
#     def setup_class(cls):
#         cls.net_info = None
#         cls.virtual_gateway = None
#         cls.client_gateway = None
#         cls.vpn_connection = None
#         super(Test_DeleteVpnConnection, cls).setup_class()
#         try:
#             cls.net_info = oapi.create_Net(cls.a1_r1)
#         except:
#             try:
#                 cls.teardown_class()
#             finally:
#                 raise
#
#     @classmethod
#     def teardown_class(cls):
#         try:
#             if cls.net_info:
#                 oapi.delete_Net(cls.a1_r1, cls.net_info)
#         finally:
#             super(Test_DeleteVpnConnection, cls).teardown_class()
#
#     def setup_method(self, method):
#         self.virtual_gateway = None
#         self.client_gateway = None
#         self.vpn_connection = None
#         OscTinaTest.setup_method(self, method)
#         try:
#             self.virtual_gateway = self.a1_r1.CreateVirtualGateway().response.VirtualGateway
#             self.client_gateway = self.a1_r1.CreateClientGateway().response.ClientGateway
#         except:
#             try:
#                 self.teardown_method(method)
#             except:
#                 raise
#
#     def teardown_method(self, method):
#         try:
#             if self.vpn_connection:
#                 self.a1_r1.DeleteVpnConnection(VpnConnectionId=self.vpn_connection.VpnConnectionId)
#                 wait.wait_VpnConnections_state(self.a1_r1, [self.vpn_connection.VpnConnectionId], 'deleted')
#             if self.virtual_gateway:
#                 self.a1_r1.DeleteVirtualGateway(VirtualGatewayId=self.virtual_gateway.VirtualGatewayId)
#                 wait.wait_VirtualGateways_state(self.a1_r1, [self.virtual_gateway.VirtualGatewayId], 'deleted')
#             if self.client_gateway:
#                 self.a1_r1.DeleteClientGateway(ClientGatewayId=self.client_gateway.ClientGatewayId)
#         finally:
#             OscTinaTest.teardown_method(self, method)
