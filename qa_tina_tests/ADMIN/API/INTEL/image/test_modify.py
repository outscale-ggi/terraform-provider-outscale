from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import assert_code, known_error
from qa_test_tools.config import config_constants as constants
from qa_tina_tools.test_base import OscTinaTest


class Test_modify(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_modify, cls).setup_class()
        cls.image_id = None
        try:
            image_id = cls.a1_r1.config.region.get_info(constants.CENTOS_LATEST)
            cls.image_id = cls.a1_r1.oapi.CreateImage(SourceImageId=image_id,SourceRegionName=cls.a1_r1.config.region.name).response.Image.ImageId

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.image_id:
                cls.a1_r1.oapi.DeleteImage(ImageId=cls.image_id)
        finally:
            super(Test_modify, cls).teardown_class()

    def test_T5857_with_name(self):
        name = 'toto'
        self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id, name=name)
        ret = self.a1_r1.intel.image.get(id=self.image_id).response
        assert ret.result.name == name

    def test_T5858_with_manifest(self):
        manifest = 'toto'
        self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id, manifest=manifest)
        ret = self.a1_r1.intel.image.get(id=self.image_id).response
        assert ret.result.manifest == manifest

    def test_T5859_with_invalid_name_type(self):
        try:
            name = ['foo']
            self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id, name=name)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_code(error, 200, "invalid-parameter-type - Value of parameter \'Name\' must be of type: str. Received: [\'foo\']")

    def test_T5860_with_invalid_manifest_type(self):
        try:
            manifest = ['foo']
            self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id, manifest=manifest)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_code(error, 200, "invalid-parameter-type - Value of parameter \'Manifest\' must be of type: str. Received: [\'foo\']")

    def test_T5861_with_empty_manifest(self):
        try:
            self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id, manifest="")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_code(error, 200, "missing-parameter")

    def test_T5862_with_name_and_empty_manifest(self):
        name = "toto"
        self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id, name=name, manifest="")
        ret = self.a1_r1.intel.image.get(id=self.image_id).response
        assert ret.result.manifest is None
        assert ret.result.name == name
        resp = self.a1_r1.oapi.ReadImages(Filters={'ImageIds': [self.image_id]}).response
        if not hasattr(resp, 'Images'):
            known_error('TINA-6687', 'ReadImages no more working well')
        assert False, 'Remove known error'
        assert resp.Images[0].ImageName == name
        assert resp.Images[0].FileLocation is None

    def test_T5866_with_name_and_manifest(self):
        name = 'name_example'
        manifest = 'manifest_example'
        self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id, name=name, manifest=manifest)
        ret = self.a1_r1.intel.image.get(id=self.image_id).response
        assert ret.result.name == name
        assert ret.result.manifest == manifest

    def test_T5867_with_required_params(self):
        try:
            self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id, image=self.image_id)
            assert False, 'Remove known error'
        except OscApiException as error:
            if error.message == "missing-parameter - Insufficient parameters provided out of: Description, manifest," \
                                " name, setAsPublic, users. Expected at least: 1":
                known_error('TINA-6707', 'intel.image.modify Issues')
            assert False, 'Remove known error'

    def test_T5856_without_owner(self):
        try:
            self.a1_r1.intel.image.modify(image=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_code(error, 200, "missing-parameter - Parameter cannot be empty: Owner")

    def test_T5917_without_image_id(self):
        try:
            self.a1_r1.intel.image.modify(owner=self.a1_r1.config.account.account_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_code(error, 200, "missing-parameter - Parameter cannot be empty: ImageID")

    def test_T5915_from_another_account(self):
        try:
            self.a1_r1.intel.image.modify(owner=self.a2_r1.config.account.account_id, image=self.image_id, name='toto')
            known_error('TINA-6707', 'intel.image.modify Issues')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error'
            assert_error(error, 200, 0, '')
