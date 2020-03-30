from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu


class Test_DescribeLoadBalancers(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribeLoadBalancers, cls).setup_class()
        cls.ret1 = None
        cls.ret2 = None
        cls.ret3 = None
        try:
            cls.ret1 = create_load_balancer(cls.a1_r1, 'lbu1', listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
            cls.ret2 = create_load_balancer(cls.a1_r1, 'lbu2', listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
            cls.ret3 = create_load_balancer(cls.a1_r1, 'lbu3', listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                            availability_zones=[cls.a1_r1.config.region.az_name])
        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.ret1:
                delete_lbu(cls.a1_r1, 'lbu1')
            if cls.ret2:
                delete_lbu(cls.a1_r1, 'lbu2')
            if cls.ret3:
                delete_lbu(cls.a1_r1, 'lbu3')
        finally:
            super(Test_DescribeLoadBalancers, cls).teardown_class()

    def test_T1265_without_param(self):
        self.a1_r1.lbu.DescribeLoadBalancers()

    def test_T1267_with_valid_lb_names(self):
        self.a1_r1.lbu.DescribeLoadBalancers(LoadBalancerNames=['lbu1'])
        self.a1_r1.lbu.DescribeLoadBalancers(LoadBalancerNames=['lbu1', 'lbu2'])

    def test_T1266_with_invalid_lb_names(self):
        try:
            self.a1_r1.lbu.DescribeLoadBalancers(LoadBalancerNames=['toto'])
            assert False, "call should not have been successful, need valid load balancer name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "There is no ACTIVE Load Balancer named 'toto'"
        try:
            self.a1_r1.lbu.DescribeLoadBalancers(LoadBalancerNames=['lbu1', 'toto'])
            assert False, "call should not have been successful, need valid load balancer name"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "There is no ACTIVE Load Balancer named 'toto'"

    def test_T1268_with_valid_page_size(self):
        self.a1_r1.lbu.DescribeLoadBalancers(PageSize=1)
        self.a1_r1.lbu.DescribeLoadBalancers(PageSize=2)
        self.a1_r1.lbu.DescribeLoadBalancers(PageSize=4)

    def test_T1269_with_invalid_page_size(self):
        try:
            self.a1_r1.lbu.DescribeLoadBalancers(PageSize='toto')
            assert False, "call should not have been successful, need valid value for page size"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "Request is not valid."
        try:
            self.a1_r1.lbu.DescribeLoadBalancers(PageSize=-1)
            assert False, "call should not have been successful, need valid value for page size"
        except OscApiException as err:
            assert err.status_code == 400
            assert err.message == "1 validation error detected: Value '-1' at 'pageSize' failed to satisfy constraint: \
Member must have value greater than or equal to 1"

    def test_T1271_with_valid_marker(self):
        ret = self.a1_r1.lbu.DescribeLoadBalancers(PageSize=1)
        marker_1 = ret.response.DescribeLoadBalancersResult.NextMarker
        ret = self.a1_r1.lbu.DescribeLoadBalancers(Marker=marker_1)
        assert len(ret.response.DescribeLoadBalancersResult.LoadBalancerDescriptions) == 2
        ret = self.a1_r1.lbu.DescribeLoadBalancers(PageSize=2)
        marker_2 = ret.response.DescribeLoadBalancersResult.NextMarker
        ret = self.a1_r1.lbu.DescribeLoadBalancers(Marker=marker_2)
        assert len(ret.response.DescribeLoadBalancersResult.LoadBalancerDescriptions) == 1
        ret = self.a1_r1.lbu.DescribeLoadBalancers(Marker=marker_1, PageSize=1)
        assert len(ret.response.DescribeLoadBalancersResult.LoadBalancerDescriptions) == 1

    def test_T1270_with_invalid_marker(self):
        try:
            self.a1_r1.lbu.DescribeLoadBalancers(Marker='toto')
            assert False, "call should not have been successful, need valid Marker param"
        except OscApiException as err:
            assert err.status_code == 400

    def test_T1272_with_all_valid_param(self):
        ret = self.a1_r1.lbu.DescribeLoadBalancers(PageSize=1)
        marker_1 = ret.response.DescribeLoadBalancersResult.NextMarker
        ret = self.a1_r1.lbu.DescribeLoadBalancers(Marker=marker_1, PageSize=1, LoadBalancerNames=['lbu1'])
        assert len(ret.response.DescribeLoadBalancersResult.LoadBalancerDescriptions) == 1
