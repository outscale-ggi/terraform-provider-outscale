
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


NUM_INST = 1


class Test_DescribeInstanceAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeInstanceAttribute, cls).setup_class()
        cls.instance_info_a1 = None
        cls.vpc_info_1 = None
        try:
            cls.instance_info_a1 = create_instances(cls.a1_r1, nb=NUM_INST)
            cls.vpc_info_1 = create_vpc(cls.a1_r1, cidr_prefix="10.1", nb_instance=1)
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
            if cls.instance_info_a1:
                delete_instances(cls.a1_r1, cls.instance_info_a1)
            if cls.vpc_info_1:
                delete_vpc(cls.a1_r1, cls.vpc_info_1)
        finally:
            super(Test_DescribeInstanceAttribute, cls).teardown_class()

    def test_T3376_with_other_account_with_param(self):
        try:
            self.a2_r1.fcu.DescribeInstanceAttribute(Attribute='instanceType', InstanceId=self.instance_info_a1[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound',
                         'The instance IDs do not exist: {}'.format(self.instance_info_a1[INSTANCE_ID_LIST][0]))

    def test_T3377_without_instance_id(self):
        try:
            self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='instanceType')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidInstanceID.Malformed", "Invalid ID received: . Expected format: i-")
            known_error('TINA-6100', 'Incorrect error message')

    def test_T3454_without_attribute_parameter(self):
        try:
            self.a1_r1.fcu.DescribeInstanceAttribute(InstanceId=self.instance_info_a1[INSTANCE_ID_LIST][0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter: Attribute')

    def test_T2988_valid_param_sourceDestCheck(self):
        ret = self.a1_r1.fcu.DescribeInstanceAttribute(Attribute='sourceDestCheck',
                                                       InstanceId=self.vpc_info_1['subnets'][0]['instance_set'][0]['instanceId'])
        assert ret.response.sourceDestCheck.value or not ret.response.sourceDestCheck.value

    def test_T5538_from_another_account_without_instance_id(self):
        try:
            self.a2_r1.fcu.DescribeInstanceAttribute(Attribute='instanceType')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidInstanceID.Malformed", "Invalid ID received: . Expected format: i-")
            known_error('TINA-6100', 'Incorrect error message')
