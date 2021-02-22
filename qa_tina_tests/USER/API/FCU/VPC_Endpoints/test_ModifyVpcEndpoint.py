from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID, ROUTE_TABLE_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_endpoints_state


class Test_ModifyVpcEndpoint(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.vpc_info2 = None
        cls.vpcendpointid1 = None
        super(Test_ModifyVpcEndpoint, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(osc_sdk=cls.a1_r1, nb_subnet=0, igw=False)
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
            if cls.vpc_info:
                cleanup_vpcs(cls.a1_r1, vpc_id_list=[cls.vpc_info[VPC_ID]], force=True)
        finally:
            super(Test_ModifyVpcEndpoint, cls).teardown_class()

    def setup_method(self, method):
        try:
            ret1 = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID],
                                                  ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
                                                  RouteTableId=self.vpc_info[ROUTE_TABLE_ID])
            self.vpcendpointid1 = ret1.response.vpcEndpoint.vpcEndpointId
            wait_vpc_endpoints_state(self.a1_r1, [self.vpcendpointid1], state='available')
        except Exception as error:
            try:
                self.teardown_method(method)
            except Exception as err:
                raise err
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.vpcendpointid1:
                self.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=self.vpcendpointid1)
        finally:
            super(Test_ModifyVpcEndpoint, self).teardown_method(method)

    def test_T4487_no_params(self):
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', "Request is missing the following parameter: VpcEndpointId")

    def test_T4488_valid_params(self):
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1)
        assert ret.response.osc_return

    def test_T4489_invalid_vpcendpointid(self):
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: NetworkEndpoint')
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=[self.vpcendpointid1])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', "Unexpected parameter VpcEndpointId.1")
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=True)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcEndpointID.Malformed', 'Invalid ID received: True. Expected format: vpce-')
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId='123456')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcEndpointID.Malformed', 'Invalid ID received: 123456. Expected format: vpce-')

    def test_T4490_add_with_addroutetableid(self):
        rtb_id = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, AddRouteTableId=rtb_id)
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(VpcEndpointId=self.vpcendpointid1)
        print(ret.response.display())
        assert len(ret.response.vpcEndpointSet[0].routeTableIdSet) == 2

    def test_T4491_add_with_multiple_routetableid(self): 
        rtb_id = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
        rtb_id2 = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, AddRouteTableId=[rtb_id, rtb_id2])
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(VpcEndpointId=self.vpcendpointid1)
        assert len(ret.response.vpcEndpointSet[0].routeTableIdSet) == 3
        assert rtb_id in ret.response.vpcEndpointSet[0].routeTableIdSet
        assert rtb_id2 in ret.response.vpcEndpointSet[0].routeTableIdSet
        assert self.vpc_info[ROUTE_TABLE_ID] in ret.response.vpcEndpointSet[0].routeTableIdSet

    def test_T4492_add_with_invalid_routetableid(self): 
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, AddRouteTableId=['rtb-12345678'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRouteTableID.NotFound', "The route table ID 'rtb-12345678' does not exist")

    def test_T4493_add_with_routetableid_with_other_account(self): 
        try:
            rtb_id = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
            self.a2_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, AddRouteTableId=rtb_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidVpcEndpointId.NotFound', "VPC Endpoint '{}' does not exist".format(self.vpcendpointid1))

    def test_T4494_remove_with_invalid_routetableid(self): 
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, RemoveRouteTableId=['rtb-12345678'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRouteTableID.NotFound', "The route table ID 'rtb-12345678' does not exist")

    def test_T4495_remove_with_multiple_routetableida(self): 
        rtb_id = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
        rtb_id2 = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, AddRouteTableId=[rtb_id, rtb_id2])
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, RemoveRouteTableId=[rtb_id, rtb_id2])
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(VpcEndpointId=self.vpcendpointid1)
        assert len(ret.response.vpcEndpointSet[0].routeTableIdSet) == 1
        assert self.vpc_info[ROUTE_TABLE_ID] in ret.response.vpcEndpointSet[0].routeTableIdSet

    def test_T4496_remove_with_routetableid(self): 
        rtb_id = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, AddRouteTableId=rtb_id)
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, RemoveRouteTableId=[self.vpc_info[ROUTE_TABLE_ID]])
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(VpcEndpointId=self.vpcendpointid1)
        assert len(ret.response.vpcEndpointSet[0].routeTableIdSet) == 1
        assert rtb_id in ret.response.vpcEndpointSet[0].routeTableIdSet

    def test_T4497_with_all_params(self): 
        rtb_id = self.a1_r1.fcu.CreateRouteTable(VpcId=self.vpc_info[VPC_ID]).response.routeTable.routeTableId
        ret = self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, AddRouteTableId=rtb_id,
                                               RemoveRouteTableId=self.vpc_info[ROUTE_TABLE_ID])
        assert ret.response.osc_return
        ret = self.a1_r1.fcu.DescribeVpcEndpoints(VpcEndpointId=self.vpcendpointid1)
        assert len(ret.response.vpcEndpointSet[0].routeTableIdSet) == 1
        assert rtb_id in ret.response.vpcEndpointSet[0].routeTableIdSet

    def test_T4498_incorrect_params(self): 
        try:
            self.a1_r1.fcu.ModifyVpcEndpoint(VpcEndpointId=self.vpcendpointid1, ServiceName=self.vpc_info[ROUTE_TABLE_ID])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue', 'Unexpected parameter ServiceName')
