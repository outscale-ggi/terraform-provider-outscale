from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


# author:Emanuel Dias
class Test_DeleteRouteTable(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_id = None
        super(Test_DeleteRouteTable, cls).setup_class()
        try:
            # create VPC
            vpc = cls.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            cls.vpc_id = vpc.response.vpc.vpcId
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_id:
                # delete VPC
                cls.a1_r1.fcu.DeleteVpc(VpcId=cls.vpc_id)
        finally:
            super(Test_DeleteRouteTable, cls).teardown_class()

    def test_T598_delete_main_routetable(self):
        try:
            fil = {'Name': 'vpc-id', 'Value': [self.vpc_id]}
            ret = self.a1_r1.fcu.DescribeRouteTables(Filter=[fil])
            main_rtb_id = ret.response.routeTableSet[0].routeTableId
            self.a1_r1.fcu.DeleteRouteTable(RouteTableId=main_rtb_id)
            assert False, 'Deletion of mainRouteTable should have failed'
        except OscApiException as error:
            assert_error(error, 400, 'DependencyViolation', "The route table '{}' has dependencies and cannot be deleted.".format(main_rtb_id))

    def test_T594_no_param(self):
        try:
            self.a1_r1.fcu.DeleteRouteTable()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'DependencyViolation', 'Resource has a dependent object')
