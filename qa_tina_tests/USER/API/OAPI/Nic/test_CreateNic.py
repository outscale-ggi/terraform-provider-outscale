# -*- coding:utf-8 -*-
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_oapi_error
from qa_tina_tests.USER.API.OAPI.Nic.Nic import Nic


class Test_CreateNic(Nic):

    @classmethod
    def setup_class(cls):
        cls.nic_id = None
        super(Test_CreateNic, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateNic, cls).teardown_class()

    def setup_method(self, method):
        super(Test_CreateNic, self).setup_method(method)

    def teardown_method(self, method):
        try:
            if self.nic_id:
                self.a1_r1.oapi.DeleteNic(NicId=self.nic_id)
        finally:
            super(Test_CreateNic, self).teardown_method(method)

    def test_T2628_with_empty_param(self):
        try:
            self.a1_r1.oapi.CreateNic()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2629_with_empty_subnet_id(self):
        try:
            self.a1_r1.oapi.CreateNic(SubnetId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'MissingParameter', '7000')

    def test_T2630_with_invalid_subnet_id(self):
        try:
            self.a1_r1.oapi.CreateNic(SubnetId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2631_with_unknown_subnet_id(self):
        try:
            self.a1_r1.oapi.CreateNic(SubnetId='sub-12345678')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2632_with_valid_subnet(self):
        ret = self.a1_r1.oapi.CreateNic(SubnetId=self.subnet_id1).response.Nic
        self.nic_id = ret.NicId
        assert ret.AccountId == self.a1_r1.config.account.account_id
        assert ret.Description == ''
        # assert len(ret.SecurityGroups) == 0
        assert ret.IsSourceDestChecked
        assert ret.MacAddress != ''
        assert ret.NetId == self.vpc_id1
        assert ret.NicId.startswith('eni-'), "Invalid prefix: The nic ID must begin with 'eni-'"
        assert ret.PrivateDnsName is not None
        assert len(ret.PrivateIps) == 1
        assert ret.PrivateIps[0].IsPrimary
        assert ret.PrivateIps[0].PrivateIp is not None
        assert ret.PrivateIps[0].PrivateDnsName is not None
        # assert ret.PrivateIps[0].LinkPublicIp is not None
        # assert ret.LinkPublicIp is not None
        assert ret.State == 'available'
        assert ret.SubnetId == self.subnet_id1
        assert ret.SubregionName == self.a1_r1.config.region.az_name
        assert ret.Tags == []

    def test_T2633_with_description(self):
        ret = self.a1_r1.oapi.CreateNic(Description='description Test', SubnetId=self.subnet_id1).response.Nic
        self.nic_id = ret.NicId
        assert ret.Description == 'description Test'
        assert ret.NicId.startswith('eni-'), "Invalid prefix: The nic ID must begin with 'eni-'"

    def test_T2634_with_firewall_rules_set_ids_empty(self):
        ret = self.a1_r1.oapi.CreateNic(SecurityGroupIds=[], SubnetId=self.subnet_id1).response.Nic
        self.nic_id = ret.NicId
        assert self.nic_id.startswith('eni-'), "Invalid prefix: The nic ID must begin with 'eni-'"

    def test_T2635_with_firewall_rules_set_ids_invalid(self):
        try:
            self.a1_r1.oapi.CreateNic(SecurityGroupIds=['tata'], SubnetId=self.subnet_id1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4104')

    def test_T2636_with_firewall_rules_set_ids_unknown(self):
        try:
            self.a1_r1.oapi.CreateNic(SecurityGroupIds=['sg-12345678'], SubnetId=self.subnet_id1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidResource', '5020')

    def test_T2637_with_private_ips_empty(self):
        ret = self.a1_r1.oapi.CreateNic(PrivateIps=[], SubnetId=self.subnet_id1).response.Nic
        self.nic_id = ret.NicId
        assert len(ret.PrivateIps) == 1
        assert ret.PrivateIps[0].IsPrimary
        assert ret.PrivateIps[0].PrivateIp is not None
        assert ret.PrivateIps[0].PrivateDnsName is not None
        # assert ret.PrivateIps[0].LinkPublicIp is not None

    def test_T2638_with_private_ips_invalid_ip1(self):
        try:
            self.a1_r1.oapi.CreateNic(PrivateIps=[{'IsPrimary': True, 'PrivateIp': 'tata'}],
                                      SubnetId=self.subnet_id1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2639_with_private_ips_invalid_ip2(self):
        try:
            self.a1_r1.oapi.CreateNic(PrivateIps=[{'IsPrimary': True, 'PrivateIp': '296.15.2.25'}],
                                      SubnetId=self.subnet_id1)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_oapi_error(error, 400, 'InvalidParameterValue', '4047')

    def test_T2640_with_private_ips_1_primary(self):
        ret = self.a1_r1.oapi.CreateNic(PrivateIps=[{'IsPrimary': True, 'PrivateIp': '10.0.1.20'}],
                                        SubnetId=self.subnet_id1).response.Nic
        self.nic_id = ret.NicId
        assert len(ret.PrivateIps) == 1
        assert ret.PrivateIps[0].IsPrimary
        assert ret.PrivateIps[0].PrivateIp == '10.0.1.20'
        assert ret.PrivateIps[0].PrivateDnsName.startswith('ip-10-0-1-20')
        # assert ret.PrivateIps[0].LinkPublicIp is not None

    def test_T2641_with_private_ips_1_primary_1_secondary(self):
        ret = self.a1_r1.oapi.CreateNic(PrivateIps=[{'IsPrimary': True, 'PrivateIp': '10.0.1.20'},
                                                    {'IsPrimary': False, 'PrivateIp': '10.0.1.21'}
                                                    ],
                                        SubnetId=self.subnet_id1).response.Nic
        self.nic_id = ret.NicId
        assert len(ret.PrivateIps) == 2
        for ip in ret.PrivateIps:
            if ip.IsPrimary:
                assert ip.PrivateIp == '10.0.1.20'
                assert ip.PrivateDnsName.startswith('ip-10-0-1-20')
            else:
                assert ip.PrivateIp == '10.0.1.21'
                assert ip.PrivateDnsName.startswith('ip-10-0-1-21')
                # assert ip.LinkPublicIp is not None
