from qa_tina_tools.test_base import OscTinaTest


class Test_find(OscTinaTest):

    def test_T6058_with_tags(self):
        group_id = None
        try:
            ret = self.a1_r1.intel.security_group.create(owner=self.a1_r1.config.account.account_id, name='test', description='test')
            group_id = ret.response.result.id
            print(ret.response.result.display())
            TAG1 = {"key1": "value1"}
            TAG2 = {"key2": "value2"}
            TAGS = dict(TAG1, **TAG2)
            self.a1_r1.intel.api.tag.create(owner=self.a1_r1.config.account.account_id, resource_id=[group_id], tags=TAGS)
            assert len(self.a1_r1.intel.api.tag.find(key="key1")) == 1
            assert len(self.a1_r1.intel.api.tag.find(valeur="key1")) == 1
        except Exception as error:
            raise error
        finally:
            if group_id:
                self.a1_r1.intel.security_group.delete(owner=self.a1_r1.config.account.account_id , group_id=group_id)
