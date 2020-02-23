import pytest

from qa_common_tools import constants
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_DeleteKeyPair(OscTestSuite):

    def test_T934_with_valid_keyname(self):
        self.a1_r1.fcu.CreateKeyPair(KeyName='tiuyttrgt')
        self.a1_r1.fcu.DeleteKeyPair(KeyName='tiuyttrgt')

    def test_T937_with_used_keypair(self):
        self.a1_r1.fcu.CreateKeyPair(KeyName='key')
        img = self.a1_r1._config.region.get_info(constants.CENTOS7)
        ret = self.a1_r1.fcu.RunInstances(ImageId=img, KeyName='key', MinCount=1, MaxCount=1)
        instanceid = ret.response.instancesSet[0].instanceId
        wait_instances_state(self.conns[0], [instanceid], state='running', threshold=60, wait_time=5)
        ret = self.a1_r1.fcu.DeleteKeyPair(KeyName='key')
        ret = self.a1_r1.fcu.StopInstances(InstanceId=instanceid, force=True)
        wait_instances_state(self.conns[0], [instanceid], state='stopped', threshold=60, wait_time=5)
        self.a1_r1.fcu.TerminateInstances(InstanceId=instanceid)

    def test_T933_without_keyname(self):
        try:
            self.a1_r1.fcu.DeleteKeyPair()
            pytest.fail("Deleting key pair without key name should not have succeeded")
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: Name')

    def test_T935_with_not_existing_keyname(self):
        try:
            self.a1_r1.fcu.DeleteKeyPair(KeyName='tydyt')
            pytest.fail("Deleting key pair with invalid key name should not have succeeded")
        except OscApiException as error:
            assert_error(error, 400, 'InvalidKeyPair.NotFound', 'The key pair does not exist: tydyt')

    def test_T936_with_keyname_from_another_account(self):
        try:
            self.a2_r1.fcu.CreateKeyPair(KeyName='tiuyttrgt')
            self.a1_r1.fcu.DeleteKeyPair(KeyName='tiuyttrgt')
        except OscApiException as error:
            assert_error(error, 400, 'InvalidKeyPair.NotFound', 'The key pair does not exist: tiuyttrgt')
        finally:
            self.a2_r1.fcu.DeleteKeyPair(KeyName='tiuyttrgt')
