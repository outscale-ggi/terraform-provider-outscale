from qa_common_tools.test_base import OscTestSuite
import pytest


@pytest.mark.region_kms
class Test_kms(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_kms, cls).setup_class()
        try:
            cls.account_id = cls.a1_r1.config.account.account_id
            cls.account2_id = cls.a2_r1.config.account.account_id
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_kms, cls).teardown_class()

    def teardown_method(self, method):
        try:
            self.a1_r1.intel.kms.key.delete(owner=self.account_id, force=True)
            self.a1_r1.intel.kms.key.delete(owner=self.account2_id, force=True)
        except:
            pass
        finally:
            OscTestSuite.teardown_method(self, method)

    def verify_result(self, ret, **kwargs):
        assert ('bypass_policy' in kwargs and kwargs['bypass_policy'] == ret.bypass_policy) or ret.bypass_policy is False
        assert ('creation_date' in kwargs and kwargs['creation_date'] is not None and kwargs['creation_date'] == ret.creation_date) or ret.creation_date
        assert not ret.deletion_date
        assert not ret.description
        assert ret.enabled
        assert len(ret.id) == 12 and ret.id.startswith('cmk-')  # TODO use regex
        assert ('is_default' in kwargs and kwargs['is_default'] == ret.is_default) or ret.is_default is False
        assert ('manager' in kwargs and kwargs['manager'] == ret.manager) or ret.manager == 'CUSTOMER'
        assert ret.origin == 'OKMS'
        assert ret.owner == self.a1_r1.config.account.account_id
        assert ('policy' in kwargs and kwargs['policy'] == ret.policy) or ret.policy == 'default'
        assert ('rotation' in kwargs and kwargs['rotation'] == ret.rotation) or ret.rotation is True
        assert ('rotation_date' in kwargs and kwargs['rotation_date'] is not None and kwargs['rotation_date'] == ret.rotation_date) or ret.rotation_date
        assert ret.state == 'enabled'
        assert ret.usage == 'ENCRYPT_DECRYPT'

    def test_T3190_create_key(self):
        ret = self.a1_r1.intel.kms.key.create(owner=self.account_id).response.result
        self.verify_result(ret)

    def test_T3191_create_default_key(self):
        ret = self.a1_r1.intel.kms.key.create(owner=self.account_id, default=True).response.result
        self.verify_result(ret,
                           bypass_policy=None,
                           creation_date=None,
                           is_default=True,
                           manager=None,
                           policy=None,
                           rotation=None,
                           rotation_date=None)

    def test_T3192_create_default_key_twice(self):
        ret = self.a1_r1.intel.kms.key.create(owner=self.account_id, default=True).response.result
        self.verify_result(ret,
                           bypass_policy=None,
                           creation_date=None,
                           is_default=True,
                           manager=None,
                           policy=None,
                           rotation=None,
                           rotation_date=None)
        ret = self.a1_r1.intel.kms.key.create(owner=self.account_id, default=True).response.result
        self.verify_result(ret,
                           bypass_policy=None,
                           creation_date=None,
                           is_default=True,
                           manager=None,
                           policy=None,
                           rotation=None,
                           rotation_date=None)

    def test_T3193_delete_key(self):
        ret = self.a1_r1.intel.kms.key.create(owner=self.account_id).response.result
        ret = self.a1_r1.intel.kms.key.delete(owner=self.account_id, key_id=ret.id)

    def test_T3194_find_key(self):
        self.a1_r1.intel.kms.key.create(owner=self.account_id, default=True)
        key_id_1 = self.a1_r1.intel.kms.key.create(owner=self.account_id).response.result.id
        self.a1_r1.intel.kms.key.create(owner=self.account_id)
        self.a1_r1.intel.kms.key.schedule_deletion(owner=self.account_id, key_id=key_id_1, pending_window_in_days=7)
        self.a1_r1.intel.kms.key.create(owner=self.account2_id)
        ret = self.a1_r1.intel.kms.key.find(owner=self.account_id)
        assert ret.response.result
        ret = self.a1_r1.intel.kms.key.find(owner=self.account_id, limit=1)
        assert ret.response.result.count == 1
        ret = self.a1_r1.intel.kms.key.find(owner=self.account_id, id=key_id_1)
        assert len(ret.response.result) == 1
        assert ret.response.result[0].id == key_id_1
        ret = self.a1_r1.intel.kms.key.find(owner=self.account_id, offset=1, limit=1)
        assert ret.response.result.count == 1
        ret = self.a1_r1.intel.kms.key.find(owner=self.account_id, state='enabled')
        for res in ret.response.result:
            assert res.enabled is True
        ret = self.a1_r1.intel.kms.key.find(owner=self.account_id, orders=[('id', 'ASC')])
        assert ret.response.result

    def test_T3195_schedule_deletion(self):

        key_id = self.a1_r1.intel.kms.key.create(owner=self.account_id).response.result.id
        self.a1_r1.intel.kms.key.schedule_deletion(owner=self.account_id, key_id=key_id, pending_window_in_days=7)
        ret = self.a1_r1.intel.kms.key.find(id=key_id).response.result
        assert len(ret) == 1 and ret[0].deletion_date

    def test_T3196_cancel_deletion(self):
        key_id = self.a1_r1.intel.kms.key.create(owner=self.account_id).response.result.id
        self.a1_r1.intel.kms.key.schedule_deletion(owner=self.account_id, key_id=key_id, pending_window_in_days=7)
        ret = self.a1_r1.intel.kms.key.find(id=key_id).response.result
        assert len(ret) == 1 and ret[0].deletion_date
        ret = self.a1_r1.intel.kms.key.cancel_deletion(owner=self.account_id, key_id=key_id)
        ret = self.a1_r1.intel.kms.key.find(id=key_id).response.result
        assert len(ret) == 1 and not ret[0].deletion_date

    def test_T3197_gc(self):
        key_id = self.a1_r1.intel.kms.key.create(owner=self.account_id).response.result.id
        self.a1_r1.intel.kms.key.schedule_deletion(owner=self.account_id, key_id=key_id, pending_window_in_days=7)
        ret = self.a1_r1.intel.kms.key.find(id=key_id).response.result
        assert len(ret) == 1 and ret[0].deletion_date
        # this test could be done if settings could be changed
        ret = self.a1_r1.intel.kms.key.gc()
        ret = self.a1_r1.intel.kms.key.find(id=key_id).response.result
        assert len(ret) == 1 and ret[0].deletion_date

    def test_T3737_after_user_sync(self):
        self.a1_r1.intel.kms.user.sync(accounts=[self.account2_id])
        ret = self.a2_r1.kms.ListKeys()
        assert len(ret.response.Keys) == 1
