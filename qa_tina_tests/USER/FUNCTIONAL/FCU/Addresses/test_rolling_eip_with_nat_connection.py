import requests

from qa_test_tools import misc
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import info_keys
from qa_tina_tools.tina.oapi import create_Net, delete_Net
from qa_tina_tools.tina.setup_tools import start_http_server
from qa_tina_tools.tina.wait import wait_Vms_state


class Test_rolling_eip_with_nat_connection(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_rolling_eip_with_nat_connection, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_rolling_eip_with_nat_connection, cls).teardown_class()

    def test_T4737_rolling_eip(self):
        net_info = None
        try:
            # create vpc
            net_info = create_Net(self.a1_r1, nb_vm=2, state=None)
            # add rule to accept tcp on 80
            ips = misc.get_security_group_ips(self.a1_r1.config.region)
            for addr in ips:
                self.a1_r1.oapi.CreateSecurityGroupRule(SecurityGroupId=net_info[info_keys.SUBNETS][0][info_keys.SECURITY_GROUP_ID],
                                                        IpProtocol='tcp', FromPortRange=80, ToPortRange=80, IpRange=addr, Flow='Inbound')
            wait_Vms_state(self.a1_r1, net_info[info_keys.SUBNETS][0][info_keys.VM_IDS], state='ready')
            # install http server on first instance
            start_http_server(net_info[info_keys.SUBNETS][0][info_keys.PUBLIC_IP]['PublicIp'], net_info[info_keys.KEY_PAIR][info_keys.PATH],
                              self.a1_r1.config.region.get_info(constants.CENTOS_USER), text='instance1')
            # verify access to first instance http server
            http_server_address = 'http://{}'.format(net_info[info_keys.SUBNETS][0][info_keys.PUBLIC_IP]['PublicIp'])
            self.logger.info(http_server_address)
            try:
                req = requests.get(http_server_address)
                assert req.text.strip() == 'instance1'
            except:
                self.logger.debug('Could not access http server')
                raise
            # move eip of first instance to second instance
            self.a1_r1.oapi.UnlinkPublicIp(LinkPublicIpId=net_info[info_keys.SUBNETS][0][info_keys.PUBLIC_ASSOCIATION_IP])
            net_info[info_keys.SUBNETS][0][info_keys.PUBLIC_ASSOCIATION_IP] =\
                self.a1_r1.oapi.LinkPublicIp(PublicIpId=net_info[info_keys.SUBNETS][0][info_keys.PUBLIC_IP]['PublicIpId'],
                                             VmId=net_info[info_keys.SUBNETS][0][info_keys.VM_IDS][1]).response.LinkPublicIpId
            # install http server on second instance
            start_http_server(net_info[info_keys.SUBNETS][0][info_keys.PUBLIC_IP]['PublicIp'], net_info[info_keys.KEY_PAIR][info_keys.PATH],
                              self.a1_r1.config.region.get_info(constants.CENTOS_USER), text='instance2')
            # verify access to second instance http server
            try:
                req = requests.get(http_server_address)
                assert req.text.strip() == 'instance2'
            except:
                self.logger.debug('Could not access http server')
                raise
        except Exception as error:
            raise error
        finally:
            if net_info:
                delete_Net(self.a1_r1, net_info)
