import pytest

from qa_tina_tests.USER.FUNCTIONAL.FCU.Volumes.create_volume import CreateVolume


@pytest.mark.region_io1
class Test_create_volume_io1(CreateVolume):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_create_volume_io1, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_volume_io1, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T68_create_volume_io1(self):
        self.create_volume(volume_type='io1', iops=100, volume_size=4)

    def test_T3158_check_iops_volume_io1(self):
        self.create_volume(volume_type='io1', volume_size=100, perf_iops=4, iops=1000, drive_letter_code='b')

    def test_T4591_check_iops_volume_io1_ratio_30(self):
        self.create_volume(volume_type='io1', volume_size=100, perf_iops=4, iops=3000, drive_letter_code='b')

    def test_T4592_check_iops_volume_io1_ratio_300(self):
        self.create_volume(volume_type='io1', volume_size=10, perf_iops=4, iops=3000, drive_letter_code='b')
