from qa_tina_tests.USER.PERF.perf_objects import func_objects


def perf_multipart_upload_marine(oscsdk, logger, queue, args):
    result = {'status': 'OK'}
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='30k', result=result)
    queue.put(result.copy())
