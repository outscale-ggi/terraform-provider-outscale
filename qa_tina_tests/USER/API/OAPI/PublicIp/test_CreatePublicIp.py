# -*- coding:utf-8 -*-
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite


class Test_CreatePublicIp(OscTestSuite):

    def setup_method(self, method):
        super(Test_CreatePublicIp, self).setup_method(method)
        self.ip = None

    def teardown_method(self, method):
        try:
            if self.ip:
                self.a1_r1.oapi.DeletePublicIp(PublicIp=self.ip)
        finally:
            super(Test_CreatePublicIp, self).teardown_method(method)

    def test_T2006_without_param(self):
        ret = self.a1_r1.oapi.CreatePublicIp()
        ret.check_response()
        self.ip = ret.response.PublicIp.PublicIp
        assert hasattr(ret.response.PublicIp, 'PublicIp')
        assert hasattr(ret.response.PublicIp, 'PublicIpId')
        assert ret.response.PublicIp.PublicIpId.startswith('eipalloc')

    def test_T2010_with_invalid_param(self):
        try:
            self.a1_r1.oapi.CreatePublicIp(toto='toto')
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3001')
