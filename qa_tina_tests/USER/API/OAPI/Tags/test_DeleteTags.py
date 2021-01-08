import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_test_tools.test_base import OscTestSuite


class Test_DeleteTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteTags, cls).setup_class()
        cls.is_id = None
        cls.is_id2 = None

    @classmethod
    def teardown_class(cls):
        super(Test_DeleteTags, cls).teardown_class()

    def setup_method(self, method):
        super(Test_DeleteTags, self).setup_method(method)
        self.is_id = None
        self.is_id2 = None
        try:
            self.is_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            self.is_id2 = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
            self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': 'value'}])
            self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id2], Tags=[{'Key': 'toto', 'Value': 'value'}])
        except:
            try:
                self.teardown_method(method)
            except:
                pass
            raise

    def teardown_method(self, method):
        try:
            if self.is_id:
                self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.is_id)
            if self.is_id2:
                self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=self.is_id2)
        finally:
            super(Test_DeleteTags, self).teardown_method(method)

    def test_T2363_valid_params(self):
        self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': 'value'}])

    def test_T2364_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': 'value'}], DryRun=True)
        assert_dry_run(ret)

    def test_T2511_missing_resource_id(self):
        try:
            self.a1_r1.oapi.DeleteTags(ResourceIds=[], Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T2512_resource_id_string_type(self):
        try:
            self.a1_r1.oapi.DeleteTags(ResourceIds=['toto'], Tags=[{'Key': 'key', 'Value': 'value'}])
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4025')

    def test_T2513_incorrect_type_resource_id(self):
        try:
            self.a1_r1.oapi.DeleteTags(ResourceIds=[True], Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4110')

    def test_T2514_missing_tags(self):
        try:
            self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')

    def test_T2515_incorrect_type_tags(self):
        try:
            self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags={'Key': 'key', 'Value': 'value'})
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4110')

    def test_T2516_missing_tags_key(self):
        try:
            self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags=[{'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4069')

    def test_T2517_empty_tags_key(self):
        try:
            self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags=[{'Key': '', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4069')

    def test_T2518_single_resource_single_tags(self):
        self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags=[{'Key': 'toto', 'Value': 'value'}])

    def test_T2519_single_resource_multi_tags(self):
        self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags=[{'Key': 'toto', 'Value': 'values'}, {'Key': 'titi', 'Value': 'value'}])

    def test_T2520_multi_resource_single_tags(self):
        self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id, self.is_id2], Tags=[{'Key': 'toto', 'Value': 'value'}])

    def test_T2521_multi_resource_multi_tags(self):
        self.a1_r1.oapi.DeleteTags(ResourceIds=[self.is_id, self.is_id2], Tags=[{'Key': 'toto', 'Value': 'value'}, {'Key': 'titi', 'Value': 'titi'}])

    @pytest.mark.tag_sec_confidentiality
    def test_T3531_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5044')
