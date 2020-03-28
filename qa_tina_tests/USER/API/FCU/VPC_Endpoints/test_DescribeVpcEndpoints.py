
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_endpoints_state
from qa_tina_tools.tools.tina.info_keys import VPC_ID, ROUTE_TABLE_ID
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs


class Test_DescribeVpcEndpoints(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.vpc_info2 = None
        cls.vpcendpointid1 = None
        cls.vpcendpointid2 = None
        super(Test_DescribeVpcEndpoints, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(osc_sdk=cls.a1_r1, nb_subnet=0, igw=False)
            ret1 = cls.a1_r1.fcu.CreateVpcEndpoint(VpcId=cls.vpc_info[VPC_ID],
                                                  ServiceName='com.outscale.{}.osu'.format(cls.a1_r1.config.region.name),
                                                  RouteTableId=cls.vpc_info[ROUTE_TABLE_ID])
            cls.vpcendpointid1 = ret1.response.vpcEndpoint.vpcEndpointId
            cls.vpc_info2 = create_vpc(osc_sdk=cls.a1_r1, nb_subnet=0, igw=False)
            ret2 = cls.a1_r1.fcu.CreateVpcEndpoint(VpcId=cls.vpc_info2[VPC_ID],
                                                  ServiceName='com.outscale.{}.osu'.format(cls.a1_r1.config.region.name),
                                                  RouteTableId=cls.vpc_info2[ROUTE_TABLE_ID])
            cls.vpcendpointid2 = ret2.response.vpcEndpoint.vpcEndpointId
            wait_vpc_endpoints_state(cls.a1_r1, [cls.vpcendpointid1, cls.vpcendpointid2], state='available')
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_info:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info[VPC_ID]], force=True)
            if cls.vpc_info2:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info2[VPC_ID]], force=True)
        finally:
            super(Test_DescribeVpcEndpoints, cls).teardown_class()

    def test_T4272_without_params(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints()
        assert len(ret.response.vpcEndpointSet) == 2

    def test_T4273_filter_net_id(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'vpc-id', 'Value':self.vpc_info[VPC_ID]}])
        assert len(ret.response.vpcEndpointSet) == 1

    def test_T4553_with_vpcendpointid(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(VpcEndpointId=self.vpcendpointid1)
        assert len(ret.response.vpcEndpointSet) == 1
        assert self.vpcendpointid1 == ret.response.vpcEndpointSet[0].vpcEndpointId
        assert ret.response.vpcEndpointSet[0].serviceName == 'com.outscale.{}.osu'.format(self.a1_r1.config.region.name)
        assert ret.response.vpcEndpointSet[0].state == 'available'
        assert ret.response.vpcEndpointSet[0].vpcId == self.vpc_info[VPC_ID]
        assert ret.response.vpcEndpointSet[0].routeTableIdSet[0] == self.vpc_info[ROUTE_TABLE_ID]

    def test_T4474_with_multiple_vpcendpointid(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(VpcEndpointId=[self.vpcendpointid1, self.vpcendpointid2])
        assert len(ret.response.vpcEndpointSet) == 2

    def test_T4475_filter_servicename(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'service-name', 'Value':'com.outscale.{}.osu'.format(self.a1_r1.config.region.name)}])
        assert len(ret.response.vpcEndpointSet) == 2

    def test_T4476_filter_invalid_servicename(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'service-name', 'Value':'foo'}])
        assert ret.response.vpcEndpointSet == None

    def test_T4477_filter_invalid_net_id(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'vpc-id', 'Value':'vpc-xxxxxxx'}])
        assert ret.response.vpcEndpointSet == None

    def test_T4478_filter_vpcendpointid(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'vpc-endpoint-id', 'Value':self.vpcendpointid1}])
        assert len(ret.response.vpcEndpointSet) == 1
        assert self.vpcendpointid1 == ret.response.vpcEndpointSet[0].vpcEndpointId
        assert ret.response.vpcEndpointSet[0].serviceName == 'com.outscale.{}.osu'.format(self.a1_r1.config.region.name)
        assert ret.response.vpcEndpointSet[0].state == 'available'
        assert ret.response.vpcEndpointSet[0].vpcId == self.vpc_info[VPC_ID]
        assert ret.response.vpcEndpointSet[0].routeTableIdSet[0] == self.vpc_info[ROUTE_TABLE_ID]

    def test_T4479_filter_invalid_vpcendpointid(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'vpc-endpoint-id', 'Value':'vpc-xxxxxxx'}])
        assert ret.response.vpcEndpointSet == None

    def test_T4480_filter_vpcendpointstate(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'vpc-endpoint-state', 'Value':'available'}])
        assert len(ret.response.vpcEndpointSet) == 2      
        self.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=[self.vpcendpointid1])
        wait_vpc_endpoints_state(self.a1_r1, [self.vpcendpointid1], state='deleted')
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'vpc-endpoint-state', 'Value':'deleted'}])
        assert len(ret.response.vpcEndpointSet) == 1

    def test_T4481_filter_invalid_vpcendpointstate(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(Filter=[{'Name':'vpc-endpoint-state', 'Value':'attaching'}])
        assert ret.response.vpcEndpointSet == None

