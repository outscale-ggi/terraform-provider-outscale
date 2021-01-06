from multiprocessing import Process

from qa_test_tools.test_base import OscTestSuite

class Test_access_keys(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.QUOTAS = {'accesskey_limit': 1000}
        super(Test_access_keys, cls).setup_class()

    def test_T5323_parallel_loop(self):

        def exec_job(osc_sdk, nb_retry):
            for i in range(nb_retry):
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
        for i in range(nb_worker):
            t = Process(target=exec_job,
                        args=(self.a1_r1, nb_retry))
            threads.append(t)

        self.logger.debug("Start process")
        for i in range(len(threads)):
            threads[i].start()

        self.logger.debug("Wait process...")
        for i in range(len(threads)):
            threads[i].join()
        self.logger.debug("    ...Process end")
        for i in range(len(threads)):
            assert threads[i].exitcode == 0
