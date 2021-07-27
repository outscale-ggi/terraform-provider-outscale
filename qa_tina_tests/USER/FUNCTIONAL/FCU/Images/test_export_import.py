from string import ascii_lowercase
from time import sleep

import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.config import config_constants as constants
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_instances, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_volumes
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, INSTANCE_SET, KEY_PAIR, PATH
from qa_tina_tools.tools.tina.wait_tools import wait_volumes_state, wait_images_state
from qa_tina_tools.tina import check_tools


@pytest.mark.region_storageservice
class Test_export_import(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        super(Test_export_import, cls).setup_class()
        try:
            cls.inst_info = create_instances(cls.a1_r1, state='running')
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            try:
                if cls.inst_info:
                    delete_instances(cls.a1_r1, cls.inst_info)
            except Exception as error:
                raise error
        finally:
            super(Test_export_import, cls).teardown_class()

    def verify_inst_img(self, inst_id, image_id):
        desc_inst = self.a1_r1.fcu.DescribeInstances(InstanceId=[inst_id]).response.reservationSet[0].instancesSet[0]
        desc_img = self.a1_r1.fcu.DescribeImages(ImageId=[image_id]).response.imagesSet[0]
        # TODO do more assert stuff, for now just volumes
        assert len(desc_inst.blockDeviceMapping) == len(desc_img.blockDeviceMapping)

    def test_T3706_with_io1_volume(self):
        image_id = None
        imp_image_id = None
        vol_id_list = None
        ret_attach = None
        bucket = None
        bucket_name = id_generator(prefix="bucket", chars=ascii_lowercase)
        inst_info = None
        try:
            inst_id = self.inst_info[INSTANCE_ID_LIST][0]
            # create io1 volume
            _, vol_id_list = create_volumes(self.a1_r1, iops=100, volume_type='io1', state='available')
            # _, vol_id_list = create_volumes(self.a1_r1, volume_type='standard', state='available')
            # attach volume
            ret_attach = self.a1_r1.fcu.AttachVolume(InstanceId=inst_id, VolumeId=vol_id_list[0], Device='/dev/xvdb')
            wait_volumes_state(self.a1_r1, vol_id_list, state='in-use')
            # create image
            image_id = self.a1_r1.fcu.CreateImage(InstanceId=inst_id, Name=id_generator(prefix='omi_')).response.imageId
            wait_images_state(self.a1_r1, [image_id], state='available')

            self.verify_inst_img(inst_id, image_id)

            # create bucket
            bucket = self.a1_r1.storageservice.create_bucket(Bucket=bucket_name)
            # export image
            ret_export = self.a1_r1.fcu.CreateImageExportTask(ImageId=image_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                             'OsuBucket': bucket_name}).response.imageExportTask
            ret = None
            for _ in range(60):
                ret = self.a1_r1.fcu.DescribeImageExportTasks(ImageExportTaskId=ret_export.imageExportTaskId)
                if ret.response.imageExportTaskSet[0].state == 'completed':
                    break
                ret = None
                sleep(5)
            if not ret:
                raise OscTestException("Export task did not reach 'completed' state")

            # import image
            ret = self.a1_r1.fcu.RegisterImage(ImageLocation=ret.response.imageExportTaskSet[0].exportToOsu.osuManifestUrl)
            imp_image_id = ret.response.imageId
            wait_images_state(self.a1_r1, [imp_image_id], state='available')
            # create instance
            inst_info = create_instances(self.a1_r1, omi_id=imp_image_id, state='running')
            imp_inst_id = inst_info[INSTANCE_ID_LIST][0]

            # verify instance is running with attached volume
            self.verify_inst_img(imp_inst_id, imp_image_id)

        except Exception as error:
            raise error
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
            if imp_image_id:
                cleanup_images(self.a1_r1, image_id_list=[imp_image_id], force=True)
            if bucket:
                ret = self.a1_r1.storageservice.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in ret:
                    for obj in ret['Contents']:
                        self.a1_r1.storageservice.delete_object(Bucket=bucket_name, Key=obj['Key'])
                self.a1_r1.storageservice.delete_bucket(Bucket=bucket_name)
            if image_id:
                cleanup_images(self.a1_r1, image_id_list=[image_id], force=True)
            if ret_attach:
                self.a1_r1.fcu.DetachVolume(InstanceId=inst_id, VolumeId=vol_id_list[0])
                wait_volumes_state(self.a1_r1, vol_id_list, state='available')
            if vol_id_list:
                delete_volumes(self.a1_r1, vol_id_list)

    def test_T5450_check_file_after_import_the_image(self):
        image_id = None
        imp_image_id = None
        vol_id_list = []
        ret_attach = None
        bucket = None
        bucket_name = id_generator(prefix="bucket", chars=ascii_lowercase)
        inst_info = None
        try:
            inst_id = self.inst_info[INSTANCE_ID_LIST][0]
            sshclient = check_tools.check_ssh_connection(self.a1_r1, self.inst_info[INSTANCE_SET][0]['instanceId'],
                                                         self.inst_info[INSTANCE_SET][0]['ipAddress'], self.inst_info[KEY_PAIR][PATH],
                                                         self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            cmd = 'sudo mkdir test'
            _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            # create image
            image_id = self.a1_r1.fcu.CreateImage(InstanceId=inst_id, Name=id_generator(prefix='omi_')).response.imageId
            wait_images_state(self.a1_r1, [image_id], state='available')

            self.verify_inst_img(inst_id, image_id)

            # create bucket
            bucket = self.a1_r1.storageservice.create_bucket(Bucket=bucket_name)
            # export image
            ret_export = self.a1_r1.fcu.CreateImageExportTask(ImageId=image_id, ExportToOsu={'DiskImageFormat': 'qcow2',
                                                                                             'OsuBucket': bucket_name}).response.imageExportTask
            ret = None
            for _ in range(60):
                ret = self.a1_r1.fcu.DescribeImageExportTasks(ImageExportTaskId=ret_export.imageExportTaskId)
                if ret.response.imageExportTaskSet[0].state == 'completed':
                    break
                ret = None
                sleep(5)
            if not ret:
                raise OscTestException("Export task did not reach 'completed' state")

            # import image
            ret = self.a1_r1.fcu.RegisterImage(ImageLocation=ret.response.imageExportTaskSet[0].exportToOsu.osuManifestUrl)
            imp_image_id = ret.response.imageId
            wait_images_state(self.a1_r1, [imp_image_id], state='available')
            # create instance
            inst_info = create_instances(self.a1_r1, omi_id=imp_image_id, state='running')
            imp_inst_id = inst_info[INSTANCE_ID_LIST][0]

            # verify instance is running with attached volume
            self.verify_inst_img(imp_inst_id, imp_image_id)
            sshclient = check_tools.check_ssh_connection(self.a1_r1, self.inst_info[INSTANCE_SET][0]['instanceId'],
                                                         self.inst_info[INSTANCE_SET][0]['ipAddress'],
                                                         self.inst_info[KEY_PAIR][PATH],
                                                         self.a1_r1.config.region.get_info(constants.CENTOS_USER))
            cmd = 'sudo cd test'
            _, status, _ = SshTools.exec_command_paramiko(sshclient, cmd)
            assert not status, "SSH command was not executed correctly on the remote host"

        except Exception as error:
            raise error
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)
            if imp_image_id:
                cleanup_images(self.a1_r1, image_id_list=[imp_image_id], force=True)
            if bucket:
                ret = self.a1_r1.storageservice.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in ret:
                    for obj in ret['Contents']:
                        self.a1_r1.storageservice.delete_object(Bucket=bucket_name, Key=obj['Key'])
                self.a1_r1.storageservice.delete_bucket(Bucket=bucket_name)
            if image_id:
                cleanup_images(self.a1_r1, image_id_list=[image_id], force=True)
            if ret_attach:
                self.a1_r1.fcu.DetachVolume(InstanceId=inst_id, VolumeId=vol_id_list[0])
                wait_volumes_state(self.a1_r1, vol_id_list, state='available')
            if vol_id_list:
                delete_volumes(self.a1_r1, vol_id_list)
