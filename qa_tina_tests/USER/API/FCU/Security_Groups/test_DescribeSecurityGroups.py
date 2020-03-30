# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.delete_tools import delete_security_group
from qa_tina_tools.tools.tina.create_tools import create_security_group
from qa_test_tools.misc import assert_error

NB_SG1 = 1


class Test_DescribeSecurityGroups(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeSecurityGroups, cls).setup_class()
        cls.sg1 = []
        try:
            for _ in range(NB_SG1):
                cls.sg1.append(create_security_group(cls.a1_r1))
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            for sg_id in cls.sg1:
                delete_security_group(cls.a1_r1, sg_id)
        finally:
            super(Test_DescribeSecurityGroups, cls).teardown_class()

    def test_T3184_with_other_account(self):
        try:
            self.a2_r1.fcu.DescribeSecurityGroups(GroupId=self.sg1[0])
            assert False, "Call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidGroup.NotFound", "The security group '{}' does not exist".format(self.sg1[0]))
