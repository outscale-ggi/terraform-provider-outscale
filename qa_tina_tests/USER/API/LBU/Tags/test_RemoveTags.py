from time import sleep

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_load_balancer
from qa_tina_tools.tools.tina.delete_tools import delete_lbu

class Test_RemoveTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_RemoveTags, cls).setup_class()
        cls.ret = None
        cls.lbu_name = id_generator(prefix='lbu-')
        try:
            cls.ret = create_load_balancer(cls.a1_r1, lb_name=cls.lbu_name, listeners=[
                {'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
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
            if cls.ret:
                # I KNOW, IT HURTS ON THE EYE! MAIS C'EST COMME ÇA
                sleep(60)
                delete_lbu(cls.a1_r1, cls.lbu_name)
        finally:
            super(Test_RemoveTags, cls).teardown_class()

    def test_T5431_valid_params(self):
        filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
        self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
        resp = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult
        assert resp.TagDescriptions[0].Tags is None

    def test_T5432_without_tag(self):
        try:
            self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter Tags')

    def test_T5433_without_lbu_name(self):
        ret = None
        filters = {}
        try:
            filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            self.a1_r1.lbu.RemoveTags(Tags=[filters])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')
        finally:
            if ret:
                self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])

    def test_T5434_with_invalid_tag(self):
        try:
            filters = {'toto': 'toto'}
            resp = self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            if resp.status_code == 200:
                known_error('TINA-', '')
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert False, 'Remove known error code'
            assert_error(err, 400, 'ValidationError', 'The request must contain the parameter LoadBalancerNames')

    def test_T5435_with_invalid_lbu_name(self):
        ret = None
        filters = {}
        try:
            filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            self.a1_r1.lbu.RemoveTags(LoadBalancerNames=['toto'], Tags=[filters])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', 'The specified load balancer does not exists.')
        finally:
            if ret:
                self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])

    def test_T5436_with_invalid_type_lbu_name(self):
        ret = None
        filters = {}
        try:
            filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            self.a1_r1.lbu.RemoveTags(LoadBalancerNames=self.lbu_name, Tags=[filters])
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'OWS.Error', 'Request is not valid.')
        finally:
            if ret:
                self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])

    def test_T5437_with_invalid_type_tag(self):
        ret = None
        filters = {}
        try:
            filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=filters)
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'OWS.Error', 'Request is not valid.')
        finally:
            if ret:
                self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])

    def test_T5438_with_multiple_tags(self):
        filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
        filters_2 = {'Key': id_generator("tagkey2-"), 'Value': id_generator("tagvalue2-")}
        self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters_2])
        self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters, filters_2])
        resp = self.a1_r1.lbu.DescribeTags(LoadBalancerNames=[self.lbu_name]).response.DescribeTagsResult
        assert resp.TagDescriptions[0].Tags is None

    def test_T5439_from_another_account(self):
        ret = None
        filters = {}
        try:
            filters = {'Key': id_generator("tagkey-"), 'Value': id_generator("tagvalue-")}
            ret = self.a1_r1.lbu.AddTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            self.a2_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
            assert False, "call should not have been successful"
        except OscApiException as err:
            assert_error(err, 400, 'LoadBalancerNotFound', "The specified load balancer does not exists.")
        finally:
            if ret:
                self.a1_r1.lbu.RemoveTags(LoadBalancerNames=[self.lbu_name], Tags=[filters])
