from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.info_keys import SUBNET_ID, SUBNETS
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc


class Test_reserve(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        super(Test_reserve, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, igw=False)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_reserve, cls).teardown_class()

    def test_T3263_private_vpc(self):
        try:
            self.a1_r1.intel.subnet.reserve(subnet_id=self.vpc_info[SUBNETS][0][SUBNET_ID], groups=['SOMEGROUP'])
        except OscApiException as error:
            assert_error(error, 200, 0, 'invalid-vpc - This action cannot be used for private VPCs.')
