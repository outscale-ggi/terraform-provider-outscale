import os
from datetime import datetime
from string import ascii_lowercase

from qa_test_tools import misc
from qa_tina_tests.USER.PERF.perf_common import log_error
from qa_tina_tools.tina import oos


def func_objects(oscsdk, func, service, logger, size, result):
    connector = getattr(oscsdk, service)
    bucket_name = None
    upload_done = False
    try:
        tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
        connector.create_bucket(Bucket=tmp)
        bucket_name = tmp
        if os.sys.platform != 'darwin':
            size = size.upper()
        path_to_file = oos.write_big_data(size, 'data.txt')
        if func == 'multipart_upload':
            mpu = oos.s3multipartupload(
                oscsdk,
                bucket_name,
                'data.txt',
                path_to_file)
            # abort all multipart uploads for this bucket (optional, for starting over)
            mpu.abort_all()
            # create new multipart upload
            mpu_id = mpu.create()
            connector.list_multipart_uploads(Bucket=bucket_name)
            # upload parts
            logger.debug("beginning of the multipart_upload")
            start_upload = datetime.now()
            parts = mpu.upload(mpu_id)
            upload_duration = (datetime.now() - start_upload).total_seconds()
            upload_done = True
            result["multipart_upload" + service + size] = upload_duration
            logger.debug("end of the multipart_upload")
            logger.debug("beginning of the list_parts")
            start_list_parts = datetime.now()
            response = connector.list_parts(Bucket=bucket_name, Key='data.txt', UploadId=mpu_id)
            list_parts_duration = (datetime.now() - start_list_parts).total_seconds()
            result["list_parts" + service + size] = list_parts_duration
            logger.debug("end of the list_parts")
            assert len(response['Parts']) >= 1
            logger.debug("beginning of the list_multipart_uploads")
            start_list_multipart_uploads = datetime.now()
            multiple_upload = connector.list_multipart_uploads(Bucket=bucket_name)
            list_list_multipart_uploads = (datetime.now() - start_list_multipart_uploads).total_seconds()
            result["list_multipart_uploads" + service + size] = list_list_multipart_uploads
            logger.debug("end of the list_multipart_uploads")
            assert multiple_upload['Uploads'][0]['Key'] == 'data.txt'
            mpu.complete(mpu_id, parts)
        elif func == 'put_object':
            data = open(path_to_file, "r")
            logger.debug("beginning of the put_object")
            start_put_object = datetime.now()
            connector.put_object(Bucket=bucket_name, Key='data.txt', Body=str.encode(data.read()))
            put_object_duration = (datetime.now() - start_put_object).total_seconds()
            upload_done = True
            result["put_object" + service + size] = put_object_duration
            logger.debug("end of the put_object")
            logger.debug("beginning of the get_object")
            start_get_object = datetime.now()
            connector.get_object(Bucket=bucket_name, Key='data.txt')
            get_object_duration = (datetime.now() - start_get_object).total_seconds()
            result["get_object" + service + size] = get_object_duration
            logger.debug("end of the get_object")

    except Exception as error:
        log_error(logger, error, "Unexpected error while executing %s".format("bucket_operations"), result)
    finally:
        errors = []
        if os.path.isfile(path_to_file):
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


def perf_objects(oscsdk, logger, queue, args):

    result = {'status': 'OK'}
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='100m', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='500m', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='1g', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='2g', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='5g', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='10g', result=result)
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='100m', result=result)
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='500m', result=result)
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='1g', result=result)
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='2g', result=result)
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='5g', result=result)
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='10g', result=result)
    queue.put(result.copy())
