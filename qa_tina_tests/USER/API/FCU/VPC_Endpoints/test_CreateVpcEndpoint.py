from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID, ROUTE_TABLE_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_endpoints_state, wait_vpcs_state


class Test_CreateVpcEndpoint(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        cls.vpc_id = None
        super(Test_CreateVpcEndpoint, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateVpcEndpoint, cls).teardown_class()

    def setup_method(self, method):
        try:
            self.vpc_info = create_vpc(osc_sdk=self.a1_r1, nb_subnet=0, igw=False)
            wait_vpcs_state(self.a1_r1, [self.vpc_info[VPC_ID]], state='available')
        except Exception as error:
            try:
                self.teardown_method(method)
            finally:
                raise error

    def teardown_method(self, method):
        try:
            if self.vpc_info:
                cleanup_vpcs(self.a1_r1, vpc_id_list=[self.vpc_info[VPC_ID]], force=True)
        finally:
            super(Test_CreateVpcEndpoint, self).teardown_method(method)

    def test_T4271_valid_params(self):
        ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
                                               RouteTableId=self.vpc_info[ROUTE_TABLE_ID])
        wait_vpc_endpoints_state(self.a1_r1, [ret.response.vpcEndpoint.vpcEndpointId], state='available')

    def test_T2608_with_same_route_table(self):
        rtb_id = self.a1_r1.fcu.DescribeRouteTables(Filter=[{'Name': 'vpc-id',
                                                             'Value': [self.vpc_info[VPC_ID]]}]).response.routeTableSet[0].routeTableId
        # rtb_id = self.a1_r1.oapi.ReadRouteTables(Filters={'NetIds': [self.net_id]}).response.RouteTables[0].RouteTableId
        ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
                                               RouteTableId=rtb_id)
        wait_vpc_endpoints_state(self.a1_r1, [ret.response.vpcEndpoint.vpcEndpointId], state='available')
        try:
            ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID],
                                                   ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name), RouteTableId=rtb_id)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            msg = "VPC endpoint already exists for ServiceName: com.outscale.{}.api, RouteTablesIDs: {}"
            assert_error(err, 400, 'VPCEndpointAlreadyExists', msg.format(self.a1_r1.config.region.name, rtb_id))

    def test_T4267_with_missing_params(self):
        try:
            self.a1_r1.fcu.CreateVpcEndpoint()
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'Request is missing the following parameter: VpcId, ServiceName')
        try:
            self.a1_r1.fcu.CreateVpcEndpoint(ServiceName='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'Request is missing the following parameter: VpcId')
        try:
            self.a1_r1.fcu.CreateVpcEndpoint(VpcId='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'Request is missing the following parameter: ServiceName')

    def test_T4268_with_invalid_vpc_id(self):
        try:
            self.a1_r1.fcu.CreateVpcEndpoint(VpcId='net-toto', ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name))
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidVpcID.NotFound', "The vpc ID 'net-toto' does not exist")

    def test_T4269_unknown_service_name(self):
        try:
            self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='toto')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidServiceName', "Service 'toto' does not exists")

    def test_T4270_invalid_route_table_ids(self):
        try:
            self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
                                             RouteTableId=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidRouteTableID.NotFound', "The route table ID 'toto' does not exist")
        try:
            self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
                                             RouteTableId=['rtb-1234567'])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidRouteTableID.NotFound', "The route table ID 'rtb-1234567' does not exist")

    def test_T4499_existing_vpcendpoint(self):
        try:
            ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID],
                                                   ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
                                                   RouteTableId=self.vpc_info[ROUTE_TABLE_ID])
            wait_vpc_endpoints_state(self.a1_r1, [ret.response.vpcEndpoint.vpcEndpointId], state='available')
            ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID],
                                                   ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name),
                                                   RouteTableId=self.vpc_info[ROUTE_TABLE_ID])
            wait_vpc_endpoints_state(self.a1_r1, [ret.response.vpcEndpoint.vpcEndpointId], state='available')
        except OscApiException as err:
            assert_error(err, 400, 'VPCEndpointAlreadyExists', "VPC endpoint already exists for ServiceName: com.outscale.{}.api, RouteTablesIDs: {}"
                         .format(self.a1_r1.config.region.name, self.vpc_info[ROUTE_TABLE_ID]))
