import pytest
from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_GetKeyRotationStatus(Kms):

    @classmethod
    def setup_class(cls):
        super(Test_GetKeyRotationStatus, cls).setup_class()
        try:
            pass
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_GetKeyRotationStatus, cls).teardown_class()
