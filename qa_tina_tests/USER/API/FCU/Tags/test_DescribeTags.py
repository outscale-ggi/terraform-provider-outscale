
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error, get_export_value


class Test_DescribeTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeTags, cls).setup_class()
        cls.res_id1 = None
        cls.res_id2 = None
        cls.res_id3 = None
        try:
            cls.res_id1 = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='description', GroupName='Test_DescribeTags1').response.groupId
            cls.res_id2 = cls.a1_r1.fcu.CreateInternetGateway().response.internetGateway.internetGatewayId
            cls.res_id3 = cls.a2_r1.fcu.CreateSecurityGroup(GroupDescription='description', GroupName='Test_DescribeTags3').response.groupId
            for i in range(5):
                cls.a1_r1.fcu.CreateTags(ResourceId=[cls.res_id1], Tag=[{'Key': 'key{}'.format(i + 1), 'Value': 'value{}'.format(i + 1)}])
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.res_id1], Tag=[{'Key': 'key6', 'Value': 'value1'}])
            cls.a1_r1.fcu.CreateTags(ResourceId=[cls.res_id2], Tag=[{'Key': 'key1', 'Value': 'value1'}])
            cls.a2_r1.fcu.CreateTags(ResourceId=[cls.res_id3], Tag=[{'Key': 'key1', 'Value': 'value1'}])
        except Exception as error:
            try:
                cls.teardown_class()
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.res_id1:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.res_id1)
            if cls.res_id2:
                cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.res_id2)
            if cls.res_id3:
                cls.a2_r1.fcu.DeleteSecurityGroup(GroupId=cls.res_id3)
        finally:
            super(Test_DescribeTags, cls).teardown_class()

    def test_T5033_without_params(self):
        resp = self.a1_r1.fcu.DescribeTags().response
        assert len(resp.tagSet) == 7
        assert not hasattr(resp, 'nextToken')

    def test_T5034_with_max_result(self):
        resp = self.a1_r1.fcu.DescribeTags(MaxResults=5).response
        if get_export_value('OSC_USE_GATEWAY'):
            assert len(resp.tagSet) == 7
            known_error('GTW-1364', 'MaxResults parameter not used')
        assert len(resp.tagSet) == 5
        assert resp.nextToken

    def test_T5035_with_next_token(self):
        resp = self.a1_r1.fcu.DescribeTags(MaxResults=5).response
        if get_export_value('OSC_USE_GATEWAY'):
            assert len(resp.tagSet) == 7
            known_error('GTW-1364', 'MaxResults parameter not used')
        assert len(resp.tagSet) == 5
        assert resp.nextToken
        resp = self.a1_r1.fcu.DescribeTags(NextToken=resp.nextToken).response
        assert len(resp.tagSet) == 2
        assert not hasattr(resp, 'nextToken')

    def test_T5036_with_filter_resource_id(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [self.res_id1]}]).response.tagSet
        assert len(tags) == 6

    def test_T5037_with_filter_resource_ids(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [self.res_id1, self.res_id2]}]).response.tagSet
        assert len(tags) == 7

    def test_T5038_with_filter_key(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'key', 'Value': ['key1']}]).response.tagSet
        assert len(tags) == 2

    def test_T5039_with_filter_keys(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'key', 'Value': ['key1', 'key2']}]).response.tagSet
        assert len(tags) == 3

    def test_T5040_with_filter_value(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'value', 'Value': ['value1']}]).response.tagSet
        assert len(tags) == 3

    def test_T5041_with_filter_values(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'value', 'Value': ['value1', 'value2']}]).response.tagSet
        assert len(tags) == 4

    def test_T5042_with_filter_key_value(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'key', 'Value': ['key1']},
                                                   {'Name': 'value', 'Value': ['value1']}]).response.tagSet
        assert len(tags) == 2

    def test_T5043_with_filter_resource_type(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-type', 'Value': ['security-group']}]).response.tagSet
        assert len(tags) == 6

    def test_T5044_with_filter_resource_types(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-type', 'Value': ['security-group', 'internet-gateway']}]).response.tagSet
        if get_export_value('OSC_USE_GATEWAY'):
            assert len(tags) == 6
            known_error('GTW-1364', 'Filter is not used')
        assert len(tags) == 7

    def test_T5045_with_incorrect_max_result(self):
        tags = self.a1_r1.fcu.DescribeTags(MaxResult=-1).response.tagSet
        assert len(tags) == 7

    def test_T5046_with_incorrect_max_result_type(self):
        tags = self.a1_r1.fcu.DescribeTags(MaxResult='toto').response.tagSet
        assert len(tags) == 7

    def test_T5047_with_incorrect_next_token(self):
        try:
            self.a1_r1.fcu.DescribeTags(NextToken=23).response.tagSet
        except OscApiException as error:
            assert_error(error, 400, 'InvalidnextToken.Malformed', "Invalid value for 'nextToken': 23")

    def test_T5048_with_incorrect_next_token_type(self):
        try:
            self.a1_r1.fcu.DescribeTags(NextToken=[23]).response.tagSet
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY'):
                assert_error(error, 500, 'InternalError', None)
                known_error('GTW-1364', 'Unexpected internal error')
            assert_error(error, 400, 'InvalidnextToken.Malformed', "Invalid value for 'nextToken': 23")

    def test_T5049_with_empty_filter(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[]).response.tagSet
        assert len(tags) == 7

    def test_T5050_with_incorrect_filter_type(self):
        try:
            self.a1_r1.fcu.DescribeTags(Filter='toto')
            if get_export_value('OSC_USE_GATEWAY'):
                known_error('GTW-1364', 'Incorrect filter should be an error')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if not get_export_value('OSC_USE_GATEWAY'):
                assert_error(error, 500, 'InternalError', None)
                known_error('TINA-5749', 'Unexpected internal error')
                assert_error(error, 400, '', '')

    def test_T5051_with_incorrect_filter_only_name(self):
        try:
            tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'key'}]).response.tagSet
            assert not tags
            if get_export_value('OSC_USE_GATEWAY'):
                assert False, 'Remove known error code'
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY'):
                assert_error(error, 400, 'InvalidParameterValue', None)
                assert not error.message
                known_error('GTW-1364', 'Missing error message')

    def test_T5052_with_incorrect_filter_only_value(self):
        try:
            self.a1_r1.fcu.DescribeTags(Filter=[{'Value': ['value1']}])
            assert False, 'Call should not be successful'
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY'):
                assert_error(error, 400, 'InvalidParameterValue', None)
                assert not error.message
                known_error('GTW-1364', 'Missing error message')
            else:
                assert_error(error, 500, 'InternalError', None)
                known_error('TINA-5749', 'Unexpected internal error')
            assert_error(error, 400, '', '')

    def test_T5053_with_incorrect_filter_content(self):
        try:
            self.a1_r1.fcu.DescribeTags(Filter=[{'toto': 'resource-type', 'tutu': ['security-group']}])
            assert False, 'Call should not be successful'
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY'):
                assert_error(error, 400, 'InvalidParameterValue', None)
                assert not error.message
                known_error('GTW-1364', 'Missing error message')
            else:
                assert_error(error, 500, 'InternalError', None)
                known_error('TINA-5749', 'Unexpected internal error')
            assert_error(error, 400, '', '')

    def test_T5054_with_filter_unknown_resource_type(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-type', 'Value': ['toto']}]).response.tagSet
        assert not tags

    def test_T5055_with_filter_unknown_resource_id(self):
        tags = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': ['i-12345678']}]).response.tagSet
        assert not tags
