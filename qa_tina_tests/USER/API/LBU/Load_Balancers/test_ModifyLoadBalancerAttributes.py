

from string import ascii_lowercase

import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_ModifyLoadBalancerAttributes(OscTestSuite):

    @classmethod
    def setup_class(cls):
        # cls.vpc_id = None
        cls.lb_name = None
        try:
            super(Test_ModifyLoadBalancerAttributes, cls).setup_class()
            lb_name = id_generator(prefix='lbu-')
            create_load_balancer(cls.a1_r1, lb_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                 availability_zones=[cls.a1_r1.config.region.az_name])
            cls.lb_name = lb_name
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.lb_name:
                delete_lbu(cls.a1_r1, cls.lb_name)
        finally:
            super(Test_ModifyLoadBalancerAttributes, cls).teardown_class()

    def test_T2991_wrong_AccessLog_param(self):
        try:
            access_log = {'Enabled': True, 'S3BucketName': 'test', 'S3BucketPrefix': 'prefix', 'EmitInterval': 5}
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerAttributes={'AccessLog': access_log}, LoadBalancerName=self.lb_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidConfigurationRequest', None)

    def test_T2992_missing_required_param(self):
        try:
            access_log = {'S3BucketName': 'test', 'S3BucketPrefix': 'prefix', 'EmitInterval': 5}
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerAttributes={'AccessLog': access_log}, LoadBalancerName=self.lb_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidConfigurationRequest', 'Bucket is unavailable for access log')

    def test_T4529_without_name(self):
        try:
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerAttributes={'ConnectionSettings': {'IdleTimeout': 123}})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerName')

    def test_T4530_without_attribute(self):
        try:
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerAttributes')

    @pytest.mark.region_storageservice
    def test_T5136_valid_access_log(self):
        ret_create_bucket = None
        bucket_name = id_generator(prefix="bucket", chars=ascii_lowercase)
        try:
            ret_create_bucket = self.a1_r1.storageservice.create_bucket(Bucket=bucket_name)

            access_log = {'S3BucketName': bucket_name, 'S3BucketPrefix': 'prefix', 'EmitInterval': 5, 'Enabled': True}
            self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerAttributes={'AccessLog': access_log}, LoadBalancerName=self.lb_name)
            ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
            assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AccessLog.Enabled == 'true'
            assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AccessLog.S3BucketName == bucket_name
            assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AccessLog.S3BucketPrefix == 'prefix'
            assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AccessLog.EmitInterval == '5'
        except OscApiException as error:
            raise error
        finally:
            ret = self.a1_r1.oos.list_objects(Bucket=bucket_name)
            if 'Contents' in list(ret.keys()):
                for j in ret['Contents']:
                    self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=j['Key'])
            if ret_create_bucket:
                self.a1_r1.storageservice.delete_bucket(Bucket=bucket_name)

    # def test_T0003_with_access_log(self):
    #    self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
    #                                                LoadBalancerAttributes={'AccessLog': {'Enabled': False, 'EmitInterval': 12}})
    #    ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
    #    self.logger.debug(ret.response.display())
    #    #assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Key == 'SecuredCookies'

    def test_T4531_with_additional_attribute(self):
        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'AdditionalAttributes': [{'Key': 'SecuredCookies', 'Value': True}]})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Key == 'SecuredCookies'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Value == 'true'

    def test_T4532_with_connection_draining(self):
        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'ConnectionDraining': {'Enabled': True, 'Timeout': 456}})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Enabled == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Timeout == '456'

    def test_T4533_with_connection_setting(self):
        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'ConnectionSettings': {'IdleTimeout': 456}})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionSettings.IdleTimeout == '456'

    def test_T4534_multiple_modify(self):
        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'ConnectionSettings': {'IdleTimeout': 123}})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionSettings.IdleTimeout == '123'

        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'ConnectionDraining': {'Enabled': True, 'Timeout': 123}})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Enabled == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Timeout == '123'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionSettings.IdleTimeout == '123'

        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'AdditionalAttributes': [{'Key': 'SecuredCookies', 'Value': True}]})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Key == 'SecuredCookies'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Value == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Enabled == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Timeout == '123'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionSettings.IdleTimeout == '123'

        # Modify AccessLog + check

        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'ConnectionSettings': {'IdleTimeout': 456}})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Key == 'SecuredCookies'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Value == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Enabled == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Timeout == '123'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionSettings.IdleTimeout == '456'

        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'ConnectionDraining': {'Enabled': True, 'Timeout': 456}})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Key == 'SecuredCookies'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Value == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Enabled == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Timeout == '456'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionSettings.IdleTimeout == '456'

        self.a1_r1.lbu.ModifyLoadBalancerAttributes(LoadBalancerName=self.lb_name,
                                                    LoadBalancerAttributes={'AdditionalAttributes': [{'Key': 'SecuredCookies', 'Value': False}]})
        ret = self.a1_r1.lbu.DescribeLoadBalancerAttributes(LoadBalancerName=self.lb_name)
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Key == 'SecuredCookies'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.AdditionalAttributes[0].Value == 'false'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Enabled == 'true'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionDraining.Timeout == '456'
        assert ret.response.DescribeLoadBalancerAttributesResult.LoadBalancerAttributes.ConnectionSettings.IdleTimeout == '456'
