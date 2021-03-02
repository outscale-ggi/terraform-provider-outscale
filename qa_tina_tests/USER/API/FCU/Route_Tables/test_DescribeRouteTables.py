# pylint: disable=missing-docstring
from qa_tina_tools.tools.tina.create_tools import create_vpc

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import ROUTE_TABLE_ID, INTERNET_GATEWAY_ID, VPC_ID, SUBNETS, SUBNET_ID


NUM_RTS = 3


class Test_DescribeRouteTables(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_id = None
        cls.rt_ids = []
        super(Test_DescribeRouteTables, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_subnet=1, igw=True, default_rtb=True)
            cls.vpc_id = cls.vpc_info[VPC_ID]
            for _ in range(NUM_RTS):
                rt_info = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_id)
                rtb_id = rt_info.response.routeTable.routeTableId
                cls.rt_ids.append(rtb_id)
            cls.rtb_assoc_id = cls.a1_r1.fcu.AssociateRouteTable(RouteTableId=cls.rt_ids[0],
                                                                 SubnetId=cls.vpc_info[SUBNETS][0][SUBNET_ID]).response.associationId
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            if cls.rtb_assoc_id:
                cls.a1_r1.fcu.DisassociateRouteTable(AssociationId=cls.rtb_assoc_id)
            if cls.rt_ids:
                for i in cls.rt_ids:
                    cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=i)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DescribeRouteTables, cls).teardown_class()

    def test_T3227_with_other_account(self):
        ret = self.a2_r1.fcu.DescribeRouteTables()
        assert not ret.response.routeTableSet, 'Unexpected non-empty result'

    def test_T3274_without_param(self):
        ret = self.a1_r1.fcu.DescribeRouteTables().response.routeTableSet
        assert len(set([RouteTable.routeTableId for RouteTable in ret])) == len(self.rt_ids) + 1
        for rtb in ret:
            if not rtb.associationSet or not rtb.associationSet[0].main:
                assert rtb.routeTableId in self.rt_ids

    def test_T3275_with_other_account_with_param(self):
        try:
            self.a2_r1.fcu.DescribeRouteTables(RouteTableId=[self.rt_ids[0]])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidRouteTableID.NotFound', "The routeTable IDs u'{}' do not exist".format(self.rt_ids[0]))

    def test_T3276_with_other_account_with_filter(self):
        ret = self.a2_r1.fcu.DescribeRouteTables(Filter=[{'Name': 'route-table-id', 'Value': self.rt_ids[0]}])
        assert not ret.response.routeTableSet

    def test_T5547_with_associationroutetableassociation_id_filter(self):
        ret = self.a1_r1.fcu.DescribeRouteTables(Filter=[{'Name': 'association.route-table-association-id', 'Value': self.rtb_assoc_id}])
        assert ret.response.routeTableSet[0].associationSet[0].routeTableId == self.rt_ids[0]
