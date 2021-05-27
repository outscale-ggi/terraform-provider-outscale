
from __future__ import division
import re

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.constants import VOLUME_MAX_SIZE, VOLUME_SIZES, VOLUME_IOPS, MAX_IO1_RATIO
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state


class Test_CreateVolume(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vol_id = None
        cls.snap_id = None
        super(Test_CreateVolume, cls).setup_class()
        try:
            ret = cls.a1_r1.fcu.CreateVolume(AvailabilityZone=cls.a1_r1.config.region.az_name, VolumeType='standard', Size='10')
            cls.vol_id = ret.response.volumeId
            wait_volumes_state(cls.a1_r1, [cls.vol_id], state='available', cleanup=False)
            ret = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.vol_id)
            cls.snap_id = ret.response.snapshotId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vol_id:
                cls.a1_r1.fcu.DeleteVolume(VolumeId=cls.vol_id)
            if cls.snap_id:
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snap_id)
        finally:
            super(Test_CreateVolume, cls).teardown_class()

    def create_volume_type(self, **kwargs):
        vol_id = None
        try:
            conf_parameters = {'AvailabilityZone': self.a1_r1.config.region.az_name}
            conf_parameters.update(kwargs)
            ret = self.a1_r1.fcu.CreateVolume(**conf_parameters)
            vol_id = ret.response.volumeId
            msg = "Volume expected type: {}, ".format(kwargs['VolumeType']) + "but is: {}".format(ret.response.volumeType)
            assert ret.response.volumeType == kwargs['VolumeType'], msg
            pattern = re.compile(r'^vol-[0-9a-f]{8}$')
            assert re.match(pattern, ret.response.volumeId), "Id '{}' not match pattern '{}'".format(ret.response.volumeId, pattern.pattern)
        finally:
            if vol_id:
                wait_volumes_state(self.a1_r1, [vol_id], state='available', cleanup=False)
                ret = self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, [vol_id], cleanup=True)

    def create_tests_on_volume_size_value(self, threshold=None, check_iop=False, **kwargs):
        good_exception_raise = False
        vol_id = None
        try:
            conf_parameters = {'AvailabilityZone': self.a1_r1.config.region.az_name}
            conf_parameters.update(kwargs)
            ret = self.a1_r1.fcu.CreateVolume(**conf_parameters)
            vol_id = ret.response.volumeId
            if not threshold:
                if check_iop is False:
                    msg = "Volume  size should be {}, but the created size is: {}".format(kwargs['Size'], ret.response.size)
                    assert ret.response.size == str(kwargs['Size']), msg
                else:
                    msg = "Volume created should be {} iops, but is {}".format(kwargs['Iops'], ret.response.iops)
                    assert ret.response.iops == str(kwargs['Iops']), msg

        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidParameterValue'
            assert threshold, error.message
            print((error.message))
            if check_iop:
                min_iops = VOLUME_IOPS[kwargs['VolumeType']]['min_iops']
                max_iops = VOLUME_IOPS[kwargs['VolumeType']]['max_iops']
                assert error.message == 'Invalid IOPS: {} Min: {} Max: {}'.format(kwargs['Iops'], min_iops, max_iops)
            else:
                min_size = VOLUME_SIZES[kwargs['VolumeType']]['min_size']
                max_size = VOLUME_SIZES[kwargs['VolumeType']]['max_size']
                assert error.message == "Volume size must be between '{}' and '{}'".format(min_size, max_size)
            good_exception_raise = True
        finally:
            if vol_id:
                wait_volumes_state(self.a1_r1, [vol_id], state='available', cleanup=False)
                ret = self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                wait_volumes_state(self.a1_r1, [vol_id], cleanup=True)
            if threshold:
                size = kwargs['Iops'] if check_iop is True else kwargs['Size']
                assert good_exception_raise, "Operation should have raise an exception with a size of {} as the {} is {}" \
                    .format(size, "maximum" if size > threshold else "minimum", threshold)

    def test_T695_standard(self):
        self.create_volume_type(VolumeType='standard', Size=VOLUME_SIZES['standard']['min_size'] + 1)

    def test_T696_standard_min_size(self):
        self.create_tests_on_volume_size_value(VolumeType='standard', Size=VOLUME_SIZES['standard']['min_size'])

    def test_T698_standard_max_size(self):
        self.create_tests_on_volume_size_value(VolumeType='standard', Size=VOLUME_MAX_SIZE)

    def test_T699_standard_out_of_range_max_size(self):
        self.create_tests_on_volume_size_value(threshold=VOLUME_MAX_SIZE, VolumeType='standard', Size=VOLUME_MAX_SIZE + 1)

    def test_T700_io1(self):
        self.create_volume_type(VolumeType='io1', Iops=VOLUME_IOPS['io1']['min_iops'] + 1,
                                 Size=VOLUME_SIZES['io1']['min_size'] + 1)

    def test_T701_io1_min_iops(self):
        self.create_tests_on_volume_size_value(check_iop=True, VolumeType='io1', Iops=VOLUME_IOPS['io1']['min_iops'],
                                                Size=VOLUME_SIZES['io1']['min_size'] + 1)

    def test_T702_io1_out_of_range_min_iops(self):
        try:
            self.create_tests_on_volume_size_value(threshold=VOLUME_IOPS['io1']['min_iops'], check_iop=True, VolumeType='io1',
                                                    Iops=VOLUME_IOPS['io1']['min_iops'] - 1,
                                                    Size=VOLUME_SIZES['io1']['min_size'] + 1)
            assert False, 'Remove known error code'
        except AssertionError as error:
            if str(error).startswith('Operation should have raise'):
                known_error('TINA-6383', 'iops size is not checked')
            raise error



    def test_T703_io1_max_iops(self):
        self.create_tests_on_volume_size_value(check_iop=True, VolumeType='io1', Iops=VOLUME_IOPS['io1']['max_iops'],
                                                Size=VOLUME_SIZES['io1']['max_size'])

    def test_T704_io1_out_of_range_max_iops(self):
        try:
            self.create_tests_on_volume_size_value(threshold=VOLUME_IOPS['io1']['max_iops'], check_iop=True, VolumeType='io1',
                                                    Iops=VOLUME_IOPS['io1']['max_iops'] + 1,
                                                    Size='500')
        except AssertionError as error:
            if str(error).startswith('Operation should have raise'):
                known_error('TINA-6383', 'iops size is not checked')
            raise error

    def test_T705_io1_min_size(self):
        self.create_tests_on_volume_size_value(VolumeType='io1', Size=VOLUME_SIZES['io1']['min_size'],
                                                Iops=VOLUME_IOPS['io1']['min_iops'])

    def test_T706_io1_out_of_range_min_size(self):
        self.create_tests_on_volume_size_value(threshold=VOLUME_SIZES['io1']['min_size'], VolumeType='io1',
                                                Size=VOLUME_SIZES['io1']['min_size'] - 1,
                                                Iops=VOLUME_IOPS['io1']['min_iops'])

    def test_T707_io1_max_size(self):
        self.create_tests_on_volume_size_value(VolumeType='io1', Size=VOLUME_MAX_SIZE, Iops=VOLUME_IOPS['io1']['min_iops'])

    def test_T708_io1_out_of_range_max_size(self):
        self.create_tests_on_volume_size_value(threshold=VOLUME_MAX_SIZE, VolumeType='io1', Size=VOLUME_MAX_SIZE + 1,
                                                Iops=VOLUME_IOPS['io1']['min_iops'])

    def test_T709_gp2(self):
        self.create_volume_type(VolumeType='gp2', Size=VOLUME_SIZES['gp2']['min_size'] + 1)

    def test_T710_gp2_min_size(self):
        self.create_tests_on_volume_size_value(VolumeType='gp2', Size=VOLUME_SIZES['gp2']['min_size'])

    def test_T712_gp2_max_size(self):
        self.create_tests_on_volume_size_value(VolumeType='gp2', Size=VOLUME_MAX_SIZE)

    def test_T713_gp2_out_of_range_max_size(self):
        self.create_tests_on_volume_size_value(threshold=VOLUME_MAX_SIZE, VolumeType='gp2', Size=VOLUME_MAX_SIZE + 1)

    def test_T724_no_param(self):
        try:
            self.a1_r1.fcu.CreateVolume()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: zone')

    def test_T725_dry_run(self):
        try:
            ret = self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name, Size=666, DryRun='true')
            assert ret.response.Errors.Error.Code == 'DryRunOperation', "Parameter: dryRun should trigger a 400 " \
                                                                        +"error with the tag: DryRunOpertion, " \
                                                                        +" and should block the volume's creation " \
                                                                        +"operation."
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'DryRunOperation'

    def test_T726_without_az(self):
        try:
            self.a1_r1.fcu.CreateVolume(Size=666)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: zone')

    def test_T727_with_valid_snap_id(self):
        self.create_volume_type(VolumeType='standard', Size="10", SnapshotId=self.snap_id)

    def test_T1611_with_valid_snap_id_too_small(self):
        try:
            self.create_volume_type(VolumeType='standard', Size="1", SnapshotId=self.snap_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         'SnapshotId and VolumeSize are specified and are incompatible. {} size (10 GiB) must be less than VolumeSize value (1 GiB)'
                         .format(self.snap_id))

    def test_T728_with_invalid_snap_id(self):
        try:
            self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name, VolumeType='standard',
                                        Size='1', SnapshotId="snap-12345678")
            assert False, 'Should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         'The Snapshot ID does not exist: snap-12345678, for account: {}'.format(self.a1_r1.config.account.account_id))

    def test_T729_from_other_account_snap_id(self):
        try:
            self.a2_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name, VolumeType='standard', Size='1', SnapshotId=self.snap_id)
            assert False, 'Should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSnapshot.NotFound',
                         'The Snapshot ID does not exist: {}, for account: {}'.format(self.snap_id, self.a2_r1.config.account.account_id))

    def test_T4589_io1_max_iops_ratio(self):
        self.create_volume_type(VolumeType='io1', Iops=int(((VOLUME_SIZES['io1']['min_size']) * MAX_IO1_RATIO)),
                                 Size=VOLUME_SIZES['io1']['min_size'])

    def test_T4590_io1_out_of_range_iops_ratio(self):
        try:
            self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name,
                                        Size=VOLUME_SIZES['io1']['min_size'], VolumeType='io1',
                                        Iops=int(((VOLUME_SIZES['io1']['min_size']) * MAX_IO1_RATIO)) + 1)
            assert False, 'Create Volume was not supposed to succeed'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidParameterValue'
            msg = 'Iops to volume size ratio is too high: {}. Max: {}'.format(
                (((VOLUME_SIZES['io1']['min_size']) * MAX_IO1_RATIO) + 1) / VOLUME_SIZES['io1']['min_size'], MAX_IO1_RATIO)
            assert error.message == msg

    def test_T730_with_invalid_iops_ratio(self):
        try:
            self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name,
                                        Size=VOLUME_SIZES['io1']['min_size'], VolumeType='io1',
                                        Iops=VOLUME_IOPS['io1']['max_iops'])
            assert False, 'Create Volume was not supposed to succeed'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidParameterValue'
            ratio = round(VOLUME_IOPS['io1']['max_iops'] / VOLUME_SIZES['io1']['min_size'], 1)
            msg = 'Iops to volume size ratio is too high: {}. Max: {}'.format(ratio, MAX_IO1_RATIO)
            assert error.message == msg

    def test_T2170_with_invalid_volume_type(self):
        try:
            self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name, Size=10, VolumeType='foo')
            assert False, 'Create Volume was not supposed to succeed'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value of parameter \'VolumeType\' is not valid: foo. Supported values: gp2, io1, os1, sc1, "
                         "st1, standard")
