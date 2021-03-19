
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import assert_oapi_error
from qa_test_tools.test_base import OscTestSuite


class Test_UpdateImage(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateImage, cls).setup_class()
        cls.image_id = None
        try:
            image_id = cls.a1_r1.config.region.get_info(constants.CENTOS7)
            cls.image_id = cls.a1_r1.oapi.CreateImage(SourceImageId=image_id, SourceRegionName=cls.a1_r1.config.region.name).response.Image.ImageId
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.image_id:
                cls.a1_r1.oapi.DeleteImage(ImageId=cls.image_id)
        finally:
            super(Test_UpdateImage, cls).teardown_class()

    def test_T2331_empty_param(self):
        try:
            self.a1_r1.oapi.UpdateImage()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2332_invalid_image_id(self):
        try:
            permissions = {'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]}}
            self.a1_r1.oapi.UpdateImage(ImageId='tata', PermissionsToLaunch=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2333_unknown_image_id(self):
        try:
            permissions = {'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]}}
            self.a1_r1.oapi.UpdateImage(ImageId='ami-12345678', PermissionsToLaunch=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5023')

    def test_T2334_no_permissions(self):
        try:
            self.a1_r1.oapi.UpdateImage(ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2335_permission_addition_account_ids_valid(self):
        permissions = {'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)

    def test_T2336_permission_addition_many_account_ids_valid(self):
        permissions = {'Additions': {'AccountIds': [self.a1_r1.config.account.account_id, self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)

    def test_T2337_permission_addition_account_ids_invalid(self):
        try:
            permissions = {'Additions': {'AccountIds': ['tata']}}
            self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4105')

    def test_T2338_permission_addition_invalid_global_permissions(self):
        try:
            permissions = {'Additions': {'GlobalPermission': 'tata'}}
            self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T2339_permission_addition_global_permissions(self):
        permissions = {'Additions': {'GlobalPermission': True}}
        self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)

    def test_T2340_permission_addition_accounts_and_global_permissions(self):
        permissions = {'Additions': {'GlobalPermission': True, 'AccountIds': [self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)

    def test_T2341_permission_addition_and_removal_account_ids_invalid(self):
        try:
            permissions = {'Additions': {'AccountIds': [self.a2_r1.config.account.account_id]},
                           'Removals': {'AccountIds': [self.a2_r1.config.account.account_id]}}
            self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameter', '3002')

    def test_T2342_permission_removal_account_ids_valid(self):
        permissions = {'Removals': {'AccountIds': [self.a2_r1.config.account.account_id]}}
        self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)

    def test_T2343_permission_removal_global_permissions(self):
        permissions = {'Removals': {'GlobalPermission': True}}
        assert self.a1_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)

    @pytest.mark.tag_sec_confidentiality
    def test_T3461_other_account(self):
        permissions = {'Additions': {'AccountIds': [self.a1_r1.config.account.account_id]}}
        try:
            self.a2_r1.oapi.UpdateImage(ImageId=self.image_id, PermissionsToLaunch=permissions)
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', 5023)
