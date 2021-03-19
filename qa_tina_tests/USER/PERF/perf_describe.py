from datetime import datetime

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tests.USER.PERF.perf_common import log_error


def test_func(func, logger, key, result):
    try:
        retry = 20
        for num in range(retry):
            try:
                logger.debug("%s : %d/%d", str(func), num+1, retry)
                start_desc = datetime.now()
                func(max_retry=0)
                result[key] = (datetime.now() - start_desc).total_seconds()
                break
            except OscApiException as error:
                if error.status_code != 503:
                    raise error
    except Exception as error:
        log_error(logger, error, "Unexpected error while executing {}".format(str(func)), result)


def perf_describe(oscsdk, logger, queue, args):

    print(args)
    result = {'status': 'OK'}

    test_func(oscsdk.fcu.DescribeInstances, logger, 'desc_inst', result)
    test_func(oscsdk.fcu.DescribeVolumes, logger, 'desc_vol', result)
    test_func(oscsdk.fcu.DescribeImages, logger, 'desc_img', result)
    test_func(oscsdk.fcu.DescribeSnapshots, logger, 'desc_snap', result)

    queue.put(result.copy())
