from qa_tina_tests.USER.PERF.perf_storage import perf_storage


def perf_osu(oscsdk, logger, queue, args):
    return perf_storage(oscsdk=oscsdk, service='osu', logger=logger, queue=queue, args=args)
