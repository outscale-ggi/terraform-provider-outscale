

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST

NUM_INST = 2


class Test_DescribeInstances(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeInstances, cls).setup_class()
        cls.instance_info_a1 = None
        try:
            cls.instance_info_a1 = create_instances(cls.a1_r1, nb=NUM_INST)
        except Exception as error:
            try:
                cls.teardown_class()
            except:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.instance_info_a1:
                delete_instances(cls.a1_r1, cls.instance_info_a1)
        finally:
            super(Test_DescribeInstances, cls).teardown_class()

    def test_T3224_with_other_account(self):
        ret = self.a2_r1.fcu.DescribeInstances()
        assert not ret.response.reservationSet, 'Unexpected non-empty result'

    def test_T3225_without_param(self):
        ret = self.a1_r1.fcu.DescribeInstances()
        id_list = []
        for res in ret.response.reservationSet:
            for inst in res.instancesSet:
                id_list.append(inst.instanceId)
                assert inst.instanceId in self.instance_info_a1[INSTANCE_ID_LIST]
        assert len(set(id_list)) == NUM_INST

    def test_T3226_with_other_account_with_param(self):
        try:
            self.a2_r1.fcu.DescribeInstances(InstanceId=[self.instance_info_a1[INSTANCE_ID_LIST][0]])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound',
                         'The Instance ID does not exist: {}, for account: {}'.format(self.instance_info_a1[INSTANCE_ID_LIST][0],
                                                                                      self.a2_r1.config.account.account_id))

    def test_T3273_with_other_account_with_filter(self):
        ret = self.a2_r1.fcu.DescribeInstances(Filter=[{'Name': 'instance-id', 'Value': [self.instance_info_a1[INSTANCE_ID_LIST][0]]}])
        assert not ret.response.reservationSet

    def test_T5146_with_existing_and_not_existing_instances(self):
        try:
            self.a1_r1.fcu.DescribeInstances(InstanceId=[self.instance_info_a1[INSTANCE_ID_LIST][0], 'i-1b5240d7'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidInstanceID.NotFound',
                         'The Instance ID does not exist: i-1b5240d7, for account: {}'.format(self.a1_r1.config.account.account_id))
