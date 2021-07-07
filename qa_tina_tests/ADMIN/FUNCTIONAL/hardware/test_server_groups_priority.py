from netaddr import IPNetwork

from qa_sdk_common.exceptions.osc_exceptions import OscException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.oapi import create_Vms, delete_Vms
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes


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

    def test_T5803_groups_priority_on_shards(self):
        try:
            io1_shards = '/vm2'
            shard_info = self.a1_r1.intel.storage.get_shard(mount_point=io1_shards)
            ret = self.a1_r1.intel.storage.set_shard_tags(mount_point=io1_shards,
                    tags={'volumeType':shard_info.response.result.tags[0].value + ',standard'})
            groupe_name= 'test_priority'
            self.a1_r1.intel.hardware.create_group(name=groupe_name)
            self.a1_r1.intel.hardware.set_account_bindings(account=self.a1_r1.config.account.account_id,
                                                           groups=[groupe_name,'default', 'PRODUCTION'])
            groups = shard_info.response.result.reservation
            groups.append(groupe_name)
            self.a1_r1.intel.storage.reserve_shard(shard=io1_shards,
                                            groups=groups)
            _,vol_id_list = create_volumes(self.a1_r1, count=20)
            ret = self.a1_r1.intel.data_file.find(owner=self.a1_r1.config.account.account_id)
            assert {vol.shards[0] for vol in ret.response.result} == {io1_shards}
        except OscException as error:
            raise error
        finally:
            ret = self.a1_r1.intel.storage.set_shard_tags(mount_point=io1_shards,
                    tags={'volumeType':shard_info.response.result.tags[0].value})
            self.a1_r1.intel.hardware.set_account_bindings(account=self.a1_r1.config.account.account_id,
                                                           groups=['default', 'PRODUCTION'])
            self.a1_r1.intel.hardware.remove_group(group=groupe_name)
            if vol_id_list:
                delete_volumes(self.a1_r1, vol_id_list)
