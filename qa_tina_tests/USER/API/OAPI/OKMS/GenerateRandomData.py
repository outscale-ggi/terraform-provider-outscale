from qa_test_tools.misc import assert_dry_run, assert_oapi_error
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
import pytest
from qa_tina_tests.USER.API.OAPI.OKMS.okms import OKMS


@pytest.mark.region_kms
class Test_GenerateRandomData(OKMS):

    @classmethod
    def setup_class(cls):
        super(Test_GenerateRandomData, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_GenerateRandomData, cls).teardown_class()

#     def test_T5190_valid_params(self):
#         ret = self.a1_r1.oapi.GenerateRandomData(Size=8).response
#         assert ret.Plaintext
# 
#     def test_T5191_incorrect_size(self):
#         try:
#             self.a1_r1.oapi.GenerateRandomData(Size='foobar')
#             assert False, 'Call should not have been successful, invalid key id'
#         except OscApiException as error:
#             assert_oapi_error(error, 400, 'MissingParameter','7000')
# 
#     def test_T5192_missing_size(self):
#         try:
#             self.a1_r1.oapi.GenerateRandomData()
#             assert False, 'Call should not have been successful, no key id'
#         except OscApiException as error:
#             assert_oapi_error(error, 400, 'InvalidParameterValue','2000')
# 
#     def test_T5193_size_too_small(self):
#         try:
#             self.a1_r1.oapi.GenerateRandomData(Size=0)
#             assert False, 'Call should not have been successful, nob too small'
#         except OscApiException as error:
#             assert_oapi_error(error, 400, 'InvalidParameterValue','2000')
# 
#     def test_T5194_size_too_big(self):
#         try:
#             self.a1_r1.oapi.GenerateRandomData(Size=1025)
#             assert False, 'Call should not have been successful, nob too big'
#         except OscApiException as error:
#             assert_oapi_error(error, 400, 'MissingParameter','7000')
# 
#     def test_T5195_dry_run(self):
#         ret = self.a1_r1.oapi.GenerateRandomData(Size=8, DryRun=True)
#         assert_dry_run(ret)
