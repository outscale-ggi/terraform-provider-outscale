
from qa_tina_tools.tina import oapi, info_keys
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools import misc


class Test_delete_attached_security_group(OscTestSuite):

    def test_T5659_delete_attached_security_group(self):

        lb_info = None
        vpc_info = None
        try:
            vpc_info = oapi.create_Net(self.a1_r1)
            sg_id = oapi.create_SecurityGroup(self.a1_r1, net_id=vpc_info[info_keys.NET_ID])
            lb_info = oapi.create_LoadBalancer(self.a1_r1, misc.id_generator(prefix='lb-'),
                                               subnets=[vpc_info[info_keys.SUBNETS][0][info_keys.SUBNET_ID]], sg=[sg_id])
            self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sg_id)
            sg_id = None
        except Exception as error:
            raise error
        finally:
            if lb_info:
                oapi.delete_LoadBalancer(self.a1_r1, lb_info)
            if sg_id:
                oapi.delete_SecurityGroup(self.a1_r1, sg_id)
            if vpc_info:
                oapi.delete_Net(self.a1_r1, vpc_info)
