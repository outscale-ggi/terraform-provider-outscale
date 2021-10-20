from datetime import datetime
# from threading import current_thread

from qa_tina_tests.USER.PERF.perf_common import log_error


NUM_IP_ALLOCATIONS = 5


def perf_ip_allocation(oscsdk, logger, queue, args):

    #thread_name = current_thread().name
    print(args)

    result = {'status': 'OK'}

    ip_allocation_ids = []
    if result['status'] != "KO":
        try:
            logger.debug("Create ip allocations")
            start_create = datetime.now()
            for _ in range(NUM_IP_ALLOCATIONS):
                ip_allocation_ids.append(oscsdk.fcu.AllocateAddress().response.publicIp)
            time_ip_allocation = (datetime.now() - start_create).total_seconds()
            result['ip_allocation_create'] = time_ip_allocation
            logger.debug("Ip allocations time: %.2f", time_ip_allocation)
        except Exception as error:
            log_error(logger, error, "Unexpected error while allocating ips", result)


    if ip_allocation_ids:
        release_error = None
        try:
            logger.debug("Delete ip allocations")
            start_delete = datetime.now()
            for pub_ip in ip_allocation_ids:
                try:
                    oscsdk.fcu.ReleaseAddress(PublicIp=pub_ip)
                except Exception as error:
                    release_error = error
            time_ip_release = (datetime.now() - start_delete).total_seconds()
            result['ip_allocation_delete'] = time_ip_release
        except Exception as error:
            log_error(logger, error, "Unexpected error while releasing ips", result)
        if release_error:
            raise release_error

    queue.put(result.copy())
