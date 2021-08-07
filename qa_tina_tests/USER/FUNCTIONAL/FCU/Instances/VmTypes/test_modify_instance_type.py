
import os
import re

from qa_test_tools.config import config_constants
from qa_test_tools.compare_objects import verify_response, create_hints
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import create_tools, delete_tools, wait_tools, info_keys


class Test_modify_instance_type(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.vpc_info = None
        # attention, this only works if default type is not aws type
        super(Test_modify_instance_type, cls).setup_class()
        cls.default_type = cls.a1_r1.config.region.get_info(config_constants.DEFAULT_INSTANCE_TYPE)
        try:
            regex = r"(tinav([1-5]).c([0-9]*)r([0-9]*)(p([0-9]*))?)"
            res = re.match(regex, cls.default_type)
            cls.new_type = 'tinav{}.c{}r{}{}'.format(res.group(2), int(res.group(3)) + 1, int(res.group(4)) + 1, res.group(5))
            cls.inst_info = create_tools.create_instances(cls.a1_r1)
            cls.vpc_info = create_tools.create_vpc(cls.a1_r1, nb_instance=1)

            hints = []
            hints.append(cls.a1_r1.config.account.account_id)
            hints.append(cls.a1_r1.config.region.name)
            hints.append(cls.a1_r1.config.region.az_name)
            hints.append(cls.a1_r1.config.region.get_info(config_constants.CENTOS_LATEST))

            hints.append(cls.inst_info[info_keys.INSTANCE_ID_LIST][0])
            hints.append(cls.inst_info[info_keys.SECURITY_GROUP_ID])
            hints.append(cls.inst_info[info_keys.KEY_PAIR][info_keys.NAME])

            hints.append(cls.vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST][0])
            hints.append(cls.vpc_info[info_keys.SUBNETS][0][info_keys.SECURITY_GROUP_ID])
            hints.append(cls.vpc_info[info_keys.VPC_ID])
            hints.append(cls.vpc_info[info_keys.SUBNETS][0][info_keys.SUBNET_ID])

            cls.hints = create_hints(hints)
            cls.ignored_keys = ['reservationId',
                                'groupName',
                                'privateDnsName',
                                'dnsName',
                                'launchTime',
                                'ipAddress',
                                'privateIpAddress',
                                'blockDeviceMapping',
                                'networkInterfaceSet']
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_tools.delete_instances(cls.a1_r1, cls.inst_info)
            if cls.vpc_info:
                delete_tools.delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_modify_instance_type, cls).teardown_class()

    def verif_instance_type(self, instanceid, new_type, test_name, is_private):
        wait_tools.wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[instanceid], state='running')
        resp = self.a1_r1.fcu.DescribeInstances(InstanceId=[instanceid]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_before_{}.json'.format(test_name)),
                        hints=self.hints, ignored_keys=self.ignored_keys)
        delete_tools.stop_instances(osc_sdk=self.a1_r1, instance_id_list=[instanceid])
        wait_tools.wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[instanceid], state='stopped')
        self.a1_r1.fcu.ModifyInstanceAttribute(InstanceId=instanceid, InstanceType={'Value': new_type})
        create_tools.start_instances(osc_sdk=self.a1_r1, instance_id_list=[instanceid], state='running')
        resp = self.a1_r1.fcu.DescribeInstances(InstanceId=[instanceid]).response
        if is_private:
            assert hasattr(resp.reservationSet[0].instancesSet[0], 'subnetId') and resp.reservationSet[0].instancesSet[0].subnetId
            assert hasattr(resp.reservationSet[0].instancesSet[0], 'vpcId') and resp.reservationSet[0].instancesSet[0].vpcId
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_after_{}.json'.format(test_name)),
                        hints=self.hints, ignored_keys=self.ignored_keys)

    def test_T5854_modify_type_inst_public(self):
        self.verif_instance_type(self.inst_info[info_keys.INSTANCE_ID_LIST][0], self.new_type, 'public', False)

    def test_T5855_modify_type_inst_private(self):
        self.verif_instance_type(self.vpc_info[info_keys.SUBNETS][0][info_keys.INSTANCE_ID_LIST][0], self.new_type, 'private', True)
