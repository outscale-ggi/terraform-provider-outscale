# pylint: disable=missing-docstring

from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import id_generator

NUM_GROUPS = 5


class Test_ListGroups(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.group_names = []
        cls.paths = []
        super(Test_ListGroups, cls).setup_class()
        try:
            path = '/'
            for _ in range(NUM_GROUPS):
                name = id_generator(prefix="group_name_")
                cls.a1_r1.eim.CreateGroup(GroupName=name, Path=path)
                cls.group_names.append(name)
                cls.paths.append(path)
                path = '{}{}/'.format(path, id_generator(prefix="seg"))
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            for group_name in cls.group_names:
                cls.a1_r1.eim.DeleteGroup(GroupName=group_name)
        finally:
            super(Test_ListGroups, cls).teardown_class()

    def test_T2834_without_param(self):
        ret = self.a1_r1.eim.ListGroups()
        assert len(ret.response.ListGroupsResult.Groups) == NUM_GROUPS
        names = [group.GroupName for group in ret.response.ListGroupsResult.Groups]
        paths = [group.Path for group in ret.response.ListGroupsResult.Groups]
        assert set(names) == set(self.group_names)
        assert set(paths) == set(self.paths)
        assert not hasattr(ret.response.ListGroupsResult, 'IsTruncated')
        assert not hasattr(ret.response.ListGroupsResult, 'Marker')

    def test_T3752_with_path_prefix(self):
        ret = self.a1_r1.eim.ListGroups(PathPrefix=self.paths[2])
        assert len(ret.response.ListGroupsResult.Groups) == 3
        names = [group.GroupName for group in ret.response.ListGroupsResult.Groups]
        paths = [group.Path for group in ret.response.ListGroupsResult.Groups]
        assert set(names) == set(self.group_names[2:])
        assert set(paths) == set(self.paths[2:])
        assert not hasattr(ret.response.ListGroupsResult, 'IsTruncated')
        assert not hasattr(ret.response.ListGroupsResult, 'Marker')

    def test_T3755_other_account(self):
        ret = self.a2_r1.eim.ListGroups()
        assert not ret.response.ListGroupsResult.Groups == 0
