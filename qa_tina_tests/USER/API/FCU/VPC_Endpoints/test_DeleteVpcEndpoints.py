
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID
from qa_tina_tools.tools.tina.wait_tools import wait_vpc_endpoints_state


class Test_DeleteVpcEndpoints(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vpc_info = None
        super(Test_DeleteVpcEndpoints, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(osc_sdk=cls.a1_r1, nb_subnet=0, igw=False)
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
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_DeleteVpcEndpoints, cls).teardown_class()

    def test_T1721_without_param(self):
        try:
            self.a1_r1.fcu.DeleteVpcEndpoints()
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            if  error.message == 'Request is missing the following parameter: VpcEndpointIds':
                known_error('TINA-5256', 'DeleteVpcEndpoints incorrect error message')
            assert False, 'Remove known error code'
            assert_error(error, 400, 'MissingParameter', 'Request is missing the following parameter: VpcEndpointId')

    def test_T1722_with_invalid_vpc_endpoint_id(self):
        ret = self.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId='foo')
        assert ret.status_code == 200
        assert ret.response.unsuccessful[0].error.code == 'InvalidVpcEndpointId.NotFound'
        assert ret.response.unsuccessful[0].error.message == "VPC Endpoint 'foo' does not exist"
        ret = self.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=['foo'])
        assert ret.status_code == 200
        assert ret.response.unsuccessful[0].error.code == 'InvalidVpcEndpointId.NotFound'
        assert ret.response.unsuccessful[0].error.message == "VPC Endpoint 'foo' does not exist"

    def test_T1723_with_valid_vpc_endpoint_id(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpointServices()
        if not ret.response.serviceNameSet:
            pytest.skip('VpcEndpoints not supported on {}'.format(self.a1_r1.config.region.name))
        ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name))
        vpc_endpoint_id = ret.response.vpcEndpoint.vpcEndpointId
        wait_vpc_endpoints_state(self.a1_r1, [vpc_endpoint_id], state='available')
        self.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=[vpc_endpoint_id])
        wait_vpc_endpoints_state(self.a1_r1, [vpc_endpoint_id], state='deleted')

    def test_T1724_with_multiple_vpc_endpoint_id(self):
        ret = self.a1_r1.fcu.DescribeVpcEndpointServices()
        if not ret.response.serviceNameSet:
            pytest.skip('VpcEndpoints not supported on {}'.format(self.a1_r1.config.region.name))
        vpc_endpoint_id_list = []
        ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name))
        vpc_endpoint_id_list.append(ret.response.vpcEndpoint.vpcEndpointId)
        ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID], ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name))
        vpc_endpoint_id_list.append(ret.response.vpcEndpoint.vpcEndpointId)
        wait_vpc_endpoints_state(self.a1_r1, vpc_endpoint_id_list, state='available')
        self.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=vpc_endpoint_id_list)
        wait_vpc_endpoints_state(self.a1_r1, vpc_endpoint_id_list, state='deleted')

    @pytest.mark.tag_sec_confidentiality
    def test_T4473_with_valid_vpc_endpoint_id_with_other_account(self):
        try:
            ret = self.a1_r1.fcu.DescribeVpcEndpointServices()
            if not ret.response.serviceNameSet:
                pytest.skip('VpcEndpoints not supported on {}'.format(self.a1_r1.config.region.name))
            ret = self.a1_r1.fcu.CreateVpcEndpoint(VpcId=self.vpc_info[VPC_ID],
                                                   ServiceName='com.outscale.{}.api'.format(self.a1_r1.config.region.name))
            wait_vpc_endpoints_state(self.a1_r1, [ret.response.vpcEndpoint.vpcEndpointId], state='available')
            res = self.a2_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=[ret.response.vpcEndpoint.vpcEndpointId])
            assert res.status_code == 200
            assert res.response.unsuccessful[0].error.code == 'InvalidVpcEndpointId.NotFound'
            assert res.response.unsuccessful[0].error.message == "VPC Endpoint '{}' does not exist".format(ret.response.vpcEndpoint.vpcEndpointId)
        finally:
            self.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=[ret.response.vpcEndpoint.vpcEndpointId])
            wait_vpc_endpoints_state(self.a1_r1, [ret.response.vpcEndpoint.vpcEndpointId], state='deleted')
