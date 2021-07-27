import pytest

from qa_test_tools.account_tools import create_account, delete_account
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.constants import TWO_REGIONS_NEEDED


class Test_copy_account(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_copy_account, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_copy_account, cls).teardown_class()

    def test_T3571_valid_params(self):
        if not hasattr(self, 'a1_r2'):
            pytest.skip(TWO_REGIONS_NEEDED)
        pid = None
        ret_copy = None
        try:
            pid = create_account(self.a1_r2)
            ret_copy = self.a1_r2.xsub.copy_account(pid=pid, destination_region=self.a1_r1.config.region.name, profile=None)
        except Exception as error:  # for debug purposes
            raise error
        finally:
            if pid:
                delete_account(self.a1_r2, pid)
            if ret_copy:
                delete_account(self.a1_r1, pid)
