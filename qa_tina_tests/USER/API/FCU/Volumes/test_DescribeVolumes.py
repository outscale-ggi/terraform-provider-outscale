
import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException, \
    OscSdkException
from qa_test_tools.test_base import OscTestSuite, get_export_value, known_error
from qa_tina_tools.constants import VOLUME_SIZES, VOLUME_IOPS
from qa_tina_tools.tools.tina.create_tools import create_volumes, create_instances_old
from qa_tina_tools.tools.tina.delete_tools import delete_volumes, delete_instances_old 


class Test_DescribeVolumes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeVolumes, cls).setup_class()
        cls.vol_id_list = []
        for key, value in list(VOLUME_SIZES.items()):
            iops = None
            if key in list(VOLUME_IOPS.keys()):
                iops = VOLUME_IOPS[key]['min_iops']
            _, vol_ids = create_volumes(osc_sdk=cls.a1_r1, volume_type=key, size=value['min_size'], iops=iops, state='available')
            cls.vol_id_list.extend(vol_ids)

    @classmethod
    def teardown_class(cls):
        delete_volumes(osc_sdk=cls.a1_r1, volume_id_list=cls.vol_id_list)
        super(Test_DescribeVolumes, cls).teardown_class()

    def test_T1235_no_volumes_available(self):
        ret = self.a2_r1.fcu.DescribeVolumes()
        assert ret.response.volumeSet is None, "No volumes expected"

    def test_T1234_without_params(self):
        ret = self.a1_r1.fcu.DescribeVolumes()
        pattern = re.compile(r'^vol-[0-9a-f]{8}$')
        try:
            for vol in ret.response.volumeSet:
                assert vol.status == 'available'
                assert vol.availabilityZone == self.a1_r1.config.region.az_name
                assert vol.volumeType in list(VOLUME_SIZES.keys())
                assert re.match(pattern, vol.volumeId)
                if vol.volumeType in list(VOLUME_IOPS.keys()):
                    assert vol.iops == str(VOLUME_IOPS[vol.volumeType]['min_iops'])
                elif vol.volumeType == 'gp2':
                    assert vol.iops == str(max(int(vol.size) * 3, 100))
                assert vol.attachmentSet is None
                assert vol.tagSet is None
                assert vol.snapshotId is None
                assert vol.size == str(VOLUME_SIZES[vol.volumeType]['min_size'])
        except AttributeError as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                known_error('GTW-1368', 'Missing snapshot id in response')
            raise error
        assert len(ret.response.volumeSet) == len(VOLUME_SIZES), "The Number of volumes does not match"

    def test_T1237_with_filter_size(self):
        filtered_size = VOLUME_SIZES['standard']['min_size']
        ret = self.a1_r1.fcu.DescribeVolumes(Filter=[{'Name': 'size', 'Value': filtered_size}])
        nb_expected_vol = 0
        expected_type_list = []
        for key, value in list(VOLUME_SIZES.items()):
            if value['min_size'] == filtered_size:
                nb_expected_vol += 1
                expected_type_list.append(key)
        try:
            for vol in ret.response.volumeSet:
                assert vol.volumeType in expected_type_list
                assert vol.size == str(filtered_size)
        except AssertionError as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                known_error('GTW-1368', 'Filtering does not function')
            raise error
        assert len(ret.response.volumeSet) == nb_expected_vol, "The Number of volumes does not match"

    def test_T1238_dry_run(self):
        try:
            self.a1_r1.fcu.DescribeVolumes(DryRun='true')
            assert False, 'DryRun should have failed'
        except OscSdkException as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                known_error('GTW-1368', 'DryRun response is incorrect, missing request id')
            raise error
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'DryRunOperation'

    def test_T1239_with_filter_status(self):
        inst_id = None
        try:
            ret, inst_ids = create_instances_old(self.a1_r1, state='running')
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
            assert len(ret.response.volumeSet) == len(VOLUME_SIZES), "The Number of volumes does not match"
        except AssertionError as error:
            if get_export_value('OSC_USE_GATEWAY', False):
                known_error('GTW-1368', 'Filtering does not function')
            raise error
        finally:
            if inst_id:
                delete_instances_old(osc_sdk=self.a1_r1, instance_id_list=[inst_id])
