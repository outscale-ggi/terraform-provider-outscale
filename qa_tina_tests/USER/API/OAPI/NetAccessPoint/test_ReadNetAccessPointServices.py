from qa_tina_tools.test_base import OscTinaTest

SERVICE_NAMES = ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'osu', 'oos', 'kms']


class Test_ReadNetAccessPointServices(OscTinaTest):

    def test_T3336_empty_filters(self):
        services = self.a1_r1.oapi.ReadNetAccessPointServices().response.Services
        assert len(services) == len(SERVICE_NAMES)
        for service in services:
            assert service.ServiceName.split('.')[3] in SERVICE_NAMES
            assert service.IpRanges
            assert service.ServiceName
            assert service.ServiceId
