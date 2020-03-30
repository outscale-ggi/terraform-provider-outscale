#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import argparse
import importlib
import inspect
import logging
from multiprocessing import Queue
import sys
from threading import Thread
import time

from qa_test_tools.config import OscConfig
from qa_support_tools.influxdb.influxdb import push_metrics
from qa_support_tools.influxdb.influxdb_config import OscInfluxdbConfig
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_instances, cleanup_volumes, cleanup_security_groups, cleanup_keypairs
from qa_sdks.osc_sdk import OscSdk


LOGGING_LEVEL = logging.DEBUG

PERF_TYPES = ['perf_snapshot', 'perf_describe', 'perf_volume', 'perf_sg', 'perf_inst', 'perf_inst_windows', 'perf_simple_snapshot']

if __name__ == '__main__':

    logger = logging.getLogger('perf')

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter('[%(asctime)s] ' +
                          '[%(levelname)8s]' +
                          '[%(threadName)s] ' +
                          '[%(module)s.%(funcName)s():%(lineno)d]: ' +
                          '%(message)s', '%m/%d/%Y %H:%M:%S'))

    logger.setLevel(level=LOGGING_LEVEL)
    logger.addHandler(log_handler)

    logger.propagate = False

    logging.getLogger('tools').addHandler(log_handler)
    logging.getLogger('tools').setLevel(level=LOGGING_LEVEL)

    args_p = argparse.ArgumentParser(description="Test platform performances",
                                     formatter_class=argparse.RawTextHelpFormatter)

    args_p.add_argument('-r', '--region-az', dest='az', action='store',
                        required=True, type=str,
                        help='Selected Outscale region AZ for the test')
    args_p.add_argument('-a', '--account', dest='account', action='store',
                        required=True, type=str, help='Set account used for the test')
    args_p.add_argument('-n', '--nb-worker', dest='nb_worker', action='store',
                        required=True, type=int, help='Number of simultaneous test')
    args_p.add_argument('-o', '--omi', dest='omi', action='store',
                        required=False, type=str, help='OMI for the test')
    args_p.add_argument('-i', '--instance-type', dest='inst_type', action='store',
                        required=False, type=str, help='Instance type for the test')
    args_p.add_argument('-g', '--graph', dest='graph', action='store',
                        required=False, type=str, help='send data to graph')
    args_p.add_argument('-c', '--cleanup', dest='cleanup', action='store',
                        required=False, type=bool, default=False, help='clean all resources')
    args_p.add_argument('-t', '--type', dest='perf_type', action='store',
                        required=True, type=str, help='performance test type')
    args_p.add_argument('-vt', '--volume_type', dest='volume_type', action='store',
                        required=False, type=str, default='standard', help='volume type')
    args_p.add_argument('-vs', '--volume_size', dest='volume_size', action='store',
                        required=False, type=int, default=50, help='volume type')
    args_p.add_argument('-db', '--data_base', dest='db', action='store',
                        required=False, type=str, help='database name')

    args = args_p.parse_args()

    if args.perf_type not in PERF_TYPES:
        logger.info("incorrect perf test type, should be in " + str(PERF_TYPES))
        exit(1)

    oscsdk = OscSdk(config=OscConfig.get(az_name=args.az, account_name=args.account))

    if args.cleanup:
        logger.info("Clean all remaining resources")
        cleanup_instances(oscsdk, args.nb_worker)
        cleanup_volumes(oscsdk)
        cleanup_security_groups(oscsdk)
        cleanup_keypairs(oscsdk)
        logger.info("Stop cleanup")

    QUEUE = Queue()
    threads = []
    final_status = 0

    module = importlib.import_module(args.perf_type, '.')
    methods = inspect.getmembers(module, inspect.isfunction)
    for method in methods:
        if method[0] == args.perf_type:
            break
    if method[0] != args.perf_type:
        logger.info("method {} could not be found".format(args.perf_type))
        exit(1)
    logger.info("Start workers")
    for i in range(args.nb_worker):
        t = Thread(name="{}-{}".format(args.perf_type, i),
                   target=method[1],
                   args=[oscsdk, logger, QUEUE, args])
        threads.append(t)
        t.start()

    logger.info("Wait workers")
    for i in range(len(threads)):
        threads[i].join()
    time.sleep(2)

    logger.info("Get results")
    timestamp = int(time.time())
    i = 0
    while not QUEUE.empty():
        i += 1
        res = QUEUE.get()
        import pprint
        pprint.pprint(res)
        if res['status'] != 'OK':
            final_status += 1
        if args.graph and args.db:
            data = {}
            logger.debug("execution time")
            for key, value in list(res.items()):
                if key == "status":
                    continue
                data[str(key)] = int(value * 1000)
            push_metrics(args.db, args.graph, {'region': args.az[:-1], 'az': args.az, 'id_worker': i}, data, OscInfluxdbConfig.get(), timestamp)
            logger.debug(res)
    if i != len(threads):
        logger.error('Missing result !!!')
        final_status += 1
    sys.exit(final_status)
