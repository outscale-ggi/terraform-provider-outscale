import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import delete_tools
from qa_test_tools.config import config_constants as constants


class Test_create_vm(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_vm, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_vm, cls).teardown_class()

    @pytest.mark.region_admin
    def test_T4503_create_without_hardware_group(self):
        vm_id = None
        group = self.a1_r1.intel.hardware.get_account_bindings(account=self.users[0]).response.result[0]
        self.a1_r1.intel.hardware.set_account_bindings(account=self.users[0], groups=[])
        try:
            vm_id = self.a1_r1.oapi.CreateVms(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7)).response.Vms[0].VmId
            assert False, 'Call should not be successful'
        except OscApiException as error:
            misc.assert_error(error, 400, '10001', 'InsufficientCapacity')
        finally:
            if group:
                self.a1_r1.intel.hardware.set_account_bindings(account=self.users[0], groups=[group])
            if vm_id:
                delete_tools.terminate_instances(self.a1_r1, [vm_id])

    def test_T4691_create_twice_with_same_token(self):
        vm_id = None
        vm_id_bis = None
        token = misc.id_generator('token')
        try:
            vm_id = self.a1_r1.oapi.CreateVms(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                              ClientToken=token).response.Vms[0].VmId
            try:
                vm_id_bis = self.a1_r1.oapi.CreateVms(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                                      ClientToken=token).response.Vms[0].VmId
            except OscApiException as error:
                misc.assert_oapi_error(error, 400, 'InvalidParameterValue', 4119)
            finally:
                if vm_id_bis:
                    delete_tools.terminate_instances(self.a1_r1, [vm_id_bis])
        finally:
            delete_tools.terminate_instances(self.a1_r1, [vm_id])
