import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.config import config_constants
from qa_tina_tools.tina import oapi, info_keys, wait


PUBLIC_NET_IP_RANGE_SUFFIX = '10.0'


class Test_net_access_point(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_net_access_point, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_net_access_point, cls).teardown_class()

    @pytest.mark.region_storageservice
    def test_T5540_netaccesspoint_for_storage_service(self):
        net_with_internet_info = None
        net_access_point = None
        net_access_point_service_name = None
        try:
            net_with_internet_info = oapi.create_Net(self.a1_r1, nb_subnet=3, nb_vm=1, state=None, cidr_prefix=PUBLIC_NET_IP_RANGE_SUFFIX)
            self.a1_r1.oapi.CreateSecurityGroupRule(
                SecurityGroupId=net_with_internet_info[info_keys.SUBNETS][1][info_keys.SECURITY_GROUP_ID],
                IpProtocol='icmp', FromPortRange=-1, ToPortRange=-1, Flow='Inbound',
                IpRange=net_with_internet_info[info_keys.SUBNETS][0][info_keys.IP_RANGE])
            for index in [1, 2]:
                self.a1_r1.oapi.CreateSecurityGroupRule(
                    SecurityGroupId=net_with_internet_info[info_keys.SUBNETS][index][info_keys.SECURITY_GROUP_ID],
                    IpProtocol='tcp', FromPortRange=22, ToPortRange=22, Flow='Inbound',
                    IpRange=net_with_internet_info[info_keys.SUBNETS][0][info_keys.IP_RANGE])
            try:
                net_access_point_service_name = self.a1_r1.config.region.get_info(config_constants.OSU_SERVICE_NAME)
            except ValueError:
                tmp_list = self.a1_r1.config.region.get_info(config_constants.HOST).split('.')
                tmp_list.reverse()
                net_access_point_service_name = '{}.{}'.format('.'.join(tmp_list), self.a1_r1.config.region.get_info(config_constants.STORAGESERVICE))
            net_access_point = self.a1_r1.oapi.CreateNetAccessPoint(
                    NetId=net_with_internet_info[info_keys.NET_ID],
                    ServiceName=net_access_point_service_name,
                    RouteTableIds=[net_with_internet_info[info_keys.SUBNETS][2][info_keys.ROUTE_TABLE_ID]]).response.NetAccessPoint

            wait.wait_Vms_state(self.a1_r1, [net_with_internet_info[info_keys.SUBNETS][0][info_keys.VM_IDS][0]],
                                state='ready')

            sshclient = SshTools.check_connection_paramiko(
                net_with_internet_info[info_keys.SUBNETS][0][info_keys.PUBLIC_IP]['PublicIp'],
                net_with_internet_info[info_keys.KEY_PAIR][info_keys.PATH],
                username=self.a1_r1.config.region.get_info(config_constants.CENTOS_USER), retry=4, timeout=10)
            tmp_list = net_access_point_service_name.split('.')
            tmp_list.reverse()
            cmd = "curl -k https://{}".format('.'.join(tmp_list))
            wait.wait_Vms_state(self.a1_r1, [net_with_internet_info[info_keys.SUBNETS][2][info_keys.VM_IDS][0]],
                                state='ready')
            sshclient_jhost = SshTools.check_connection_paramiko_nested(
                sshclient=sshclient,
                ip_address=net_with_internet_info[info_keys.SUBNETS][0][info_keys.PUBLIC_IP]['PublicIp'],
                ssh_key=net_with_internet_info[info_keys.KEY_PAIR][info_keys.PATH],
                local_private_addr=net_with_internet_info[info_keys.SUBNETS][0][info_keys.VMS][0]['PrivateIp'],
                dest_private_addr=net_with_internet_info[info_keys.SUBNETS][2][info_keys.VMS][0]['PrivateIp'],
                username=self.a1_r1.config.region.get_info(config_constants.CENTOS_USER),
                retry=4, timeout=10)
            out, _, _ = SshTools.exec_command_paramiko(sshclient_jhost, cmd, retry=20, timeout=20)
            assert 'Access Denied' in out
        finally:
            errors = []
            if net_access_point:
                try:
                    self.a1_r1.oapi.DeleteNetAccessPoint(NetAccessPointId=net_access_point.NetAccessPointId)
                except Exception as error:
                    errors.append(error)
            if net_with_internet_info:
                try:
                    oapi.delete_Net(self.a1_r1, net_with_internet_info)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise OscTestException('Found {} errors while cleaning resources : \n{}'.format(len(errors), [str(err) for err in errors]))
