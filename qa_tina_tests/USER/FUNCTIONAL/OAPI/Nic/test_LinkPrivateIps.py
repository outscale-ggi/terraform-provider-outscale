from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import oapi, info_keys
from qa_test_tools.exceptions.test_exceptions import OscTestException

class Test_LinkPrivateIps(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.net_info = None
        cls.net_id = None
        cls.subnet = None
        cls.nic = None
        cls.private_ip = None
        super(Test_LinkPrivateIps, cls).setup_class()
        try:
            cls.net_info = oapi.create_Net(cls.a1_r1, igw=False)
            cls.net_id = cls.net_info[info_keys.NET_ID]
            cls.subnet = cls.net_info[info_keys.SUBNETS][0]
            cls.nic = cls.a1_r1.oapi.CreateNic(SubnetId=cls.subnet[info_keys.SUBNET_ID]).response.Nic
            cls.private_ip = cls.nic.PrivateIps[0].PrivateIp
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.nic:
                cls.a1_r1.oapi.DeleteNic(NicId=cls.nic.NicId)
            if cls.net_info:
                oapi.delete_Net(cls.a1_r1, cls.net_info)
        finally:
            super(Test_LinkPrivateIps, cls).teardown_class()

    def test_6098_allocate_each_private_ip(self):
        errors = {}
        for i in range(4, 255):
            try:
                ip = '10.0.1.{}'.format(i)
                self.a1_r1.oapi.LinkPrivateIps(NicId=self.nic.NicId, PrivateIps=[ip], AllowRelink=True)
                if i > 13:
                    ip = '10.0.1.{}'.format(i - 10)
                    if ip != self.private_ip:
                        self.a1_r1.oapi.UnlinkPrivateIps(NicId=self.nic.NicId, PrivateIps=[ip])
            except Exception as error:
                errors[i] = error
        if errors:
            raise OscTestException('Some errors occurred ({})'.format(len(errors)))
