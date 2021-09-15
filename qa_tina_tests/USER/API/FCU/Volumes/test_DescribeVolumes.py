import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException

from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools import constants
from qa_tina_tools.tools.tina import create_tools, delete_tools


class Test_DescribeVolumes(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVolumes, cls).setup_class()
        cls.vol_id_list = []
        for key, value in list(constants.VOLUME_SIZES.items()):
            iops = None
            if key in list(constants.VOLUME_IOPS.keys()):
                iops = constants.VOLUME_IOPS[key]['min_iops']
            _, vol_ids = create_tools.create_volumes(osc_sdk=cls.a1_r1, volume_type=key, size=value['min_size'], iops=iops, state='available')
            cls.vol_id_list.extend(vol_ids)
        if len(constants.VOLUME_SIZES) < 4:
            _, vol_ids = create_tools.create_volumes(osc_sdk=cls.a1_r1, count=4 - len(constants.VOLUME_SIZES),
                                                     size=constants.VOLUME_SIZES['standard']['min_size'], state='available')
            cls.vol_id_list.extend(vol_ids)

    @classmethod
    def teardown_class(cls):
        delete_tools.delete_volumes(osc_sdk=cls.a1_r1, volume_id_list=cls.vol_id_list)
        super(Test_DescribeVolumes, cls).teardown_class()

    def test_T1235_no_volumes_available(self):
        ret = self.a2_r1.fcu.DescribeVolumes()
        assert ret.response.volumeSet is None, "No volumes expected"

    def test_T1234_without_params(self):
        ret = self.a1_r1.fcu.DescribeVolumes()
        pattern = re.compile(r'^vol-[0-9a-f]{8}$')
        for vol in ret.response.volumeSet:
            assert vol.status == 'available'
            assert vol.availabilityZone == self.a1_r1.config.region.az_name
            assert vol.volumeType in list(constants.VOLUME_SIZES.keys())
            assert re.match(pattern, vol.volumeId)
            if vol.volumeType in list(constants.VOLUME_IOPS.keys()):
                assert vol.iops == str(constants.VOLUME_IOPS[vol.volumeType]['min_iops'])
            elif vol.volumeType == 'gp2':
                assert vol.iops == str(max(int(vol.size) * 3, 100))
            assert vol.attachmentSet is None
            assert vol.snapshotId is None
            assert vol.size == str(constants.VOLUME_SIZES[vol.volumeType]['min_size'])
        assert len(ret.response.volumeSet) == max(len(constants.VOLUME_SIZES), 4), "The Number of volumes does not match"

    def test_T1237_with_filter_size(self):
        filtered_size = constants.VOLUME_SIZES['standard']['min_size']
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'size', 'Value': filtered_size}])
        nb_expected_vol = 0
        expected_type_list = []
        for key, value in list(constants.VOLUME_SIZES.items()):
            if value['min_size'] == filtered_size:
                nb_expected_vol += 1
                expected_type_list.append(key)
        for vol in ret.response.volumeSet:
            assert vol.volumeType in expected_type_list
            assert vol.size == str(filtered_size)
        assert len(ret.response.volumeSet) == nb_expected_vol + max(0, 4 - len(constants.VOLUME_SIZES)), "The Number of volumes does not match"

    def test_T1238_dry_run(self):
        try:
            self.a1_r1.fcu.DescribeVolumes(DryRun='true')
            assert False, 'DryRun should have failed'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'DryRunOperation'

    def test_T1239_with_filter_status(self):
        inst_id = None
        try:
            ret, inst_ids = create_tools.create_instances_old(self.a1_r1, state='running')
            inst_id = inst_ids[0]
            ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'status', 'Value': 'in-use'}])
            assert len(ret.response.volumeSet) == 1, "The Number of volumes does not match"
            assert ret.response.volumeSet[0].status == 'in-use'
            assert ret.response.volumeSet[0].attachmentSet[0].status == 'attached'
            assert ret.response.volumeSet[0].attachmentSet[0].volumeId == ret.response.volumeSet[0].volumeId
            assert ret.response.volumeSet[0].attachmentSet[0].instanceId == inst_id
            assert ret.response.volumeSet[0].attachmentSet[0].deleteOnTermination == 'true'
            assert ret.response.volumeSet[0].attachmentSet[0].device == '/dev/sda1'
            ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'status', 'Value': 'available'}])
            for vol in ret.response.volumeSet:
                assert vol.status == 'available'
                assert vol.attachmentSet is None
            assert len(ret.response.volumeSet) == max(len(constants.VOLUME_SIZES), 4), "The Number of volumes does not match"
        finally:
            if inst_id:
                delete_tools.delete_instances_old(osc_sdk=self.a1_r1, instance_id_list=[inst_id])

    def test_T5944_valid_filter_by_tag_key(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag-key', 'Value': 'key2'}])
        assert len(ret.response.volumeSet) == 2

    def test_T5945_valid_filter_by_tag_value(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag-value', 'Value': 'value2'}])
        assert len(ret.response.volumeSet) == 2

    def test_T5946_valid_filter_by_tag_key_and_value(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag:key1', 'Value': 'value2'}])
        assert len(ret.response.volumeSet) == 1

    def test_T5947_filter_by_tag_key_and_value_wildcard(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag:key2', 'Value': '*'}])
        assert len(ret.response.volumeSet) == 2

    def test_T5948_one_tag_key_multiple_tag_values(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag:key2', 'Value': ['value1', 'value2']}])
        assert len(ret.response.volumeSet) == 2

    def test_T5949_multiple_tag_keys(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag-key', 'Value': ['key1', 'key2']}])
        assert len(ret.response.volumeSet) == 3

    def test_T5950_multiple_tag_values(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag-value', 'Value': ['value1', 'value2']}])
        assert len(ret.response.volumeSet) == 3

    def test_T5951_multiple_tag_key_value(self):
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'tag:key1', 'Value': 'value2'}, {'Name': 'tag:key2', 'Value': 'value2'}])
        assert ret.response.volumeSet is None
