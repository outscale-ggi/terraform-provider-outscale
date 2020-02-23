from qa_common_tools.test_base import OscTestSuite


class Test_ReadNetAccessPointServices(OscTestSuite):

    def test_T3336_empty_filters(self):
        self.a1_r1.oapi.ReadNetAccessPointServices().response.Services
