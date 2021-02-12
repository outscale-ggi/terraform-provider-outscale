from multiprocessing import Process

from qa_test_tools.test_base import OscTestSuite


class Test_access_keys(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'accesskey_limit': 1000}
        super(Test_access_keys, cls).setup_class()

    def test_T5323_parallel_loop(self):

        def exec_job(osc_sdk, nb_retry):
            for _ in range(nb_retry):
                ak = None
                try:
                    ret = osc_sdk.oapi.CreateAccessKey()
                    ak = ret.response.AccessKey.AccessKeyId
                finally:
                    if ak:
                        osc_sdk.oapi.DeleteAccessKey(AccessKeyId=ak)

        nb_worker = 50
        nb_retry = 20

        threads = []

        self.logger.debug("Init process")
        for _ in range(nb_worker):
            thread = Process(target=exec_job,
                             args=(self.a1_r1, nb_retry))
            threads.append(thread)

        self.logger.debug("Start process")
        for thread in threads:
            thread.start()

        self.logger.debug("Wait process...")
        for thread in threads:
            thread.join()
        self.logger.debug("    ...Process end")
        for thread in threads:
            assert thread.exitcode == 0
