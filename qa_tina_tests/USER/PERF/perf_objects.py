from datetime import datetime
import os
from string import ascii_lowercase

from qa_test_tools import misc
from qa_tina_tests.USER.PERF.perf_common import log_error
from qa_tina_tools.tina import storage


def func_objects(oscsdk, func, service, logger, size, result):
    connector = getattr(oscsdk, service)
    bucket_name = None
    upload_done = False
    path_to_file = None
    try:
        tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
        connector.create_bucket(Bucket=tmp)
        bucket_name = tmp
        if os.sys.platform != 'darwin':
            size = size.upper()
        path_to_file = storage.write_big_data(size, 'data.txt')
        if func == 'multipart_upload':
            mpu = storage.s3multipartupload(
                oscsdk,
                service,
                bucket_name,
                'data.txt',
                path_to_file)
            # abort all multipart uploads for this bucket (optional, for starting over)
            mpu.abort_all()
            # create new multipart upload
            mpu_id = mpu.create()
            connector.list_multipart_uploads(Bucket=bucket_name)
            # upload parts
            logger.debug("beginning of the multipart_upload"+size)
            start_upload = datetime.now()
            parts = mpu.upload(mpu_id)
            upload_duration = (datetime.now() - start_upload).total_seconds()
            upload_done = True
            result["multipart_upload" + service + size] = upload_duration
            logger.debug("end of the multipart_upload"+size)
            logger.debug("beginning of the list_parts"+size)
            start_list_parts = datetime.now()
            connector.list_parts(Bucket=bucket_name, Key='data.txt', UploadId=mpu_id)
            list_parts_duration = (datetime.now() - start_list_parts).total_seconds()
            result["list_parts" + service + size] = list_parts_duration
            logger.debug("end of the list_parts"+size)
            logger.debug("beginning of the list_multipart_uploads"+size)
            start_list_multipart_uploads = datetime.now()
            connector.list_multipart_uploads(Bucket=bucket_name)
            list_list_multipart_uploads = (datetime.now() - start_list_multipart_uploads).total_seconds()
            result["list_multipart_uploads" + service + size] = list_list_multipart_uploads
            logger.debug("end of the list_multipart_uploads"+size)
            mpu.complete(mpu_id, parts)
        elif func == 'put_object':
            data = open(path_to_file, "r")
            logger.debug("beginning of the put_object"+size)
            start_put_object = datetime.now()
            body = str.encode(data.read())
            connector.put_object(Bucket=bucket_name, Key='data.txt', Body=body)
            put_object_duration = (datetime.now() - start_put_object).total_seconds()
            upload_done = True
            result["put_object" + service + size] = put_object_duration
            logger.debug("end of the put_object"+size)
            logger.debug("beginning of the get_object"+size)
            start_get_object = datetime.now()
            connector.get_object(Bucket=bucket_name, Key='data.txt')
            get_object_duration = (datetime.now() - start_get_object).total_seconds()
            result["get_object" + service + size] = get_object_duration
            logger.debug("end of the get_object")
    except Exception as error:
        log_error(logger, error, "Unexpected error while executing %s".format("bucket_operations"), result)
    finally:
        errors = []
        if path_to_file and os.path.isfile(path_to_file):
            try:
                os.remove(path_to_file)
            except Exception as error:
                errors.append(error)
        if upload_done:
            try:
                connector.delete_object(Bucket=bucket_name, Key='data.txt')
            except Exception as error:
                errors.append(error)
        if bucket_name:
            try:
                connector.delete_bucket(Bucket=bucket_name)
            except Exception as error:
                errors.append(error)
