#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os

import time
import json
import dateutil.parser as dp

from qa_support_tools.influxdb.influxdb import push_metrics
from qa_support_tools.influxdb.influxdb_config import OscInfluxdbConfig


LOGGING_LEVEL = logging.DEBUG


if __name__ == '__main__':
    logger = logging.getLogger('charge_oos')

    args_p = argparse.ArgumentParser(description="Test oos performances",
                                     formatter_class=argparse.RawTextHelpFormatter)

    args_p.add_argument('-r', '--region', dest='region', action='store',
                        required=True, type=str, help='Selected Outscale region for the test')
    args_p.add_argument('-dir', '--result_dir', dest='result', action='store',
                        required=True, type=str, help='Set result_dir used for the test')
    args_p.add_argument('-job', '--job_name', dest='job_name', action='store',
                        required=False, type=int, help='the job name in jenkins')
    args_p.add_argument('-build', '--build_number', dest='build_number', action='store',
                        required=True, type=str, help='the build number')
    args_p.add_argument('-db', '--data_base', dest='db', action='store',
                        required=False, type=str, help='database name')
    args_p.add_argument('-dr', '--dry_run', dest='dry_run', action='store',
                        required=False, default=True, type=bool, help='set dry run ')

    args = args_p.parse_args()

    logger.info("Push results")
    timestamp = int(time.time())
    if args.result:
        os_walk = os.walk(args.result)
    tests = next(os_walk)[1]
    hosts = next(os_walk)[1]
    for test in tests:
        for host in hosts:
            os_walk = os.walk(args.result+'/{}/{}'.format(test, host))
            workers = next(os_walk)[-1]
            for worker in workers:
                data = {}
                with open(args.result+'/{}/{}/{}'.format(test, host, worker)) as file:
                    jsonData = json.load(file)
                for duration in jsonData:
                    data[test] = duration['duration']
                    parsed_t = dp.parse(duration['date'])
                    t_in_seconds = parsed_t.strftime('%s')
                    if not args.dry_run:
                        push_metrics(args.db, args.graph, {'region': args.region, 'job': args.job_name, 'build':args.build_number,
                                                           'host': host, 'id_worker': worker}, data,
                                     OscInfluxdbConfig.get(), t_in_seconds)
                    print(data)
