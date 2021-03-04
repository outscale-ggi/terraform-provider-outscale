from qa_test_tools.test_base import OscTestSuite


Service_Name = ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'kms', 'oos']


class Test_ReadNetAccessPointServices(OscTestSuite):

    def test_T3336_empty_filters(self):
        services = self.a1_r1.oapi.ReadNetAccessPointServices().response.Services
        assert len(services) == len(Service_Name)
        for service in services:
            assert service.ServiceName.split('.')[3] in Service_Name
            assert service.IpRanges
            assert service.ServiceName
            assert service.ServiceId
