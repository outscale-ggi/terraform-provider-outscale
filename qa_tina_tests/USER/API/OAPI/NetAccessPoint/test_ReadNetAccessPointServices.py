from qa_tina_tools.test_base import OscTinaTest

SERVICE_NAMES = {'default': ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'osu', 'oos', 'kms'],
                 'in-west-1': ['fcu', 'lbu', 'eim', 'icu', 'directlink', 'api', 'oos', 'kms']}


class Test_ReadNetAccessPointServices(OscTinaTest):

    def test_T3336_empty_filters(self):
        reg_name = self.a1_r1.config.region.name
        services = self.a1_r1.oapi.ReadNetAccessPointServices().response.Services
        expected_services = SERVICE_NAMES[reg_name] if reg_name in SERVICE_NAMES else SERVICE_NAMES['default']
        assert len(services) == len(expected_services)
        for service in services:
            assert service.ServiceName.split('.')[-1] in expected_services
            assert service.IpRanges
            assert service.ServiceName
            assert service.ServiceId
