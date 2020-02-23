from qa_common_tools.test_base import OscTestSuite

class Test_revoke(OscTestSuite):

    def test_T3566_with_negative_protocol_value(self):
        try:
            ret = self.a1_r1.intel.security_group.create(owner=self.a1_r1.config.account.account_id, name='test', description='test')
            print(ret.response.result)
            self.a1_r1.intel.security_group.revoke(owner=self.a1_r1.config.account.account_id, group=ret.response.result,
                                                   authorizations=[{'protocol': '-1', 'ports': (-1, -1), 'cidrs': ['0.0.0.0/32'], 'way': 'in'}])
        finally: 
            self.a1_r1.intel.security_group.delete(owner=self.a1_r1.config.account.account_id , group_id=ret.response.result)
    