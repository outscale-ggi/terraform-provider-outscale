from qa_common_tools.config import config_constants as constants
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import wait_tools, delete_tools


class Test_create(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create, cls).teardown_class()

    def test_T4896_with_resource_tags(self):
        resource_tags = {'instance': {'name': 'toto'}, 'volume': {'name': 'titi'}}
        model = {
            'ami': self.a1_r1.config.region.get_info(constants.CENTOS7),
            'resource_tags': resource_tags,
            'type': "t2.nano",
        }
        try:
            ret = self.a1_r1.oapi.CreateSecurityGroup(Description="test_desc", SecurityGroupName="test_name")
            sgid = ret.response.SecurityGroup.SecurityGroupId
            result = self.a1_r1.intel.instance.create(owner=self.a1_r1.config.account.account_id, model=model,
                                                min_count=1, max_count=1, groups=[sgid])
            wait_tools.wait_instances_state(self.a1_r1, [result.response.result.instances[0].id], "running")
            ret = self.a1_r1.oapi.ReadTags(Filters={'Keys': ['name'], 'Values': ['toto'], "ResourceIds": [result.response.result.instances[0].id]})
            assert len(ret.response.Tags) == 1
            ret = self.a1_r1.oapi.ReadTags(Filters={'Keys': ['name'], 'Values': ['titi']})
            assert len(ret.response.Tags) == 1
        finally:
            if result:
                delete_tools.terminate_instances(self.a1_r1, [result.response.result.instances[0].id])
            if sgid:
                self.a1_r1.oapi.DeleteSecurityGroup(SecurityGroupId=sgid)
