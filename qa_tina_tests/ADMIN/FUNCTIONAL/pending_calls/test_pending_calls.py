# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import time

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SUBNETS, SUBNET_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state


class Test_pending_calls(OscTestSuite):

    def test_T5327_create_delete_lbu_in_vpc_without_wait(self):
        vpc_info = None
        lbu_name = None
        try:
            vpc_info = create_vpc(self.a1_r1)
            self.logger.debug("Created VPC: %s", vpc_info[VPC_ID])

            name = id_generator(prefix='lb')
            self.a1_r1.lbu.CreateLoadBalancer(LoadBalancerName=name,
                                              Listeners=[{'InstancePort': '80', 'LoadBalancerPort': '80', 'Protocol': 'HTTP'}], Scheme='internal',
                                              Subnets=[vpc_info[SUBNETS][0][SUBNET_ID]])
            lbu_name = name
            self.logger.debug("Created LBU: %s", lbu_name)
            time.sleep(2)

        finally:
            if lbu_name:
                self.a1_r1.lbu.DeleteLoadBalancer(LoadBalancerName=lbu_name)
            if vpc_info:
                cleanup_vpcs(self.a1_r1, vpc_id_list=[vpc_info[VPC_ID]])

        self.logger.debug("Wait...")
        time.sleep(60)

        # Check pending calls
        call_found = False
        resp = self.a1_r1.intel.call.find().response
        for call in resp.result:
            if vpc_info[VPC_ID] in call.target or vpc_info[VPC_ID] in call.resources or lbu_name in call.target or lbu_name in call.resources:
                self.logger.error(call.display())
                call_found = True
                self.a1_r1.intel.core.async_cancel(id=call.id)
        assert not call_found
