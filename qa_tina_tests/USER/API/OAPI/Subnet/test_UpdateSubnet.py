
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state
from specs import check_oapi_error


class Test_UpdateSubnet(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_UpdateSubnet, cls).setup_class()
        cls.net_id = None
        cls.subnet_id = None
        try:
            cls.net_id = cls.a1_r1.oapi.CreateNet(IpRange='10.0.0.0/16').response.Net.NetId
            cls.subnet_id = cls.a1_r1.oapi.CreateSubnet(IpRange='10.0.0.0/24', NetId=cls.net_id).response.Subnet.SubnetId
            wait_vpcs_state(cls.a1_r1, [cls.net_id], state='available')
        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.subnet_id:
                try:
                    cls.a1_r1.oapi.DeleteSubnet(SubnetId=cls.subnet_id)
                except:
                    print('Could not delete subnet')
            if cls.net_id:
                try:
                    cls.a1_r1.oapi.DeleteNet(NetId=cls.net_id)
                except:
                    print('Could not delete net')
        finally:
            super(Test_UpdateSubnet, cls).teardown_class()

    def test_T3722_no_params(self):
        try:
            self.a1_r1.oapi.UpdateSubnet()
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 7000)

    def test_T3723_missing_parameters(self):
        try:
            self.a1_r1.oapi.UpdateSubnet(SubnetId='subnet-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 7000)
        try:
            self.a1_r1.oapi.UpdateSubnet(MapPublicIpOnLaunch=True)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 7000)

    def test_T3724_invalid_subnet_id(self):
        try:
            self.a1_r1.oapi.UpdateSubnet(MapPublicIpOnLaunch=True, SubnetId='tata')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_oapi_error(error, 4104, invalid='tata', prefixes='subnet-')
        try:
            self.a1_r1.oapi.UpdateSubnet(MapPublicIpOnLaunch=True, SubnetId='subnet-1234567')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(error, 4105, given_id='subnet-1234567')
        try:
            self.a1_r1.oapi.UpdateSubnet(MapPublicIpOnLaunch=True, SubnetId='subnet-123456789')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(error, 4105, given_id='subnet-123456789')

    def test_T3725_unknown_subnet_id(self):
        try:
            self.a1_r1.oapi.UpdateSubnet(MapPublicIpOnLaunch=True, SubnetId='subnet-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            check_oapi_error(err, 5057, id='subnet-12345678')

    def test_T3726_valid_case_map_public_ip_on_launch_true(self):
        ret = self.a1_r1.oapi.UpdateSubnet(MapPublicIpOnLaunch=True, SubnetId=self.subnet_id).response.Subnet
        assert ret.MapPublicIpOnLaunch

    def test_T3727_valid_case_map_public_ip_on_launch_false(self):
        ret = self.a1_r1.oapi.UpdateSubnet(MapPublicIpOnLaunch=False, SubnetId=self.subnet_id).response.Subnet
        assert not ret.MapPublicIpOnLaunch
