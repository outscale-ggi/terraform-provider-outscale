# pylint: disable=missing-docstring

from qa_common_tools.test_base import OscTestSuite


class Test_ReadVmTypes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ReadVmTypes, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_ReadVmTypes, cls).teardown_class()

    def test_T3663_empty_filters(self):
        ret = self.a1_r1.oapi.ReadVmTypes().response.VmTypes
        assert len(ret) > 1
        for inst in ret:
            assert hasattr(inst, 'BsuOptimized')
            assert hasattr(inst, 'VmTypeName')
            assert hasattr(inst, 'MemorySize')
            assert hasattr(inst, 'VolumeCount')
            if inst.VolumeCount:
                assert hasattr(inst, 'VolumeSize')
            assert hasattr(inst, 'VcoreCount')
            assert hasattr(inst, 'MaxPrivateIps')

    def test_T3664_with_filter_vm_type_names(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VmTypeNames': ['t2.nano']}).response.VmTypes
        assert len(ret) == 1
        assert ret[0].VmTypeName == 't2.nano'

    def test_T3665_with_filter_storage_sizes(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VolumeSizes': [40]}).response.VmTypes
        assert len(ret) >= 1
        for inst in ret:
            assert inst.VolumeSize == 40

    def test_T3666_with_filter_storage_counts(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VolumeCounts': [1]}).response.VmTypes
        assert len(ret) >= 1
        for inst in ret:
            assert inst.VolumeCount == 1

    def test_T3667_with_filter_vcore_counts(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VcoreCounts': [1]}).response.VmTypes
        assert len(ret) >= 1
        for inst in ret:
            assert inst.VcoreCount == 1

    def test_T3668_with_filter_bsu_optimized_true(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'BsuOptimized': True}).response.VmTypes
        assert len(ret) >= 1
        for inst in ret:
            assert inst.BsuOptimized

    def test_T3669_with_filter_bsu_optimized_false(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'BsuOptimized': False}).response.VmTypes
        assert len(ret) >= 1
        for inst in ret:
            assert not inst.BsuOptimized

    def test_T3670_with_filter_invalid_vm_type_names(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VmTypeNames': ['foo']}).response.VmTypes
        assert len(ret) == 0

    def test_T3671_with_filter_invalid_memory(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'MemorySizes': [40]}).response.VmTypes
        assert len(ret) == 0

    def test_T3672_with_filter_invalid_storage_size(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VolumeSizes': [400000]}).response.VmTypes
        assert len(ret) == 0

    def test_T3673_with_filter_invalid_vcore_size(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VcoreCounts': [8000000]}).response.VmTypes
        assert len(ret) == 0

    def test_T3674_with_filter_invalid_storage_count(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'VolumeCounts': [800000]}).response.VmTypes
        assert len(ret) == 0

    def test_T3675_with_filter_memory_sizes(self):
        ret = self.a1_r1.oapi.ReadVmTypes(Filters={'MemorySizes': [4]}).response.VmTypes
        assert len(ret) >= 1
        for inst in ret:
            assert inst.MemorySize == 4.0
