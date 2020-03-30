from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import INTERNET_GATEWAY_ID, VPC_ID


class Test_DescribeInternetGateways(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.a1_vpc_info = None
        cls.a1_igw_ids = []
        cls.a2_vpc_info = None
        cls.a2_igw_id = None
        super(Test_DescribeInternetGateways, cls).setup_class()
        try:
            cls.a1_vpc_info = create_vpc(cls.a1_r1)
            cls.a1_r1.fcu.CreateTags(Tag=[{'Key': 'tagkey1', 'Value': 'tagvalue1'}], ResourceId=cls.a1_vpc_info[INTERNET_GATEWAY_ID])
            igw_id = cls.a1_r1.fcu.CreateInternetGateway().response.internetGateway.internetGatewayId
            cls.a1_r1.fcu.CreateTags(Tag=[{'Key': 'tagkey1', 'Value': 'tagvalue2'}], ResourceId=igw_id)
            cls.a1_igw_ids.append(igw_id)
            igw_id = cls.a1_r1.fcu.CreateInternetGateway().response.internetGateway.internetGatewayId
            cls.a1_r1.fcu.CreateTags(Tag=[{'Key': 'tagkey2', 'Value': 'tagvalue1'}], ResourceId=igw_id)
            cls.a1_igw_ids.append(igw_id)
            igw_id = cls.a1_r1.fcu.CreateInternetGateway().response.internetGateway.internetGatewayId
            cls.a1_r1.fcu.CreateTags(Tag=[{'Key': 'tagkey2', 'Value': 'tagvalue2'}], ResourceId=igw_id)
            cls.a1_igw_ids.append(igw_id)
            cls.a1_igw_id = cls.a1_igw_ids[0]
            cls.a2_vpc_info = create_vpc(cls.a2_r1)
            cls.a2_r1.fcu.CreateTags(Tag=[{'Key': 'tagkey1', 'Value': 'tagvalue1'}], ResourceId=cls.a2_vpc_info[INTERNET_GATEWAY_ID])
            cls.a2_igw_id = cls.a2_r1.fcu.CreateInternetGateway().response.internetGateway.internetGatewayId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.a1_vpc_info:
                delete_vpc(cls.a1_r1, cls.a1_vpc_info)
            if cls.a2_vpc_info:
                delete_vpc(cls.a2_r1, cls.a2_vpc_info)
            if cls.a1_igw_ids:
                for igw_id in cls.a1_igw_ids:
                    cls.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)
            if cls.a2_igw_id:
                cls.a2_r1.fcu.DeleteInternetGateway(InternetGatewayId=cls.a2_igw_id)
        finally:
            super(Test_DescribeInternetGateways, cls).teardown_class()

    def test_T1820_without_params(self):
        resp = self.a1_r1.fcu.DescribeInternetGateways().response
        assert resp.requestId
        assert len(resp.internetGatewaySet) == 4

    def test_T1821_filter_attachment_state(self):
        resp = self.a1_r1.fcu.DescribeInternetGateways(Filter=[{'Name': 'attachment.state', 'Value': 'available'}]).response
        assert resp.requestId
        assert len(resp.internetGatewaySet) == 1
        assert resp.internetGatewaySet[0].internetGatewayId == self.a1_vpc_info[INTERNET_GATEWAY_ID]
        assert resp.internetGatewaySet[0].attachmentSet[0].state == 'available'
        assert resp.internetGatewaySet[0].attachmentSet[0].vpcId == self.a1_vpc_info[VPC_ID]
        assert resp.internetGatewaySet[0].tagSet[0].key == 'tagkey1'
        assert resp.internetGatewaySet[0].tagSet[0].value == 'tagvalue1'

    def test_T1822_filter_attachment_vpc_id(self):
        resp = self.a1_r1.fcu.DescribeInternetGateways(Filter=[{'Name': 'attachment.vpc-id', 'Value': self.a1_vpc_info[VPC_ID]}]).response
        assert resp.requestId
        assert len(resp.internetGatewaySet) == 1

    def test_T1823_filter_internet_gateway_id(self):
        resp = self.a1_r1.fcu.DescribeInternetGateways(Filter=[{'Name': 'internet-gateway-id', 'Value': self.a1_igw_id}]).response
        assert resp.requestId
        assert len(resp.internetGatewaySet) == 1

    def test_T1824_filter_tag(self):
        resp = self.a1_r1.fcu.DescribeInternetGateways(Filter=[{'Name': 'tag:tagkey1', 'Value': 'tagvalue1'}]).response
        assert resp.requestId
        assert len(resp.internetGatewaySet) == 1

    def test_T1825_filter_tag_key(self):
        resp = self.a1_r1.fcu.DescribeInternetGateways(Filter=[{'Name': 'tag-key', 'Value': 'tagkey2'}]).response
        assert resp.requestId
        assert len(resp.internetGatewaySet) == 2

    def test_T1826_filter_tag_value(self):
        resp = self.a1_r1.fcu.DescribeInternetGateways(Filter=[{'Name': 'tag-value', 'Value': 'tagvalue2'}]).response
        assert resp.requestId
        assert len(resp.internetGatewaySet) == 2
