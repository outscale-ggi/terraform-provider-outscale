from netaddr import IPNetwork

from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.oapi import create_Vms, delete_Vms
from qa_sdk_common.exceptions.osc_exceptions import OscException


class Test_server_groups_priority(OscTestSuite):

    def test_T5802_groups_priority_on_privateip(self):
        try:
            groupe_name= 'test_priority'
            self.a1_r1.intel.hardware.create_group(name=groupe_name)
            self.a1_r1.intel.hardware.set_account_bindings(account=self.a1_r1.config.account.account_id,
                                                           groups=[groupe_name,'default', 'PRODUCTION'])
            subnet_info = self.a1_r1.intel.subnet.find(network='vpc-00000000', az=self.a1_r1.config.region.az_name)
            groups = subnet_info.response.result[0].reservation
            groups.append(groupe_name)
            self.a1_r1.intel.subnet.reserve(subnet_id=subnet_info.response.result[0].id,
                                            groups=groups)
            vm_info = create_Vms(self.a1_r1, 10)
            ip_priv_list= {vm['PrivateIp'] for vm in vm_info['vms']}

            for ip_priv in ip_priv_list:
                assert ip_priv in IPNetwork(subnet_info.response.result[0].cidr)
        except OscException as error:
            raise error
        finally:
            self.a1_r1.intel.hardware.set_account_bindings(account=self.a1_r1.config.account.account_id,
                                                           groups=['default', 'PRODUCTION'])
            self.a1_r1.intel.hardware.remove_group(group=groupe_name)
            if vm_info:
                delete_Vms(self.a1_r1, vm_info)
