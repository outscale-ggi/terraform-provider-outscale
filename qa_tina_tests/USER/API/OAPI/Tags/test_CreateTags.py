from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException


class Test_CreateTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_CreateTags, cls).setup_class()
        cls.is_id = None

    @classmethod
    def teardown_class(cls):
        super(Test_CreateTags, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateTags, self).setup_method(method)
        self.is_id = None
        try:
            self.is_id = self.a1_r1.oapi.CreateInternetService().response.InternetService.InternetServiceId
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
        finally:
            super(Test_CreateTags, self).teardown_method(method)

    def test_T2361_valid_params(self):
        self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': 'value'}])

    def test_T2362_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': 'value'}], DryRun=True)
        assert_dry_run(ret)

    def test_T2504_without_key(self):
        try:
            self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4069')

    def test_T2505_with_empty_key(self):
        try:
            self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Key': '', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameterValue', '4069')

    def test_T2506_without_value(self):
        self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key'}])

    def test_T2507_with_empty_value(self):
        self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': ''}])

    def test_T2508_no_key_dry_run(self):
        ret = self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Value': 'value'}], DryRun=True)
        assert_dry_run(ret)

    def test_T2509_invalid_params(self):
        try:
            self.a1_r1.oapi.CreateTags(ResourceIds=[self.is_id], Tags=[{'Key': 'key', 'Value': 'value', 'toto': 'toto'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'InvalidParameter', '3001')

    def test_T2510_without_resource_id(self):
        try:
            self.a1_r1.oapi.CreateTags(ResourceIds=[], Tags=[{'Key': 'key', 'Value': 'value'}])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_oapi_error(err, 400, 'MissingParameter', '7000')
