from qa_sdk_common.exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest


class Test_DescribeAvailabilityZones(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeAvailabilityZones, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribeAvailabilityZones, cls).teardown_class()

    def test_T5664_no_param(self):
        ret = self.a1_r1.fcu.DescribeAvailabilityZones()
        ret.check_response()

    def test_T5665_dry_run(self):
        try:
            self.a1_r1.fcu.DescribeAvailabilityZones(DryRun=True)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, 'DryRunOperation', 'Request would have succeeded, but DryRun flag is set.')

    def test_T5666_unknown_param(self):
        try:
            self.a1_r1.fcu.DescribeAvailabilityZones(Foo="bar")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, 'InvalidParameterValue', 'Unexpected parameter Foo')
