from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import stop_instances, terminate_instances, delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST


class Test_DescribeInstanceStatus(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeInstanceStatus, cls).setup_class()
        cls.inst_info_1 = None
        cls.inst_info_2 = None
        cls.inst_id_running = None
        cls.inst1_id_running = None
        cls.inst2_id_stopped = None
        cls.inst3_id_running = None
        # cls.inst4_id_other_az = None
        try:
            # create 4 instances
            cls.inst_info_1 = create_instances(cls.a1_r1, nb=5)
            # get instance ID
            cls.inst_id_running = cls.inst_info_1[INSTANCE_ID_LIST][0]
            cls.inst1_id_running = cls.inst_info_1[INSTANCE_ID_LIST][1]
            cls.inst2_id_stopped = cls.inst_info_1[INSTANCE_ID_LIST][2]
            cls.inst3_id_running = cls.inst_info_1[INSTANCE_ID_LIST][3]
            cls.inst4_id_terminated = cls.inst_info_1[INSTANCE_ID_LIST][4]
            stop_instances(cls.a1_r1, [cls.inst2_id_stopped])
            terminate_instances(cls.a1_r1, [cls.inst4_id_terminated])
            cls.inst_info_2 = create_instances(cls.a2_r1)
            cls.inst_account2 = cls.inst_info_2[INSTANCE_ID_LIST][0]
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info_1:
                delete_instances(cls.a1_r1, cls.inst_info_1)
            if cls.inst_info_2:
                delete_instances(cls.a2_r1, cls.inst_info_2)
        finally:
            super(Test_DescribeInstanceStatus, cls).teardown_class()

    def test_T906_no_param(self):
        ret = self.a1_r1.fcu.DescribeInstanceStatus()
        # check if all are running
        assert ret.response.instanceStatusSet[0].instanceState.code == '16', "State of the Instance should be running"
        assert ret.response.instanceStatusSet[1].instanceState.code == '16', "State of the Instance should be running"
        assert ret.response.instanceStatusSet[2].instanceState.code == '16', "State of the Instance should be running"
        # check size of the list
        assert len(ret.response.instanceStatusSet) == 3

    def test_T908_include_all_instances_true(self):
        ret = self.a1_r1.fcu.DescribeInstanceStatus(IncludeAllInstances=True)
        assert len(ret.response.instanceStatusSet) == 5

    def test_T907_include_all_instances_false(self):
        ret = self.a1_r1.fcu.DescribeInstanceStatus(IncludeAllInstances=False)
        # check if all are running
        for i in range(3):
            assert ret.response.instanceStatusSet[i].instanceState.code == '16', "State of the Instance should be running"
        # check size of the list
        assert len(ret.response.instanceStatusSet) == 3

    def test_T909_with_instance_id(self):
        self.a1_r1.fcu.DescribeInstanceStatus(InstanceId=[self.inst_id_running])

    def test_T910_with_instance_ids(self):
        ret = self.a1_r1.fcu.DescribeInstanceStatus(InstanceId=[self.inst_id_running, self.inst1_id_running])
        assert len(ret.response.instanceStatusSet) == 2
        assert True if self.inst_id_running in (instanceset.instanceId for instanceset in
                                                ret.response.instanceStatusSet) else False
        assert True if self.inst1_id_running in (instanceset.instanceId for instanceset in
                                                 ret.response.instanceStatusSet) else False

    # def test_T911_filter_availability_zone(self):

    # def test_T912_filter_event_description(self):

    # def test_T913_filter_event_not_after(self):

    # def test_T914_filter_event_code(self):

    # def test_T915_filter_event_not_before(self):

    def test_T916_filter_instance_state_code(self):
        # check running
        code_status = '16'
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[{'Name': 'instance-state-code', 'Value': code_status}])
        assert len(ret.response.instanceStatusSet) == 3
        for i in range(3):
            assert ret.response.instanceStatusSet[i].instanceState.code == code_status
        # check stopped
        code_status = '80'
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[{'Name': 'instance-state-code', 'Value': code_status}], IncludeAllInstances=True)
        assert ret.response.instanceStatusSet and len(ret.response.instanceStatusSet) == 1
        assert ret.response.instanceStatusSet[0].instanceState.code == code_status

    def test_T917_filter_instance_state_name(self):
        # check running
        code_Name = 'running'
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[{'Name': 'instance-state-name', 'Value': code_Name}])
        assert len(ret.response.instanceStatusSet) == 3
        for i in range(3):
            assert ret.response.instanceStatusSet[i].instanceState.name == code_Name
        # check stopped
        code_Name = 'stopped'
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[{'Name': 'instance-state-name', 'Value': code_Name}], IncludeAllInstances=True)
        assert ret.response.instanceStatusSet and len(ret.response.instanceStatusSet) == 1
        assert ret.response.instanceStatusSet[0].instanceState.name == code_Name

    # def test_T918_multiple_filters(self):

    def test_T919_invalid_filter_availability_zone(self):
        filter_dict = {'Name': 'availability-zone', 'Value': 'Some-region-non-existing'}
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        assert ret.response.instanceStatusSet is None

    def test_T1333_invalid_filter_event_code(self):
        filter_dict = {'Name': 'event.code', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        assert ret.response.instanceStatusSet is None

    def test_T1334_invalid_filter_event_description(self):
        filter_dict = {'Name': 'event.description', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        assert ret.response.instanceStatusSet is None

    def test_T1335_invalid_filter_event_not_after(self):
        filter_dict = {'Name': 'event.not-after', 'Value': 'foo'}
        try:
            self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This filter option is not yet implemented: event.not-after')

    def test_T1336_invalid_filter_event_not_before(self):
        filter_dict = {'Name': 'event.not-before', 'Value': 'foo'}
        try:
            self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        except OscApiException as error:
            assert_error(error, 400, 'NotImplemented', 'This filter option is not yet implemented: event.not-before')

    def test_T1337_invalid_filter_instance_state_code(self):
        filter_dict = {'Name': 'instance-state-code', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        assert ret.response.instanceStatusSet is None

    def test_T1338_invalid_filter_instance_state_name(self):
        filter_dict = {'Name': 'instance-state-name', 'Value': 'foo'}
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        assert ret.response.instanceStatusSet is None

    def test_T1339_invalid_filter_instance_multi_value(self):
        # -multi value: instance-state-code=[16,foo]
        filter_dict = {'Name': 'instance-state-code', 'Value': ['foo', '80']}
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict])
        assert ret.response.instanceStatusSet is None

    def test_T1340_invalid_filter_instance_multi_criteria(self):
        # -multi value: instance-state-code=[16,foo]
        # -multi value: instance-state-code=[16,foo]
        filter_dict1 = {'Name': 'instance-state-code', 'Value': '80'}
        filter_dict2 = {'Name': 'instance-state-name', 'Value': '80'}
        ret = self.a1_r1.fcu.DescribeInstanceStatus(Filter=[filter_dict1, filter_dict2])
        assert ret.response.instanceStatusSet is None

    def test_T920_with_invalid_instance_id(self):
        inst_id = 'foo'
        try:
            self.a1_r1.fcu.DescribeInstanceStatus(InstanceId=inst_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.Malformed', 'Invalid ID received: foo. Expected format: i-')

    def test_T1341_with_unknown_instance_id(self):
        inst_id = 'i-12345678'
        try:
            self.a1_r1.fcu.DescribeInstanceStatus(InstanceId=inst_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', None)

    # TODO:not pssoble to create secondary account IN2
    def test_T921_with_instance_id_from_another_account(self):
        try:
            self.a1_r1.fcu.DescribeInstanceStatus(InstanceId=self.inst_account2)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound', None)

    # TODO:ask nicolas
    # def test_T922_with_invalid_filter_and_custom_instance_id(self):
