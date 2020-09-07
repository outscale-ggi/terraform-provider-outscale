from datetime import datetime
from string import ascii_lowercase

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tests.USER.PERF.perf_common import log_error


def perf_oos(oscsdk, logger, queue, args):
    result = {'status': 'OK'}
    try:
        retry = 20
        bucket_names = []
        obj_names = []
        for num in range(retry):
            logger.debug("%s : %d/%d", "create_bucket", num + 1, retry)
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            start_desc = datetime.now()
            oscsdk.oos.create_bucket(Bucket=tmp)
            result["create_bucket"] = (datetime.now() - start_desc).total_seconds()
            bucket_names.append(tmp)
        for num in range(retry):
            logger.debug("%s : %d/%d", "list_buckets", num + 1, retry)
            start_desc = datetime.now()
            oscsdk.oos.list_buckets()
            result["list_buckets"] = (datetime.now() - start_desc).total_seconds()
        for bucket_name in bucket_names:
            tmp = misc.id_generator(prefix="obj_", chars=ascii_lowercase)
            data = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            oscsdk.oos.put_object(Bucket=bucket_names[0], Key=tmp, Body=str.encode(data))
            obj_names.append(tmp)
        for num in range(retry):
            logger.debug("%s : %d/%d", "list_objects", num + 1, retry)
            start_desc = datetime.now()
            oscsdk.oos.list_objects(Bucket=bucket_names[0])
            result["list_objects"] = (datetime.now() - start_desc).total_seconds()
    except Exception as error:
        log_error(logger, error, "Unexpected error while executing %s".format("bucket_operations"), result)
    finally:
        if obj_names:
            for obj_name in obj_names:
                oscsdk.oos.delete_object(Bucket=bucket_names[0], Key=obj_name)
        if bucket_names:
            num = 0
            for bucket_name in bucket_names:
                logger.debug("%s : %d/%d", "delete_bucket", num + 1, retry)
                start_desc = datetime.now()
                oscsdk.oos.delete_bucket(Bucket=bucket_name)
                result["delete_bucket"] = (datetime.now() - start_desc).total_seconds()
                num += 1

    queue.put(result.copy())
