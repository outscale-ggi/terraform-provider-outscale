
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina import create_tools, delete_tools, wait_tools
from qa_tina_tools.tools.tina import info_keys


class Test_ReadNetPeerings(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.a1_vpc = []
        cls.a2_vpc = []
        cls.a1_peering_ids = []
        cls.a2_peering_ids = []
        super(Test_ReadNetPeerings, cls).setup_class()
        try:
            for i in range(2):
                cls.a1_vpc.append(create_tools.create_vpc(cls.a1_r1, cidr_prefix="10.1{}".format(i), igw=False, default_rtb=True, no_ping=True))
                cls.a2_vpc.append(create_tools.create_vpc(cls.a2_r1, cidr_prefix="10.2{}".format(i), igw=False, default_rtb=True, no_ping=True))
            # a1_vpc1 a1_vpc2
            # a2_vpc1 a2_vpc2
            # a1_vpc2 a2_vpc1
            # a2_vpc2 a1_vpc1
            ret = cls.a1_r1.oapi.CreateNetPeering(SourceNetId=cls.a1_vpc[0][info_keys.VPC_ID], AccepterNetId=cls.a1_vpc[1][info_keys.VPC_ID])
            cls.a1_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a2_r1.oapi.CreateNetPeering(SourceNetId=cls.a2_vpc[0][info_keys.VPC_ID], AccepterNetId=cls.a2_vpc[1][info_keys.VPC_ID])
            cls.a2_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a1_r1.oapi.CreateNetPeering(SourceNetId=cls.a1_vpc[0][info_keys.VPC_ID], AccepterNetId=cls.a2_vpc[0][info_keys.VPC_ID])
            cls.a1_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a1_r1.oapi.CreateNetPeering(SourceNetId=cls.a1_vpc[0][info_keys.VPC_ID], AccepterNetId=cls.a2_vpc[1][info_keys.VPC_ID])
            cls.a1_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a1_r1.oapi.CreateNetPeering(SourceNetId=cls.a1_vpc[1][info_keys.VPC_ID], AccepterNetId=cls.a2_vpc[0][info_keys.VPC_ID])
            cls.a1_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a1_r1.oapi.CreateNetPeering(SourceNetId=cls.a1_vpc[1][info_keys.VPC_ID], AccepterNetId=cls.a2_vpc[1][info_keys.VPC_ID])
            cls.a1_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a2_r1.oapi.CreateNetPeering(SourceNetId=cls.a2_vpc[0][info_keys.VPC_ID], AccepterNetId=cls.a1_vpc[0][info_keys.VPC_ID])
            cls.a2_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a2_r1.oapi.CreateNetPeering(SourceNetId=cls.a2_vpc[0][info_keys.VPC_ID], AccepterNetId=cls.a1_vpc[1][info_keys.VPC_ID])
            cls.a2_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a2_r1.oapi.CreateNetPeering(SourceNetId=cls.a2_vpc[1][info_keys.VPC_ID], AccepterNetId=cls.a1_vpc[0][info_keys.VPC_ID])
            cls.a2_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            ret = cls.a2_r1.oapi.CreateNetPeering(SourceNetId=cls.a2_vpc[1][info_keys.VPC_ID], AccepterNetId=cls.a1_vpc[1][info_keys.VPC_ID])
            cls.a2_peering_ids.append(ret.response.NetPeering.NetPeeringId)
            cls.a1_r1.oapi.CreateTags(ResourceIds=[cls.a1_peering_ids[0]], Tags=[{'Key': 'foo', 'Value': 'bar'}])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception as err:
                raise err
            finally:
                raise error

    @classmethod
    def teardown_class(cls):
        try:
            for peering in cls.a1_peering_ids:
                cls.a1_r1.oapi.DeleteNetPeering(NetPeeringId=peering)
            for peering in cls.a2_peering_ids:
                cls.a2_r1.oapi.DeleteNetPeering(NetPeeringId=peering)
            wait_tools.wait_vpc_peering_connections_state(cls.a1_r1, vpc_peering_connection_id_list=cls.a1_peering_ids, state='deleted')
            wait_tools.wait_vpc_peering_connections_state(cls.a2_r1, vpc_peering_connection_id_list=cls.a2_peering_ids, state='deleted')
            for vpc_info in cls.a1_vpc:
                delete_tools.delete_vpc(cls.a1_r1, vpc_info)
            for vpc_info in cls.a2_vpc:
                delete_tools.delete_vpc(cls.a2_r1, vpc_info)
        finally:
            super(Test_ReadNetPeerings, cls).teardown_class()

    def test_T2424_dry_run(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(DryRun=True)
        misc.assert_dry_run(ret)

    def test_T1989_without_param(self):
        ret = self.a1_r1.oapi.ReadNetPeerings()
        assert len(ret.response.NetPeerings) == 9
        # TODO: check response

    def test_T1997_with_valid_filter_accepter_net_account_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'AccepterNetAccountIds': [self.a2_r1.config.account.account_id]})
        assert len(ret.response.NetPeerings) == 4

    def test_T1993_with_valid_filter_accepter_net_ip_ranges(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'AccepterNetIpRanges': ['10.20.0.0/16']})
        assert len(ret.response.NetPeerings) == 2

    def test_T1995_with_valid_filter_accepter_net_net_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'AccepterNetNetIds': [self.a2_vpc[0][info_keys.VPC_ID]]})
        assert len(ret.response.NetPeerings) == 2

    def test_T1992_with_valid_filter_net_peering_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'NetPeeringIds': [self.a1_peering_ids[0]]})
        assert len(ret.response.NetPeerings) == 1
        assert len(ret.response.NetPeerings[0].Tags) == 1

    def test_T1998_with_valid_filter_source_net_account_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'SourceNetAccountIds': [self.a2_r1.config.account.account_id]})
        assert len(ret.response.NetPeerings) == 4

    def test_T1994_with_valid_filter_source_net_ip_ranges(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'SourceNetIpRanges': ['10.10.0.0/16']})
        assert len(ret.response.NetPeerings) == 3

    def test_T1996_with_valid_filter_source_net_net_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'SourceNetNetIds': [self.a1_vpc[0][info_keys.VPC_ID]]})
        assert len(ret.response.NetPeerings) == 3

    def test_T2001_with_valid_filter_state_mesages(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'StateMessages': ["Pending acceptance by {}".format(
            self.a2_r1.config.account.account_id)]})
        assert len(ret.response.NetPeerings) == 4

    def test_T2000_with_valid_filter_state_names(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'StateNames': ['pending-acceptance']})
        assert len(ret.response.NetPeerings) == 9

    def test_T2425_with_valid_filter_tag_keys(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'TagKeys': ['foo']})
        assert len(ret.response.NetPeerings) == 1

    def test_T2426_with_valid_filter_tag_values(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'TagValues': ['bar']})
        assert len(ret.response.NetPeerings) == 1

    def test_T2427_with_valid_filter_tags(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'Tags': ['foo=bar']})
        assert len(ret.response.NetPeerings) == 1

    def test_T2428_with_invalid_filter_accepter_net_account_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'AccepterNetAccountIds': ['012345678901']})
        assert not ret.response.NetPeerings

    def test_T2429_with_invalid_filter_accepter_net_ip_ranges(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'AccepterNetIpRanges': ['1.2.0.0/16']})
        assert not ret.response.NetPeerings

    def test_T2430_with_invalid_filter_accepter_net_net_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'AccepterNetNetIds': ['vpc-12345678']})
        assert not ret.response.NetPeerings

    def test_T1991_with_invalid_filter_net_peering_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'NetPeeringIds': ['pcx-1234578']})
        assert not ret.response.NetPeerings

    def test_T2431_with_invalid_filter_source_net_account_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'SourceNetAccountIds': ['012345678901']})
        assert not ret.response.NetPeerings

    def test_T2432_with_invalid_filter_source_net_ip_ranges(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'SourceNetIpRanges': ['1.1.0.0/16']})
        assert not ret.response.NetPeerings

    def test_T2433_with_invalid_filter_source_net_net_ids(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'SourceNetNetIds': ['vpc-12345678']})
        assert not ret.response.NetPeerings

    def test_T2434_with_invalid_filter_state_mesages(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'StateMessages': ["Active"]})
        assert not ret.response.NetPeerings

    def test_T2435_with_invalid_filter_state_names(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'StateNames': ['active']})
        assert not ret.response.NetPeerings

    def test_T2436_with_invalid_filter_tag_keys(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'TagKeys': ['bar']})
        assert not ret.response.NetPeerings

    def test_T2437_with_invalid_filter_tag_values(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'TagValues': ['foo']})
        assert not ret.response.NetPeerings

    def test_T2438_with_invalid_filter_tags(self):
        ret = self.a1_r1.oapi.ReadNetPeerings(Filters={'Tags': ['bar=foo']})
        assert not ret.response.NetPeerings

    def test_T2439_with_invalid_filter(self):
        try:
            self.a1_r1.oapi.ReadNetPeerings(Filters={'foo': ['bar']})
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            misc.assert_oapi_error(error, 400, 'InvalidParameter', '3001')

    @pytest.mark.tag_sec_confidentiality
    def test_T3447_with_other_account(self):
        ret = self.a3_r1.oapi.ReadNetPeerings()
        assert not ret.response.NetPeerings

    @pytest.mark.tag_sec_confidentiality
    def test_T3449_with_other_account_filters(self):
        ret = self.a3_r1.oapi.ReadNetPeerings(Filters={'TagValues': ['bar']})
        assert not ret.response.NetPeerings

    def test_T5973_with_tag_filter(self):
        misc.execute_tag_tests(self.a1_r1, 'NetPeering', self.a1_peering_ids,
                               'oapi.ReadNetPeerings', 'NetPeerings.NetPeeringId')
