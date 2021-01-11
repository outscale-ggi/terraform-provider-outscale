from qa_test_tools.test_base import OscTestSuite


class Test_revoke(OscTestSuite):

    def test_T3566_with_negative_protocol_value(self):
        group_id = None
        try:
            ret = self.a1_r1.intel.security_group.create(owner=self.a1_r1.config.account.account_id, name='test', description='test')
            group_id = ret.response.result.id
            print(ret.response.result.display())
            self.a1_r1.intel.security_group.revoke(owner=self.a1_r1.config.account.account_id, group=group_id,
                                                   authorizations=[{'protocol': '-1', 'ports': (-1, -1), 'cidrs': ['0.0.0.0/32'], 'way': 'in'}])
        except Exception as error:
            raise error
        finally: 
            if group_id:
                self.a1_r1.intel.security_group.delete(owner=self.a1_r1.config.account.account_id , group_id=group_id)
