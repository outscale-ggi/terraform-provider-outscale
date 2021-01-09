from datetime import datetime
from string import ascii_lowercase

import numpy

from qa_test_tools import misc
from qa_tina_tests.USER.PERF.perf_common import log_error


def perf_storage(oscsdk, service, logger, queue, args):
    result = {'status': 'OK'}
    connector = getattr(oscsdk, service)
    try:
        retry = 20
        bucket_names = []
        obj_names = []
        durations = []
        for num in range(retry):
            logger.debug("%s : %d/%d", "create_bucket", num + 1, retry)
            tmp = misc.id_generator(prefix="bucket", size=10, chars=ascii_lowercase)
            start_desc = datetime.now()
            connector.create_bucket(Bucket=tmp)
            durations.append((datetime.now() - start_desc).total_seconds())
            bucket_names.append(tmp)
        result["create_bucket"+service] = numpy.array(durations).mean()
        logger.debug("%s : %d/%d", "list_buckets", num + 1, retry)
        start_desc = datetime.now()
        connector.list_buckets()
        result["list_buckets"+service] = (datetime.now() - start_desc).total_seconds()
        durations = []
        for num in range(retry):
            logger.debug("%s : %d/%d", "put_object", num + 1, retry)
            tmp = misc.id_generator(prefix="obj_", chars=ascii_lowercase)
            data = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            start_desc = datetime.now()
            connector.put_object(Bucket=bucket_names[0], Key=tmp, Body=str.encode(data))
            durations.append((datetime.now() - start_desc).total_seconds())
            obj_names.append(tmp)
        result["put_object"+service] = numpy.array(durations).mean()
        logger.debug("%s : %d/%d", "list_objects", num + 1, retry)
        start_desc = datetime.now()
        connector.list_objects(Bucket=bucket_names[0])
        result["list_objects"+service] = (datetime.now() - start_desc).total_seconds()
    except Exception as error:
        log_error(logger, error, "Unexpected error while executing %s".format("bucket_operations"), result)
    finally:
        if obj_names:
            durations = []
            for obj_name in obj_names:
                logger.debug("%s : %s", "delete_object", obj_name)
                start_desc = datetime.now()
                connector.delete_object(Bucket=bucket_names[0], Key=obj_name)
                durations.append((datetime.now() - start_desc).total_seconds())
            result["delete_object"+service] = numpy.array(durations).mean()
        if bucket_names:
            num = 0
            durations = []
            for bucket_name in bucket_names:
                logger.debug("%s : %d/%d", "delete_bucket", num + 1, retry)
                start_desc = datetime.now()
                try:
                    connector.delete_bucket(Bucket=bucket_name)
                    durations.append((datetime.now() - start_desc).total_seconds())
                    num += 1
                except Exception as error:
                    log_error(logger, error, "Unexpected error while executing %s".format("delete_bucket"), result)
            result["delete_bucket"+service] = numpy.array(durations).mean()

    queue.put(result.copy())
