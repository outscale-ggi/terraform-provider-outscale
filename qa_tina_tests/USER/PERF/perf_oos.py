from qa_tina_tests.USER.PERF.perf_storage import perf_storage


def perf_oos(oscsdk, logger, queue, args):
    return perf_storage(oscsdk=oscsdk, service='oos', logger=logger, queue=queue, args=args)
