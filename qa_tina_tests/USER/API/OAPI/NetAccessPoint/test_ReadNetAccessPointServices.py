from qa_test_tools.test_base import OscTestSuite


<<<<<<< Upstream, based on origin/TINA-2.5.17
Service_Name = ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'kms', 'oos']

<<<<<<< Upstream, based on origin/TINA-2.5.17
=======
SERVICE_NAMES = ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'kms']
>>>>>>> 5459df0 pylint
=======
SERVICE_NAMES = ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'kms']
>>>>>>> 1cf1c00 pylint

class Test_ReadNetAccessPointServices(OscTestSuite):

    def test_T3336_empty_filters(self):
        services = self.a1_r1.oapi.ReadNetAccessPointServices().response.Services
<<<<<<< Upstream, based on origin/TINA-2.5.17
        assert len(services) == len(Service_Name)
        for service in services:
            assert service.ServiceName.split('.')[3] in Service_Name
<<<<<<< Upstream, based on origin/TINA-2.5.17
=======
        assert len(services) == 7
        for service in services:
            assert service.ServiceName.split('.')[3] in SERVICE_NAMES
>>>>>>> 5459df0 pylint
=======
        services = self.a1_r1.oapi.ReadNetAccessPointServices().response.Services
        assert len(services) == 7
        for service in services:
            assert service.ServiceName.split('.')[3] in SERVICE_NAMES
>>>>>>> 1cf1c00 pylint
            assert service.IpRanges
            assert service.ServiceName
            assert service.ServiceId
