from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite


class Test_AllocateAddress(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_AllocateAddress, cls).setup_class()
        cls.conn = cls.a1_r1

    @classmethod
    def teardown_class(cls):
        super(Test_AllocateAddress, cls).teardown_class()

    def test_T288_without_param(self):
        ip = None
        try:
            ret = self.conn.fcu.AllocateAddress()
            ip = ret.response.publicIp
            assert ret.response.domain == 'standard'
        finally:
            if ip:
                self.conn.fcu.ReleaseAddress(PublicIp=ip)

    def test_T289_with_standard_domain(self):
        ip = None
        try:
            ret = self.conn.fcu.AllocateAddress(Domain='standard')
            ip = ret.response.publicIp
            assert ret.response.domain == 'standard'
        finally:
            if ip:
                self.conn.fcu.ReleaseAddress(PublicIp=ip)

    def test_T290_with_vpc_domain(self):
        ip = None
        try:
            ret = self.conn.fcu.AllocateAddress(Domain='vpc')
            ip = ret.response.publicIp
            assert ret.response.domain == 'vpc'
        finally:
            if ip:
                self.conn.fcu.ReleaseAddress(PublicIp=ip)

    def test_T291_with_invalid_domain(self):
        ip = None
        try:
            ret = self.conn.fcu.AllocateAddress(Domain='toto')
            ip = ret.response.publicIp
            assert False, "Incorrect param domain value should have caused error."
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == "InvalidParameterValue"
        finally:
            if ip:
                self.conn.fcu.ReleaseAddress(PublicIp=ip)

    def test_T292_with_invalid_param(self):
        ip = None
        try:
            ret = self.conn.fcu.AllocateAddress(toto='toto')
            ip = ret.response.publicIp
            assert ret.response.domain == 'standard'
        finally:
            if ip:
                self.conn.fcu.ReleaseAddress(PublicIp=ip)
