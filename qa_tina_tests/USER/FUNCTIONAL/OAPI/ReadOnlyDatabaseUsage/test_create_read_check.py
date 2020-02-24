from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.delete_tools import terminate_instances
from qa_common_tools.config import config_constants as constants


class Test_create_read_check(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_read_check, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_create_read_check, cls).teardown_class()

    def test_T4433_check_resource_oapi_read(self):
        vmids = []
        try:
            for _ in range(10):
                ret_inst = self.a1_r1.oapi.CreateVms(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7)).response.Vms
                vmids.extend([vm.VmId for vm in ret_inst])
                ret_read = self.a1_r1.oapi.ReadVms(Filters={'VmIds': vmids}).response.Vms
                assert sorted(vmids) == sorted([vm.VmId for vm in ret_read])
        except Exception as error:
            raise error
        finally:
            if vmids:
                terminate_instances(self.a1_r1, vmids)

    def test_T4465_check_resource_fcu_read(self):
        vmids = []
        try:
            for _ in range(10):
                ret_inst = self.a1_r1.fcu.RunInstances(ImageId=self.a1_r1.config.region.get_info(constants.CENTOS7),
                                                       MinCount=1, MaxCount=1).response.instancesSet
                vmids.extend([vm.instanceId for vm in ret_inst])
                ret_read = self.a1_r1.fcu.DescribeInstances(InstanceId=vmids).response
                inst_set = list(set().union(*[r.instancesSet for r in ret_read.reservationSet]))
                assert sorted(vmids) == sorted([inst.instanceId for inst in inst_set])
        except Exception as error:
            raise error
        finally:
            if vmids:
                terminate_instances(self.a1_r1, vmids)
