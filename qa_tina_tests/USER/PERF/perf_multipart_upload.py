from qa_tina_tests.USER.PERF.perf_objects import func_objects


def perf_multipart_upload(oscsdk, logger, queue, args):
    print(args)
    result = {'status': 'OK'}
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='100m', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='500m', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='1g', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='2000m', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='5g', result=result)
    func_objects(oscsdk=oscsdk, func='multipart_upload', service='oos', logger=logger, size='10g', result=result)
    queue.put(result.copy())
