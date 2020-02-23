import pytest

from qa_tina_tests.USER.FUNCTIONAL.FCU.Volumes.create_volume import CreateVolume


class Test_create_volume_gp2(CreateVolume):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_create_volume_gp2, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_volume_gp2, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T69_create_volume_gp2(self):
        self.create_volume(volume_type='gp2', volume_size=1)

    def test_T3159_check_iops_volume_gp2(self):
        self.create_volume(volume_type='gp2', volume_size=200, perf_iops=2, drive_letter_code='d')
