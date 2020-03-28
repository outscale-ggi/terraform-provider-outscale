from qa_common_tools.test_base import OscTestSuite


class Test_get_servers(OscTestSuite):

    def test_T1917_without_param(self):
        ret = self.a1_r1.intel.hardware.get_servers()
        assert ret.status_code == 200
        if ret.response.result:
            for server in ret.response.result:
                assert server.cluster is not None
                # assert server.cluster_id is not None
                assert server.cpu_count is not None
                assert server.cpu_family is not None
                assert server.cpu_kind is not None
                assert server.creation_date is not None
                # assert server.dedicated_owner is not None
                # assert server.groups is not None
                # assert server.hostname is not None
                # assert server.maintenance is not None
                assert server.memory is not None
                assert server.mode is not None
                assert server.name is not None
                # assert server.note is not None
                assert server.os is not None
                # assert server.runid is not None
                assert server.state is not None
                # assert server.tags is not None
                assert server.type is not None
                assert server.vm_core is not None
                assert server.vm_core_begin is not None
                assert server.vm_core_overcommit is not None
                assert server.vm_count is not None
                assert server.vm_type is not None

    def test_T4740_with_export_format_param(self):
        ret = self.a1_r1.intel.hardware.get_servers(export_format='with_expanded_details')
        assert ret.status_code == 200
        if ret.response.result:
            for server in ret.response.result:
                for tag in server.tags:
                    assert tag.key != tag.key.lower()
                assert server.cluster is not None
                # assert server.cluster_id is not None
                assert server.cpu_count is not None
                assert server.cpu_family is not None
                assert server.cpu_kind is not None
                assert server.creation_date is not None
                # assert server.dedicated_owner is not None
                # assert server.groups is not None
                # assert server.hostname is not None
                # assert server.maintenance is not None
                assert server.memory is not None
                assert server.mode is not None
                assert server.name is not None
                # assert server.note is not None
                assert server.os is not None
                # assert server.runid is not None
                assert server.state is not None
                # assert server.tags is not None
                assert server.type is not None
                assert server.vm_core is not None
                assert server.vm_core_begin is not None
                assert server.vm_core_overcommit is not None
                assert server.vm_count is not None
                assert server.vm_type is not None
