import pytest

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import cleanup_tools, wait_tools

NUM_SUBNETS = 5


def check_tags(subnets, key, value):
    for subnet in subnets:
        found = False
        if hasattr(subnet, 'Tags') and subnet.Tags:
            for tag in subnet.Tags:
                if (not key or tag.Key == key) and (not value or tag.Value == value):
                    found = True
                    break
        assert found, 'Could not find the key or value in subnet {}'.format(subnet.SubnetId)


class Test_ReadSubnets(OscTinaTest):

    @classmethod
    def setup_class(cls):

        cls.net_id = None
        cls.subnet_ids = []
        super(Test_ReadSubnets, cls).setup_class()
        try:
            cls.net_id = cls.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_tools.wait_vpcs_state(cls.a1_r1, [cls.net_id], state='available')
            for i in range(NUM_SUBNETS):
                cls.subnet_ids.append(
                    cls.a1_r1.fcu.CreateSubnet(CidrBlock=Configuration.get('subnet', '10_0_{}_0_24'.format(i + 1)),
                                               VpcId=cls.net_id).response.subnet.subnetId)
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.subnet_ids[0]], Tags=[{'Key': 'sub_key', 'Value': 'sub_value'}])

        except:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            cleanup_tools.cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.net_id], force=True)
        finally:
            super(Test_ReadSubnets, cls).teardown_class()

    def test_T2262_empty_filters(self):
        ret = self.a1_r1.oapi.ReadSubnets()
        assert len(ret.response.Subnets) == NUM_SUBNETS
        ret.check_response()

    def test_T2263_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.ReadSubnets(DryRun=True)
        misc.assert_dry_run(ret)

    def test_T2932_filters_subnet(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"SubnetIds": [self.subnet_ids[0]]}).response.Subnets
        assert len(resp) == 1
        for sub in resp:
            assert hasattr(sub, 'Tags'), 'Tags does not exist in the response'
            assert hasattr(sub, 'SubnetId'), 'SubnetId does not exist in the response'
            assert hasattr(sub, 'AvailableIpsCount'), 'AvailableIpsCount does not exist in the response'
            assert hasattr(sub, 'IpRange'), 'IpRange does not exist in the response'
            assert hasattr(sub, 'NetId'), 'NetId does not exist in the response'
            assert hasattr(sub, 'SubregionName'), 'SubregionName does not exist in the response'
            assert hasattr(sub, 'State'), 'State does not exist in the response'

    def test_T2933_filters_cidr(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"IpRanges": [Configuration.get('subnet', '10_0_{}_0_24'.format(1))]}).response.Subnets
        assert len(resp) == 1
        for sub in resp:
            assert hasattr(sub, 'Tags'), 'Tags does not exist in the response'
            assert hasattr(sub, 'SubnetId'), 'SubnetId does not exist in the response'
            assert hasattr(sub, 'AvailableIpsCount'), 'AvailableIpsCount does not exist in the response'
            assert hasattr(sub, 'IpRange'), 'IpRange does not exist in the response'
            assert hasattr(sub, 'NetId'), 'NetId does not exist in the response'
            assert hasattr(sub, 'SubregionName'), 'SubregionName does not exist in the response'
            assert hasattr(sub, 'State'), 'State does not exist in the response'

    def test_T2934_filters_net_id(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"NetIds": [self.net_id]}).response.Subnets
        assert len(resp) == NUM_SUBNETS
        for sub in resp:
            assert hasattr(sub, 'Tags'), 'Tags does not exist in the response'
            assert hasattr(sub, 'SubnetId'), 'SubnetId does not exist in the response'
            assert hasattr(sub, 'AvailableIpsCount'), 'AvailableIpsCount does not exist in the response'
            assert hasattr(sub, 'IpRange'), 'IpRange does not exist in the response'
            assert hasattr(sub, 'NetId'), 'NetId does not exist in the response'
            assert hasattr(sub, 'SubregionName'), 'SubregionName does not exist in the response'
            assert hasattr(sub, 'State'), 'State does not exist in the response'

    def test_T2935_filters_state(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"States": ['available']}).response.Subnets
        assert len(resp) == NUM_SUBNETS
        for sub in resp:
            assert hasattr(sub, 'Tags'), 'Tags does not exist in the response'
            assert hasattr(sub, 'SubnetId'), 'SubnetId does not exist in the response'
            assert hasattr(sub, 'AvailableIpsCount'), 'AvailableIpsCount does not exist in the response'
            assert hasattr(sub, 'IpRange'), 'IpRange does not exist in the response'
            assert hasattr(sub, 'NetId'), 'NetId does not exist in the response'
            assert hasattr(sub, 'SubregionName'), 'SubregionName does not exist in the response'
            assert hasattr(sub, 'State'), 'State does not exist in the response'

    def test_T2936_filters_subregion_name(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"SubregionNames": [self.azs[0]]}).response.Subnets
        assert len(resp) == NUM_SUBNETS
        for sub in resp:
            assert hasattr(sub, 'Tags'), 'Tags does not exist in the response'
            assert hasattr(sub, 'SubnetId'), 'SubnetId does not exist in the response'
            assert hasattr(sub, 'AvailableIpsCount'), 'AvailableIpsCount does not exist in the response'
            assert hasattr(sub, 'IpRange'), 'IpRange does not exist in the response'
            assert hasattr(sub, 'NetId'), 'NetId does not exist in the response'
            assert hasattr(sub, 'SubregionName'), 'SubregionName does not exist in the response'
            assert hasattr(sub, 'State'), 'State does not exist in the response'

    def test_T3001_filters_available_ips(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"AvailableIpsCounts": [251]}).response.Subnets
        assert len(resp) == NUM_SUBNETS
        for sub in resp:
            assert hasattr(sub, 'Tags'), 'Tags does not exist in the response'
            assert hasattr(sub, 'SubnetId'), 'SubnetId does not exist in the response'
            assert hasattr(sub, 'AvailableIpsCount'), 'AvailableIpsCount does not exist in the response'
            assert hasattr(sub, 'IpRange'), 'IpRange does not exist in the response'
            assert hasattr(sub, 'NetId'), 'NetId does not exist in the response'
            assert hasattr(sub, 'SubregionName'), 'SubregionName does not exist in the response'
            assert hasattr(sub, 'State'), 'State does not exist in the response'
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"AvailableIpsCounts": [25]}).response.Subnets
        assert len(resp) == 0

    @pytest.mark.tag_sec_confidentiality
    def test_T3439_with_other_account(self):
        resp = self.a2_r1.oapi.ReadSubnets().response
        assert not resp.Subnets

    @pytest.mark.tag_sec_confidentiality
    def test_T3440_with_other_account_filters(self):
        resp = self.a2_r1.oapi.ReadSubnets(Filters={"NetIds": [self.net_id]}).response
        assert not resp.Subnets

    def test_T5090_with_tags_filter(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"Tags": ['sub_key=sub_value']}).response
        assert len(resp.Subnets) == 1
        check_tags(resp.Subnets, 'sub_key', 'sub_value')

    def test_T5091_with_tagkeys_filter(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"TagKeys": ['sub_key']}).response
        assert len(resp.Subnets) == 1
        check_tags(resp.Subnets, 'sub_key', None)

    def test_T5092_with_tagvalues_filter(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"TagValues": ['sub_value']}).response
        assert len(resp.Subnets) == 1
        check_tags(resp.Subnets, None, 'sub_value')

    def test_T5093_with_invalid_tags_filter(self):
        resp = self.a1_r1.oapi.ReadSubnets(Filters={"Tags": ['incorrect_sub=incorrect_sub_value']}).response
        assert len(resp.Subnets) == 0

    def test_T5094_with_incorrect_tags_filter(self):
        try:
            self.a1_r1.oapi.ReadSubnets(Filters={"Tags": 'sub=sub_value'})
            assert False, 'Call should fail'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameterValue', '4110')

    def test_T5980_with_tag_filter(self):
        indexes, _ = misc.execute_tag_tests(self.a1_r1, 'Subnet', self.subnet_ids, 'oapi.ReadSubnets', 'Subnets.SubnetId')
        assert indexes == [3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 19, 20, 24, 25, 26, 27, 28, 29]
        known_error('API-399', 'Read calls do not support wildcards in tag filtering')
