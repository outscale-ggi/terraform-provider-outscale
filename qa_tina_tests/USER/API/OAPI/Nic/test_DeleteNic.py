
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error, assert_dry_run
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic


class Test_DeleteNic(Nic):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteNic, cls).setup_class()
        cls.vpc_info = None
        cls.nic_ids = []
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=2)
            for _ in range(2):
                cls.nic_ids.append(cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic.NicId)
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.nic_ids:
                for i in cls.nic_ids:
                    cls.a1_r1.oapi.DeleteNic(NicId=i)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DeleteNic, cls).teardown_class()

    def test_T2642_with_empty_param(self):
        try:
            self.a1_r1.oapi.DeleteNic()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2643_with_empty_nic_id(self):
        try:
            self.a1_r1.oapi.DeleteNic(NicId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2644_with_invalid_nic_id(self):
        try:
            self.a1_r1.oapi.DeleteNic(NicId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2645_with_unknown_nic_id(self):
        try:
            self.a1_r1.oapi.DeleteNic(NicId='eni-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5036')

    @pytest.mark.tag_sec_confidentiality
    def test_T3555_with_other_user(self):
        try:
            self.a2_r1.oapi.DeleteNic(NicId=self.nic_ids[0])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5036')

    def test_T2646_valid_param(self):
        self.a1_r1.oapi.DeleteNic(NicId=self.nic_ids[0])
        self.nic_ids.remove(self.nic_ids[0])

    def test_T2947_valid_param_dry_run(self):
        ret = self.a1_r1.oapi.DeleteNic(NicId=self.nic_ids[0], DryRun=True)
        assert_dry_run(ret)
