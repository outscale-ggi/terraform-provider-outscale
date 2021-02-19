from qa_tina_tests.USER.PERF.perf_objects import func_objects


def put_object_marine(oscsdk, logger, queue, args):
    result = {'status': 'OK'}
    print(args)
    func_objects(oscsdk=oscsdk, func='put_object', service='oos', logger=logger, size='10k', result=result)
    queue.put(result.copy())
