import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_test_tools.account_tools import create_account, delete_account


class Test_get_account(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_get_account, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_get_account, cls).teardown_class()

    def test_T558_no_param(self):
        try:
            self.a1_r1.xsub.get_account()
            pytest.fail("Call get_account without parameter should not have succeeded.")
        except OscApiException as error:
            assert error.status_code == 200
            assert error.error_code == 'missing-parameter'

    def test_T559_with_incorrect_param(self):
        try:
            self.a1_r1.xsub.get_account(toto='titi')
            pytest.fail("Call get_account with incorrect parameter should not have succeeded.")
        except OscApiException as error:
            assert error.status_code == 200
            assert error.error_code == 'missing-parameter'

    def test_T560_with_invalid_param(self):
        try:
            self.a1_r1.xsub.get_account(pid='azertyuiop')
            pytest.fail("Call get_account with invalid parameter should not have succeeded.")
        except OscApiException as error:
            assert error.status_code == 200
            assert error.error_code == 'NoSuchAccount'

    def test_T566_with_non_existing_account(self):
        try:
            self.a1_r1.xsub.get_account(pid='12345678')
            pytest.fail("Call get_account with non existing account should not have succeeded.")
        except OscApiException as error:
            assert error.status_code == 200
            assert error.error_code == 'NoSuchAccount'

    def test_T561_with_enabled_account(self):
        pid = None
        try:
            pid = create_account(self.a1_r1)
            ret = self.a1_r1.xsub.get_account(pid=pid)
            assert ret.response.result.account.username == pid
            assert ret.response.result.account.status.identauth == 'ACTIVE'
            assert ret.response.result.account.status.intel == 'enabled'
            assert hasattr(ret.response.result.account, 'creator') and ret.response.result.account.creator is not None
        finally:
            if pid:
                delete_account(self.a1_r1, pid)

    def test_T562_with_disabled_account(self):
        pid = None
        try:
            pid = create_account(self.a1_r1)
            self.a1_r1.xsub.disable_account(pid=pid)
            ret = self.a1_r1.xsub.get_account(pid=pid)
            assert ret.response.result.account.username == pid
            assert ret.response.result.account.status.identauth == 'INACTIVE'
            assert ret.response.result.account.status.intel == 'disabled'
        finally:
            if pid:
                delete_account(self.a1_r1, pid)

    def test_T563_with_frozen_account(self):
        pid = None
        try:
            pid = create_account(self.a1_r1)
            self.a1_r1.xsub.freeze_account(pid=pid)
            ret = self.a1_r1.xsub.get_account(pid=pid)
            assert ret.response.result.account.username == pid
            assert ret.response.result.account.status.identauth == 'FROZEN'
            assert ret.response.result.account.status.intel == 'freeze'
        finally:
            if pid:
                delete_account(self.a1_r1, pid)

    def test_T564_with_restricted_account(self):
        pid = None
        try:
            pid = create_account(self.a1_r1)
            self.a1_r1.xsub.restrict_account(pid=pid)
            ret = self.a1_r1.xsub.get_account(pid=pid)
            assert ret.response.result.account.username == pid
            assert ret.response.result.account.status.identauth == 'RESTRICTED'
            assert ret.response.result.account.status.intel == 'enabled'
        finally:
            if pid:
                delete_account(self.a1_r1, pid)

    def test_T565_with_terminated_account(self):
        pid = None
        try:
            pid = create_account(self.a1_r1)
            self.a1_r1.xsub.terminate_account(pid=pid)
            try:
                self.a1_r1.xsub.get_account(pid=pid)
                pytest.fail("Should not have been able to get details of terminated account.")
            except OscApiException as error:
                assert error.status_code == 200
                assert error.error_code == 'AccountTerminated'
        finally:
            if pid:
                delete_account(self.a1_r1, pid, terminate=False)

    def test_T4739_with_ak(self):
        pid = None
        try:
            pid = create_account(self.a1_r1)
            ret = self.a1_r1.intel.accesskey.find_by_user(owner=pid)
            keys = ret.response.result[0]
            self.a1_r1.xsub.restrict_account(pid=pid)
            ret = self.a1_r1.xsub.get_account(ak=keys.name)
            assert ret.response.result.account.username == pid
        finally:
            if pid:
                delete_account(self.a1_r1, pid)