import pytest

from qa_tina_tests.USER.API.KMS.kms import Kms


@pytest.mark.region_kms
class Test_UpdateAlias(Kms):
    pass
