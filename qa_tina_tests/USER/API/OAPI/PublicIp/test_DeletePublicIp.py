from time import sleep
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, id_generator
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_load_balancers
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_DeletePublicIp(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.ip = None
        cls.ip_id = None
        super(Test_DeletePublicIp, cls).setup_class()

    def setup_method(self, method):
        super(Test_DeletePublicIp, self).setup_method(method)
        self.ip = None
        self.ip_id = None
        try:
            ret = self.a1_r1.oapi.CreatePublicIp().response.PublicIp
            self.ip = ret.PublicIp
            self.ip_id = ret.PublicIpId
        except AssertionError as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.ip:
                self.a1_r1.oapi.DeletePublicIp(PublicIp=self.ip)
        finally:
            super(Test_DeletePublicIp, self).teardown_method(method)

    def test_T2011_without_param(self):
        try:
            self.a1_r1.oapi.DeletePublicIp()
            self.ip = None
            assert False, 'Call should not have been successful, missing parameter'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2012_with_invalid_public_ip(self):
        try:
            self.a1_r1.oapi.DeletePublicIp(PublicIp="123")
            self.ip = None
            assert False, 'Call should not have been successful, invalid public ip'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2928_with_invalid_public_id(self):
        try:
            self.a1_r1.oapi.DeletePublicIp(PublicIpId="tata")
            self.ip = None
            assert False, 'Call should not have been successful, invalid public ip id'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5025')

    def test_T2929_with_unknown_public_id(self):
        try:
            self.a1_r1.oapi.DeletePublicIp(PublicIpId="eipalloc-12345678")
            self.ip = None
            assert False, 'Call should not have been successful, invalid public ip id'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5025')

    def test_T2930_with_public_ip_id_and_public_ip(self):
        try:
            self.a1_r1.oapi.DeletePublicIp(PublicIpId=self.ip_id, PublicIp=self.ip)
            self.ip = None
            assert False, 'Call should not have been successful, invalid public ip id'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T3039_with_incoherent_public_ip_id_and_public_ip(self):
        try:
            self.a1_r1.oapi.DeletePublicIp(PublicIpId=self.ip_id, PublicIp='10.2.5.9')
            self.ip = None
            assert False, 'Call should not have been successful, invalid public ip id'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T3553_with_valid_dry_run(self):
        self.a1_r1.oapi.DeletePublicIp(PublicIp=self.ip, DryRun=True)

    @pytest.mark.tag_sec_confidentiality
    def test_T3554_with_other_user(self):
        try:
            self.a2_r1.oapi.DeletePublicIp(PublicIp=self.ip)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5025')

    def test_T2013_with_valid_public_ip(self):
        self.a1_r1.oapi.DeletePublicIp(PublicIp=self.ip)
        self.ip = None

    def test_T2931_with_valid_public_ip_id(self):
        self.a1_r1.oapi.DeletePublicIp(PublicIpId=self.ip_id)
        self.ip = None

    def test_T5812_del_public_ip_before_public_lbu(self):
        ret_ip = self.a1_r1.oapi.CreatePublicIp()
        public_ip = ret_ip.response.PublicIp.PublicIp
        name = id_generator(prefix='lbu-')
        try:
            self.a1_r1.oapi.CreateLoadBalancer(Listeners=[{'BackendPort': 80, 'LoadBalancerPort': 80, 'LoadBalancerProtocol': 'HTTP'}],
                                                     LoadBalancerName=name,
                                                     PublicIp=public_ip,
                                                     SubregionNames=[self.a1_r1.config.region.az_name])
            try:
                self.a1_r1.oapi.DeletePublicIp(PublicIp=public_ip)
                assert False, "Call should not have been successful"
            except OscApiException as error:
                assert_oapi_error(error, 409, 'ResourceConflict', '9031')
        finally:
            if name:
                try:
                    delete_lbu(self.a1_r1, name)
                    cleanup_load_balancers(self.a1_r1,  filters={'LoadBalancerNames': name}, force=True)
                except:
                    print('Could not delete lbu')
            if public_ip:
                sleep(5)
                self.a1_r1.oapi.DeletePublicIp(PublicIp=public_ip)
