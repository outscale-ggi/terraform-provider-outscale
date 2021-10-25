
import random
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic


class Test_LinkPrivateIps(Nic):

    @classmethod
    def setup_class(cls):
        super(Test_LinkPrivateIps, cls).setup_class()
        cls.nic_id1 = None
        cls.nic_id2 = None
        cls.private_ip1 = None
        cls.private_ip2 = None
        try:
            # subnet 1 has cidr 10.0.1.0/24
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_id1 = ret.NicId
            cls.private_ip1 = ret.PrivateIps[0].PrivateIp
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_id2 = ret.NicId
            cls.private_ip2 = ret.PrivateIps[0].PrivateIp
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.nic_id2:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id2)
            if cls.nic_id1:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic_id1)
        finally:
            super(Test_LinkPrivateIps, cls).teardown_class()

    def find_ip(self):
        while True:
            ip = '10.0.1.{}'.format(random.sample(range(4,254), 1)[0])
            if ip not in [self.private_ip1, self.private_ip2]:
                return ip

    def test_T2662_with_empty_param(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2663_with_empty_nic_id(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2664_with_invalid_nic_id(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2665_with_unknown_nic_id(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId='eni-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2666_with_valid_nic_id_but_missing_other_param(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2667_with_invalid_private_ip(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2668_with_invalid_private_ip2(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=['295.0.1.35'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2669_with_valid_combination(self):
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[self.find_ip()])

    def test_T2670_with_invalid_secondary_ip_count(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, SecondaryPrivateIpCount=-2)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2671_with_too_much_ip(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, SecondaryPrivateIpCount=50000)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'TooManyResources (QuotaExceded)', '10021')

    def test_T2672_with_valid_combination2(self):
        calls = 0
        while calls < 10:
            calls += 1
            try:
                ret = self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, SecondaryPrivateIpCount=2)
                ret.check_response()
                calls = 10
            except OscApiException as error:
                assert_oapi_error(error, 400, 'TooManyResources (QuotaExceded)', '10021')
                assert False, 'Call should not have been failed'

    def test_T2673_with_invalid_combination(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[self.find_ip()], SecondaryPrivateIpCount=2)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2674_with_valid_combination_allow_relink(self):
        ip = self.find_ip()
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id2, PrivateIps=[ip], AllowRelink=True)
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[ip], AllowRelink=True)

    def test_T2675_with_valid_combination2_allow_relink(self):
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, SecondaryPrivateIpCount=2, AllowRelink=True)

    def test_T2676_with_valid_combination_not_allow_relink(self):
        ip = self.find_ip()
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[ip], AllowRelink=True)
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id2, PrivateIps=[ip], AllowRelink=False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')

    def test_T3488_dry_run(self):
        ret = self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[self.find_ip()], DryRun=True)
        assert_dry_run(ret)

    @pytest.mark.tag_sec_confidentiality
    def test_T3489_other_account(self):
        try:
            self.a2_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[self.find_ip()])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5036')

    def test_T6100_primary_ip_same_nic(self):
        self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[self.private_ip1], AllowRelink=True)

    def test_T6101_primary_ip_other_nic(self):
        try:
            self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic_id1, PrivateIps=[self.private_ip2], AllowRelink=True)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4045')
