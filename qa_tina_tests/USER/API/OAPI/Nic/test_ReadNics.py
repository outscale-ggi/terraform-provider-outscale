
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tools.tools.tina import create_tools, delete_tools, wait_tools, info_keys
from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic


class Test_ReadNics(Nic):

    @classmethod
    def setup_class(cls):
        cls.nic_ids = []
        cls.vm_info = None
        cls.vm_ids = []
        super(Test_ReadNics, cls).setup_class()
        cls.nic_link_id = None
        try:
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_ids.append(ret.NicId)
            cls.a1_r1.oapi.LinkPrivateIps(NicId=cls.nic_ids[0], PrivateIps=['10.0.1.35', '10.0.1.36', '10.0.1.37', '10.0.1.38'])
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id1).response.Nic
            cls.nic_ids.append(ret.NicId)
            cls.a1_r1.oapi.LinkPrivateIps(NicId=cls.nic_ids[1], PrivateIps=['10.0.1.135'])
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id2).response.Nic
            cls.nic_ids.append(ret.NicId)
            cls.vm_info = create_tools.create_instances(cls.a1_r1, subnet_id=cls.subnet_id1, sg_id_list=[cls.firewall_id1],
                                                        state='running', inst_type='c4.large')
            cls.vm_ids = cls.vm_info[info_keys.INSTANCE_ID_LIST]
            cls.nic_link_id = cls.a1_r1.oapi.LinkNic(DeviceNumber=1, VmId=cls.vm_ids[0], NicId=cls.nic_ids[0]).response.LinkNicId
            ret = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet_id2).response.Nic
            cls.nic_ids.append(ret.NicId)
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            for i in range(len(cls.nic_ids)):
                nic_id = cls.nic_ids[i]
                if i == 0:
                    cls.a1_r1.fcu.DetachNetworkInterface(AttachmentId=cls.nic_link_id)
                    wait_tools.wait_network_interfaces_state(osc_sdk=cls.a1_r1, network_interface_id_list=[nic_id], state='available')
                cls.a1_r1.oapi.DeleteNic(NicId=nic_id)
            if cls.vm_info:
                delete_tools.delete_instances(cls.a1_r1, cls.vm_info)
        except OscApiException as err:
            raise err
        finally:
            super(Test_ReadNics, cls).teardown_class()

    def test_T2679_empty_filters(self):
        ret = self.a1_r1.oapi.ReadNics()
        # TODO use verify response
        ret.check_response()

    def test_T2680_filters_nic_id1(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'NicIds': [self.nic_ids[0]]})
        # TODO use verify response
        ret.check_response()

    def test_T2681_filters_nic_ids_1_and_2(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'NicIds': [self.nic_ids[0], self.nic_ids[2]]}).response.Nics
        assert len(ret) == 2

    def test_T2684_filters_subnet_id(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'SubnetIds': [self.subnet_id2]}).response.Nics
        assert len(ret) == 2
        nic = ret[0]
        assert nic.NicId == self.nic_ids[2]
        assert nic.SubnetId == self.subnet_id2

    def test_T2685_filters_private_ip(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'PrivateIpsPrivateIps': ['10.0.1.38']}).response.Nics
        assert len(ret) == 1
        nic = ret[0]
        assert nic.NicId == self.nic_ids[0]

    def test_T2686_filters_vm_ids(self):
        ret = self.a1_r1.oapi.ReadNics(Filters={'LinkNicVmIds': [self.vm_ids[0]]}).response.Nics
        assert len(ret) == 2  # The 'attached/ing' and the 'detaching/ed'
        for nic in ret:
            link = nic.LinkNic
            if link.State in ['attached', 'attaching'] and nic.Description == "":
                assert link.LinkNicId == self.nic_link_id
                assert link.DeviceNumber == 1
            if link.State == ('detaching' or 'detached')and nic.Description == "":
                assert nic.NicId != [0]
                assert link.LinkNicId != self.nic_link_id
            assert link.VmId == self.vm_ids[0]

    @pytest.mark.tag_sec_confidentiality
    def test_T3403_with_other_account(self):
        ret = self.a2_r1.oapi.ReadNics()
        assert not ret.response.Nics

    @pytest.mark.tag_sec_confidentiality
    def test_T3410_with_other_account_inexistante_nic(self):
        ret = self.a2_r1.oapi.ReadNics(Filters={'NicIds': [self.nic_ids[0], self.nic_ids[2]]}).response.Nics
        assert not ret

    def test_T5975_with_tag_filter(self):
        misc.execute_tag_tests(self.a1_r1, 'Nic', self.nic_ids, 'oapi.ReadNics', 'Nics.NicId')
