# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring

import string

import pytest
import time

from qa_sdk_common.config import DefaultAccount, DefaultRegion
from qa_sdk_pub.osc_api import AuthMethod
from qa_sdk_pub.osc_api import DefaultPubConfig
from qa_sdk_pub.osc_api.osc_icu_api import OscIcuApi
from qa_test_tools.account_tools import delete_account, create_account
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite


@pytest.mark.region_cloudtrace
class Test_NoSecretInLogs(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.ASQUOTAS = {'COUNT_ACCOUNT_CREATED_ACCOUNTS': 1}
        super(Test_NoSecretInLogs, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_NoSecretInLogs, cls).teardown_class()

    @pytest.mark.tag_sec_confidentiality
    def test_T4320_check_no_password_in_UpdateAccount_logs(self):
        password = id_generator(size=20)
        ret = self.a1_r1.icu.UpdateAccount(Password=password)
        self.a1_r1.config.account.password = password
        self.logger.debug(ret.response.display())
        time.sleep(15)
        # TODO: filter by request_id
        ret = self.a1_r1.oapi.ReadApiLogs()
        self.logger.debug(ret.response.display())
        # TODO: check

    @pytest.mark.tag_sec_confidentiality
    def test_T4321_check_no_password_in_CreateAccount_logs(self):
        account_info = None
        password = id_generator(size=20)
        account_param = {'City': 'Saint_Cloud', 'CompanyName': 'Outscale', 'Country': 'France',
                         'CustomerId': id_generator(size=8, chars=string.digits),
                         'Email': id_generator(prefix='qa+test_') + '@outscale.com', 'FirstName': 'Test_user', 'LastName': 'Test_Last_name',
                         'Password': password, 'ZipCode': '92210'}
        try:
            account_info = self.a1_r1.icu.CreateAccount(**account_param)
            self.logger.debug(account_info.response.display())
            time.sleep(15)
            # TODO: filter by request_id
            ret = self.a1_r1.oapi.ReadApiLogs()
            self.logger.debug(ret.response.display())
            # TODO: check
        finally:
            if account_info:
                delete_account(self.a1_r1, account_info.response.Account.AccountPid)

    @pytest.mark.tag_sec_confidentiality
    def test_T4322_check_no_password_in_ResetAccountPassword_logs(self):
        pid = None
        try:
            email = id_generator(prefix='qa+test_') + '@outscale.com'
            password = id_generator(size=20)
            pid = create_account(self.a1_r1, account_info={'email_address': email, 'password': password})
            self.a1_r1.icu.SendResetPasswordEmail(Email=email)
            rettoken = self.a1_r1.identauth.IdauthPasswordToken.createAccountPasswordToken(accountEmail=email, account_id=pid)
            config = DefaultPubConfig(account=DefaultAccount(login=email, password=password), region=DefaultRegion(name=self.a1_r1.config.region.name))
            icu = OscIcuApi(service='icu', config=config)
            new_password = id_generator(size=20)
            icu.ResetAccountPassword(auth=AuthMethod.Empty, Token=rettoken.response.passwordToken, Password=new_password)
            time.sleep(15)
            # TODO: filter by request_id
            ret = self.a1_r1.oapi.ReadApiLogs()
            self.logger.debug(ret.response.display())
            # TODO: check
        finally:
            if pid:
                delete_account(self.a1_r1, pid)

    @pytest.mark.region_synchro_osu
    @pytest.mark.region_osu
    @pytest.mark.tag_sec_confidentiality
    def test_T4323_check_no_sk_in_CreateSnapshotExportTask_logs(self):
        #ret = self.a1_r1.fcu.CreateSnapshotExportTask()
        #self.logger.debug(ret.response.display())
        time.sleep(15)
        # TODO: filter by request_id
        ret = self.a1_r1.oapi.ReadApiLogs()
        self.logger.debug(ret.response.display())
        # TODO: check
        assert False, "Not Implemented"

    @pytest.mark.region_synchro_osu
    @pytest.mark.region_osu
    @pytest.mark.tag_sec_confidentiality
    def test_T4324_check_no_sk_in_CreateImageExportTask_logs(self):
        #ret = self.a1_r1.fcu.CreateImageExportTask()
        #self.logger.debug(ret.response.display())
        time.sleep(15)
        # TODO: filter by request_id
        ret = self.a1_r1.oapi.ReadApiLogs()
        self.logger.debug(ret.response.display())
        # TODO: check
        assert False, "Not Implemented"

    @pytest.mark.tag_sec_confidentiality
    def test_T4325_check_no_password_in_icu_logs_with_password_authent(self):
        ret = self.a1_r1.icu.ListAccessKeys(auth=AuthMethod.LoginPassword)
        self.logger.debug(ret.response.display())
        time.sleep(15)
        # TODO: filter by request_id
        ret = self.a1_r1.oapi.ReadApiLogs()
        self.logger.debug(ret.response.display())
        # TODO: check
