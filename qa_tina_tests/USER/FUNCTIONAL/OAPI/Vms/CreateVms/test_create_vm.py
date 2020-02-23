import pytest

from osc_common.exceptions import OscApiException
from qa_common_tools.misc import assert_error
from qa_common_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.delete_tools import terminate_instances
from qa_common_tools import constants


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
            assert_error(error, 400, '10001', 'InsufficientCapacity')
        finally:
            if group:
                self.a1_r1.intel.hardware.set_account_bindings(account=self.users[0], groups=[group])
            if vm_id:
                terminate_instances(self.a1_r1, [vm_id])

    def test_T4691_create_twice_with_same_token(self):
        vm_id = None
        vm_id_bis = None
        try:
            vm_id = self.a1_r1.oapi.CreateVms(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                              ClientToken='test_T4691').response.Vms[0].VmId
            try:
                vm_id_bis = self.a1_r1.oapi.CreateVms(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                                      ClientToken='test_T4691').response.Vms[0].VmId
            except OscApiException as error:
                if error.status_code == 400 and error.message == 'DefaultError':
                    known_error("GTW-1144", "Incorrect error message in CreateVms")
                assert False, 'Remove known error code'
                assert_error(error, 400, '', '')
            finally:
                if vm_id_bis:
                    terminate_instances(self.a1_r1, [vm_id_bis])
        finally:
            terminate_instances(self.a1_r1, [vm_id])
