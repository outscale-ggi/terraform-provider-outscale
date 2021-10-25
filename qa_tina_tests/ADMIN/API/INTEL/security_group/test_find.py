from qa_test_tools.config.configuration import Configuration
from qa_tina_tools.test_base import OscTinaTest


class Test_find(OscTinaTest):

    def test_T6058_with_tags(self):
        group_id = None
        try:
            ret = self.a1_r1.intel.security_group.create(owner=self.a1_r1.config.account.account_id, name='test', description='test')
            group_id = ret.response.result.id
            print(ret.response.result.display())
            tag1 = {"key1": "value1"}
            tag2 = {"key2": "value2"}
            tags = dict(tag1, **tag2)
            self.a1_r1.intel.tag.create(owner=self.a1_r1.config.account.account_id, resource_id=[group_id], tags=tags)
            assert len(self.a1_r1.intel.tag.find(key=["key1"]).response.result) == 1
            assert len(self.a1_r1.intel.tag.find(value=["value2"]).response.result) == 1
            assert len(self.a1_r1.intel.tag.find().response.result) >= 1
            assert len(self.a1_r1.intel.tag.find(key=['key1', 'key2']).response.result) == 2
            assert len(self.a1_r1.intel.tag.find(value=['value1', 'value2']).response.result) == 2
        except Exception as error:
            raise error
        finally:
            if group_id:
                self.a1_r1.intel.security_group.delete(owner=self.a1_r1.config.account.account_id , group_id=group_id)
