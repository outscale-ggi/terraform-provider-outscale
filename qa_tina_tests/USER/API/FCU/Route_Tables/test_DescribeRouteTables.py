# pylint: disable=missing-docstring

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


NUM_RTS = 3


class Test_DescribeRouteTables(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_id = None
        cls.rt_ids = []
        super(Test_DescribeRouteTables, cls).setup_class()
        try:
            cls.vpc_id = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16')).response.vpc.vpcId
            for _ in range(NUM_RTS):
                rt_info = cls.a1_r1.fcu.CreateRouteTable(VpcId=cls.vpc_id)
                rtb_id = rt_info.response.routeTable.routeTableId
                cls.rt_ids.append(rtb_id)
        except Exception:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.rt_ids:
                for i in cls.rt_ids:
                    cls.a1_r1.fcu.DeleteRouteTable(RouteTableId=i)
            if cls.vpc_id:
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)
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
