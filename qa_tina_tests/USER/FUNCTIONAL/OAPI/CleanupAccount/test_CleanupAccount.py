import os

from qa_tina_tools.test_base import OscTinaTest


class Test_CleanupAccount(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_CleanupAccount, cls).setup_class()
        if not os.getenv('OSC_CU', None):
            return
        try:
            # create items
            # ------------
            # CreateAccessKeyRequest
            cls.CreateAccessKeyResponse = cls.a1_r1.oapi.CreateAccessKey().response
            # CreateAccountRequest, not tested
            # CreateClientGatewayRequest
            # CreateDhcpOptionsRequest
            # CreateDirectLinkInterfaceRequest
            # CreateFlexibleGpuRequest
            # CreateImageExportTaskRequest
            # CreateImageRequest
            # CreateInternetServiceRequest
            # CreateKeypairRequest
            # CreateListenerRuleRequest
            # CreateLoadBalancerListenersRequest
            # CreateLoadBalancerPolicyRequest
            # CreateLoadBalancerRequest
            # CreateLoadBalancerTagsRequest
            # CreateNatServiceRequest
            # CreateNetAccessPointRequest
            # CreateNetPeeringRequest
            # CreateNetRequest
            # CreateNicRequest
            # CreatePublicIpRequest
            # CreateRouteRequest
            # CreateRouteTableRequest
            # CreateSecurityGroupRequest
            # CreateSecurityGroupRuleRequest
            # CreateServerCertificateRequest
            # CreateSnapshotExportTaskRequest
            # CreateSnapshotRequest
            # CreateSubnetRequest
            # CreateTagsRequest
            # CreateVirtualGatewayRequest
            # CreateVmsRequest
            # CreateVolumeRequest
            # CreateVpnConnectionRequest
            # CreateVpnConnectionRouteRequest

        except:
            print('Caught exception')
            raise

#     def test_TXXX_cleanup_account(self):
#         if not os.getenv('OSC_CU', False):
#             pytest.skip('Only executed when account is created')
#         try:
#             cleanup.cleanup_Account(self.a1_r1)
#         except Exception as error:
#             raise error
