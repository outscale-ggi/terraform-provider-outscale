from qa_test_tools.test_base import OscTestSuite, known_error


class Test_ReadQuotas(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadQuotas, cls).setup_class()
        try:
            cls.quotas_info = {
                # simple commented are 'per something' thus not in global
                # double commented are not supported
                # Compute
                'vm_limit': ('VM Limit', 'Maximum number of VM this user can own', 'Compute'),
                'core_limit': ('Core Limit', 'Maximum number of total cores (virtual core)', 'Compute'),
                'memory_limit': ('Memory Limit', 'Maximum number of total memory (GiB)', 'Compute'),
                'ip_limit': ('IP Limit', 'Maximum IP addresses the user can allocate', 'Compute'),
                'gpu_limit': ('GPU Limit', 'Maximum number of GPU the user can allocate', 'Compute'),
                'dedicated_server_limit': ('Dedicated Server Limit', 'Maximum number of dedicated servers', 'Compute'),
                # Storage
                'volume_limit': ('Volume Limit', 'Maximum number of BSU volumes', 'Storage'),
                'volume_size_limit': ('Volume Size Limit', 'Maximum cumulated size of BSU volumes (GiB)', 'Storage'),
                'io1_volume_size_limit': ('IO1 Volume Size Limit', 'Maximum cumulated size of IO1 volumes (GiB)', 'Storage'),
                'os1_volume_size_limit': ('OS1 Volume Size Limit', 'Maximum cumulated size of OS1 volumes (GiB)', 'Storage'),
                'gp2_volume_size_limit': ('GP2 Volume Size Limit', 'Maximum cumulated size of GP2 volumes (GiB)', 'Storage'),
                'st1_volume_size_limit': ('ST1 Volume Size Limit', 'Maximum cumulated size of ST1 volumes (GiB)', 'Storage'),
                'sc1_volume_size_limit': ('SC1 Volume Size Limit', 'Maximum cumulated size of SC1 volumes (GiB)', 'Storage'),
                'standard_volume_size_limit': ('Standard Volume Size Limit', 'Maximum cumulated size of standard volumes (GiB)', 'Storage'),
                'snapshot_limit': ('Snapshot Limit', 'Maximum number of snapshots', 'Storage'),
                'snapshot_export_limit': ('Snapshot Exports Limit', 'Maximum number of running snapshot export tasks', 'Storage'),
                'snapshot_copy_limit': ('Snapshot Copy Limit', 'Maximum number of in-progress snapshot copies', 'Storage'),
                'image_export_limit': ('Image Exports Limit', 'Maximum number of running image export tasks', 'Storage'),
                'image_copy_limit': ('Image Copy Limit', 'Maximum number of in-progress image copies', 'Storage'),
                'iops_limit': ('Provisioned IOPS Limit', 'Maximum number of IOPS delivered by provisioned IOPS volumes', 'Storage'),
                # Security Groups
                'sg_limit': ('Security Groups Limit', 'Maximum number of security groups', 'Security Groups'),
                # per ...
                'sg_rule_limit': ('Security Groups Rules Limit', 'Maximum number of rules per security groups', 'Security Groups'),
                # per ...
                'vm_sg_limit': ('VM Security Groups Limit', 'Maximum number of groups assigned to a VM', 'Security Groups'),
                # per ...
                'vpc_sg_limit': ('VPC Security Groups Limit', 'Maximum number of security groups per VPC', 'Security Groups'),
                # per ...
                'vpc_sg_rule_limit': ('VPC Security Groups Rules Limit', 'Maximum number of rules per VPC security group', 'Security Groups'),
                # VPC
                'vpc_limit': ('VPC Limit', 'Maximum number of VPC', 'VPC'),
                # per ...
                'subnet_limit': ('Subnet Limit', 'Maximum number of subnets per VPC', 'VPC'),
                'igw_limit': ('Internet Gateway Limit', 'Maximum number of internet gateways', 'VPC'),
                # per ...
                'rtb_limit': ('Route Table Limit', 'Maximum number of route tables per VPC', 'VPC'),
                # per ...
                'rtb_rule_limit': ('Route Limit', 'Maximum number of route rules per route table', 'VPC'),
                'bypass_vpc_limit': ('Bypass VPC limit', 'Maximum number of firewall bypassing VPCs', 'VPC'),
                'networklink_request_limit': ('Peering requests limit', 'Maximum number of peering connection in pending acceptance', 'VPC'),
                'networklink_limit': ('Peering connection limit', 'Maximum number of available peering connections per VPC', 'VPC'),
                'network_endpoint_limit': ('VPC Endpoint Limit', 'Maximum number of VPC endpoints', 'VPC'),
                'nat_gateway_limit': ('Nat Gateway Limit', 'Maximum number of NAT gateways', 'VPC'),
                # VPN
                'vpg_limit': ('VPN Gateway Limit', 'Maximum number of VPN gateways', 'VPN'),
                'cgw_limit': ('Customer Gateway Limit', 'Maximum number of CGW gateways', 'VPN'),
                'vpnc_limit': ('VPN Connection Limit', 'Maximum number of VPN connections per VPN gateway', 'VPN'),
                'bgp_route_limit': ('BGP Route Limit', 'Maximum number BGP advertised routes per VPN connection', 'VPN'),
                'static_route_limit': ('Static Route Limit', 'Maximum number of static routes per VPN connection', 'VPN'),
                # LBU
                'lb_limit': ('Load Balancer Limit', 'Maximum number of load balancers per region', 'LBU'),
                'lb_listeners_limit': ('Load Balancer Listeners Limit', 'Maximum number of listeners for load balancers', 'LBU'),
                'lb_rules_limit': ('Load Balancer Listener Rules Limit', 'Maximum number of listener rules for an account', 'LBU'),
                # Direct Link
                'dl_connection_limit': ('Direct Link Connection Limit', 'Maximum number of Direct Link connections', 'Direct Link'),
                'dl_interface_limit': ('Direct Link Interface Limit', 'Maximum number Direct Link interfaces per connections', 'Direct Link'),
                # Other
                # # not implemented
                # #'accesskey_limit': ('Access Key Limit', 'Maximum number of access key the user can own', 'Other'),
                # #'certificate_limit': ('Certificate Limit', 'Maximum number of certificate the user can own', 'Other'),
                # #'tag_limit': ('Tag Limit', 'Maximum number of tags per resource the user can create', 'Other'),
                'bypass_group_limit': ('Bypass Group Limit', 'Maximum number of bypass group the user can own', 'Other'),
                'bypass_group_size_limit': ('Bypass Group Size Limit', 'Maximum size of a bypass group', 'Other'),
                #OKMS
                'cmk_limit': ('Customer master key limit', 'Maximum number of customer master key the user can own', 'OKMS')
            }
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        super(Test_ReadQuotas, cls).teardown_class()

    def test_T735_without_param(self):
        ret = self.a1_r1.icu.ReadQuotas()
        refs = [ref_quota.Reference for ref_quota in ret.response.ReferenceQuota]
        assert len(refs) == 2
        try:
            for ref_quota in ret.response.ReferenceQuota:
                assert (ref_quota.Reference == 'global') or ref_quota.Reference.startswith('sg-')
                if ref_quota.Reference == 'global':
                    assert len(ref_quota.Quotas) <= len(self.quotas_info)
                    for quota in ret.response.ReferenceQuota[0].Quotas:
                        assert quota.Name in self.quotas_info
                        assert quota.DisplayName == self.quotas_info[quota.Name][0]
                        assert quota.Description == self.quotas_info[quota.Name][1]
                        assert quota.GroupName == self.quotas_info[quota.Name][2]
                        assert quota.DisplayName
        except AssertionError as error:
            raise error

    def test_T1622_verify_output_format(self):
        resp = self.a1_r1.icu.ReadQuotas().response
        assert hasattr(resp, 'ReferenceQuota'), 'Missing response element = ReferenceQuota'
        refs = [ref_quota.Reference for ref_quota in resp.ReferenceQuota]
        assert len(refs) == 2, 'Incorrect length of default response'
        for ref_quota in resp.ReferenceQuota:
            assert ref_quota.Reference == 'global' or ref_quota.Reference.startswith('sg_')
            if hasattr(ref_quota, 'Quotas'):
                known_error('TINA-4152', 'Inconsistent return structure names')
            assert hasattr(refs[0], 'Quota'), 'Missing referenceQuota element = Quota'
