from qa_tina_tests.USER.PERF.perf_objects import func_objects


def perf_objects_oos(oscsdk, logger, queue, args):
    result = {'status': 'OK'}
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='2000m', result=result)
