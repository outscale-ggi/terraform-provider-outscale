from qa_tina_tests.USER.PERF.perf_inst import perf_inst_exec


def perf_inst_windows(oscsdk, logger, queue, args):
    perf_inst_exec(oscsdk, logger, queue, args, 'windows')
