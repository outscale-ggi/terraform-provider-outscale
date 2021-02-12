from string import ascii_lowercase

import pytest
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina import check_tools
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances, stop_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_SET, KEY_PAIR, PATH, INSTANCE_ID_LIST
from qa_tina_tools.tools.tina.wait_tools import wait_snapshots_state, wait_volumes_state, \
    wait_snapshot_export_tasks_state, wait_images_state


class Test_create_image_from_snapshot(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_image_from_snapshot, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_image_from_snapshot, cls).teardown_class()

    @pytest.mark.tag_redwire
    def test_T1572_create_image_from_snapshot(self):
        ci1_info = None
        ci2_info = None
        ret_ri = None
        ret_cs = None
        try:
            # run instance
            ci1_info = create_instances(self.a1_r1, state='ready')
            assert len(ci1_info[INSTANCE_SET]) == 1
            instance = ci1_info[INSTANCE_SET][0]
            # check instance connection
            check_tools.check_ssh_connection(self.a1_r1, ci1_info[INSTANCE_ID_LIST][0], instance['ipAddress'], ci1_info[KEY_PAIR][PATH],
                                             username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # SshTools.check_connection_paramiko(instance['ipAddress'], ci1_info[KEY_PAIR][PATH],
            # username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # get instance boot disk
            assert len(instance['blockDeviceMapping']) == 1
            # stop instance
            stop_instances(self.a1_r1, ci1_info[INSTANCE_ID_LIST], force=True, wait=True)
            # snapshot instance boot disk
            ret_cs = self.a1_r1.fcu.CreateSnapshot(VolumeId=instance['blockDeviceMapping'][0]['ebs']['volumeId'])
            wait_snapshots_state(self.a1_r1, [ret_cs.response.snapshotId], 'completed')
            # create omi from snapshot
            image_name = id_generator(prefix='img_')
            ret_ri = self.a1_r1.fcu.RegisterImage(BlockDeviceMapping=[{'Ebs': {'SnapshotId': ret_cs.response.snapshotId}, 'DeviceName': '/dev/sda1'}],
                                                  Name=image_name, RootDeviceName='/dev/sda1', Architecture='x86_64')
            # run instance with new omi
            ci2_info = create_instances(self.a1_r1, state='ready', omi_id=ret_ri.response.imageId)
            assert len(ci2_info[INSTANCE_SET]) == 1
            # check instance connection
            check_tools.check_ssh_connection(self.a1_r1, ci2_info[INSTANCE_ID_LIST][0], ci2_info[INSTANCE_SET][0]['ipAddress'],
                                             ci2_info[KEY_PAIR][PATH], username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            # SshTools.check_connection_paramiko(ci2_info[INSTANCE_SET][0]['ipAddress'], ci2_info[KEY_PAIR][PATH],
            # username=self.a1_r1.config.region.get_info(constants.CENTOS_USER))
        finally:
            errors = []
            if ci2_info:
                try:
                    delete_instances(self.a1_r1, ci2_info)
                except Exception as error:
                    errors.append(error)
            if ci1_info:
                try:
                    delete_instances(self.a1_r1, ci1_info)
                except Exception as error:
                    errors.append(error)
            if ret_ri:
                try:
                    cleanup_images(self.a1_r1, image_id_list=[ret_ri.response.imageId], force=True)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise OscTestException('Found {} errors while cleaning resources : \n{}'.format(len(errors), errors))

    @pytest.mark.region_admin
    def test_T5246_create_image_from_snapshot_without_product_type(self):
        ret_ri = None
        ret_cs = None
        vol_id = None
        try:
            ret = self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name, Size='1')
            vol_id = ret.response.volumeId
            wait_volumes_state(osc_sdk=self.a1_r1, state='available', volume_id_list=[vol_id])
            # snapshot volume
            ret_cs = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id)
            wait_snapshots_state(self.a1_r1, [ret_cs.response.snapshotId], 'completed')
            ret = self.a1_r1.fcu.GetProductType(SnapshotId=ret_cs.response.snapshotId)
            assert ret.response.productTypeId == '0001'
            self.a1_r1.intel.product.set(resource=ret_cs.response.snapshotId, product_ids=[])
            ret = self.a1_r1.fcu.GetProductType(SnapshotId=ret_cs.response.snapshotId)
            assert not ret.response.productTypeId
            # create omi from snapshot
            image_name = id_generator(prefix='img_')
            ret_ri = self.a1_r1.fcu.RegisterImage(
                BlockDeviceMapping=[{'Ebs': {'SnapshotId': ret_cs.response.snapshotId},
                                     'DeviceName': '/dev/sda1'}], Name=image_name,
                RootDeviceName='/dev/sda1', Architecture='x86_64')
            ret = self.a1_r1.fcu.GetProductType(ImageId=ret_ri.response.imageId)
            assert ret.response.productTypeId == '0001'
        finally:
            errors = []
            if ret_ri:
                try:
                    cleanup_images(self.a1_r1, image_id_list=[ret_ri.response.imageId], force=True)
                except Exception as error:
                    errors.append(error)
            if vol_id:
                # remove volume
                try:
                    self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                    wait_volumes_state(osc_sdk=self.a1_r1, cleanup=True, volume_id_list=[vol_id])
                except Exception as error:
                    errors.append(error)
            if errors:
                raise OscTestException('Found {} errors while cleaning resources : \n{}'.format(len(errors), errors))

    @pytest.mark.region_admin
    @pytest.mark.region_storageservice
    def test_T5458_create_image_from_imported_snapshot_and_check_product_type_and_accounting(self):
        ret_ri = None
        ret_cs = None
        vol_id = None
        snap_id = None
        key = None
        inst_info = None
        types = set()
        try:
            ret = self.a1_r1.fcu.CreateVolume(AvailabilityZone=self.a1_r1.config.region.az_name, Size='1')
            vol_id = ret.response.volumeId
            wait_volumes_state(osc_sdk=self.a1_r1, state='available', volume_id_list=[vol_id])
            # snapshot volume
            ret_cs = self.a1_r1.fcu.CreateSnapshot(VolumeId=vol_id)
            wait_snapshots_state(self.a1_r1, [ret_cs.response.snapshotId], 'completed')
            ret = self.a1_r1.fcu.GetProductType(SnapshotId=ret_cs.response.snapshotId)
            assert ret.response.productTypeId == '0001'
            bucket_name = id_generator(prefix='snap', chars=ascii_lowercase)
            ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=ret_cs.response.snapshotId,
                                                          ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                       'OsuBucket': bucket_name})
            task_id = ret.response.snapshotExportTask.snapshotExportTaskId
            wait_snapshot_export_tasks_state(osc_sdk=self.a1_r1, state='completed',
                                             snapshot_export_task_id_list=[task_id])
            # import snapshot
            k_list = self.a1_r1.storageservice.list_objects(Bucket=bucket_name)
            if 'Contents' in list(k_list.keys()):
                key = k_list['Contents'][0]['Key']
            else:
                assert False, "Key not found on storageservice"
            params = {'Bucket': bucket_name, 'Key': key}
            url = self.a1_r1.storageservice.generate_presigned_url(ClientMethod='get_object', Params=params,
                                                                   ExpiresIn=3600)
            ret = self.a1_r1.fcu.DescribeSnapshots(SnapshotId=[ret_cs.response.snapshotId])
            size = ret.response.snapshotSet[0].volumeSize
            gb_to_byte = int(size) * pow(1024, 3)
            ret = self.a1_r1.fcu.ImportSnapshot(snapshotLocation=url, snapshotSize=gb_to_byte,
                                                description='This is a snapshot test')
            snap_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=self.a1_r1, state='completed', snapshot_id_list=[snap_id])
            # create omi from snapshot
            image_name = id_generator(prefix='img_')
            ret_ri = self.a1_r1.fcu.RegisterImage(
                BlockDeviceMapping=[{'Ebs': {'SnapshotId': snap_id},
                                     'DeviceName': '/dev/sda1'}], Name=image_name,
                RootDeviceName='/dev/sda1', Architecture='x86_64')
            ret = self.a1_r1.fcu.GetProductType(ImageId=ret_ri.response.imageId)
            assert ret.response.productTypeId == '0001'
            imp_image_id = ret_ri.response.imageId
            wait_images_state(self.a1_r1, [imp_image_id], state='available')
            inst_info = create_instances(self.a1_r1, omi_id=imp_image_id, state='running')
            ret = self.a1_r1.intel.accounting.find(owner=self.a1_r1.config.account.account_id, instance=inst_info[INSTANCE_ID_LIST][0])
            for accounting in ret.response.result:
                assert accounting.type in ['ProductUsage:{}'.format(self.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE)),
                                           'BoxUsage:{}'.format(self.a1_r1.config.region.get_info(constants.DEFAULT_INSTANCE_TYPE))]
                types.add(accounting.type)
            assert len(types) == 2
            print(ret)

        finally:
            errors = []
            if ret_ri:
                try:
                    cleanup_images(self.a1_r1, image_id_list=[ret_ri.response.imageId], force=True)
                except Exception as error:
                    errors.append(error)
            if vol_id:
                # remove volume
                try:
                    self.a1_r1.fcu.DeleteVolume(VolumeId=vol_id)
                    wait_volumes_state(osc_sdk=self.a1_r1, cleanup=True, volume_id_list=[vol_id])
                except Exception as error:
                    errors.append(error)
            if ret_cs.response.snapshotId:
                try:
                    self.a1_r1.fcu.DeleteSnapshot(SnapshotId=ret_cs.response.snapshotId)
                except Exception as error:
                    errors.append(error)
            if inst_info:
                try:
                    delete_instances(self.a1_r1, inst_info)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise OscTestException('Found {} errors while cleaning resources : \n{}'.format(len(errors), errors))
