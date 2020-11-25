from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_instances
from qa_tina_tools.tools.tina.info_keys import SUBNETS, SUBNET_ID


class Test_butterfly_vpc(OscTestSuite):
    
    def test_T5057_butterfly_vpc(self):
        vpc_info = None
        inst_info = None
        try:
            vpc_info = create_vpc(self.a1_r1, nb_instance=0, tags=[{'Key': 'osc.fcu.butterfly', 'Value': True}])
            inst_info = create_instances(self.a1_r1, subnet_id=vpc_info[SUBNETS][0][SUBNET_ID], threshold=20)
            assert False, 'Remove known error'
        except AssertionError as error:
            message = None
            try:
                message = error.args[0]
            except:
                pass
            if message and message.startswith('Threshold reach for wait_instances_state'):
                known_error('TINA-6012', 'Instance did not reach running state')
            raise error    
        finally:
            if inst_info:
                try:
                    delete_instances(self.a1_r1, inst_info)
                except:
                    pass
            if vpc_info:
                try:
                    delete_vpc(self.a1_r1, vpc_info)
                except:
                    pass
