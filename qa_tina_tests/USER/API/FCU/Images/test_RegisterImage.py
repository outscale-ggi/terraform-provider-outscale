from osc_common.exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite


class Test_RegisterImage(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RegisterImage, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_RegisterImage, cls).teardown_class()

    def test_T863_invalid_manifest_url(self):
        try:
            self.a1_r1.fcu.RegisterImage(ImageLocation="http://foo")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidURL', "URL does not correspond to any server: http://foo")

    def test_T4575_missing_url_scheme_in_location(self):
        try:
            self.a1_r1.fcu.RegisterImage(ImageLocation="foo")
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidURLFormat', 'Only HTTP or HTTPs URL are accepted: foo')
