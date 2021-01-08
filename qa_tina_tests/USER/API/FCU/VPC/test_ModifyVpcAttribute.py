import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import VPC_ID


class Test_ModifyVpcAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ModifyVpcAttribute, cls).setup_class()
        cls.vpc_id = None
        cls.vpc_info = None
        try:
            cls.vpc_info = create_vpc(cls.a1_r1)
            cls.vpc_id = cls.vpc_info[VPC_ID]
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
            super(Test_ModifyVpcAttribute, cls).teardown_class()

    def test_T1258_without_param(self):
        try:
            self.a1_r1.fcu.ModifyVpcAttribute()
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "OWS.Error", "Request is not valid.")

    def test_T1259_with_invalid_vpc_id(self):
        vpcId = (id_generator(prefix='vpc-', size=10, chars=string.hexdigits)).lower()
        try:
            self.a1_r1.fcu.ModifyVpcAttribute(VpcId=vpcId)
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "OWS.Error", "Request is not valid.")

    def test_T1260_with_valid_vpc_id(self):
        try:
            self.a1_r1.fcu.ModifyVpcAttribute(VpcId=self.vpc_id)
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "OWS.Error", "Request is not valid.")

    def test_T1261_with_dns_support(self):
        self.a1_r1.fcu.ModifyVpcAttribute(VpcId=self.vpc_id, EnableDnsSupport={'Value': True})

    def test_T1262_with_dns_hostname(self):
        self.a1_r1.fcu.ModifyVpcAttribute(VpcId=self.vpc_id, EnableDnsHostnames={'Value': True})

    def test_T1263_with_dns_support_and_hostname(self):
        self.a1_r1.fcu.ModifyVpcAttribute(VpcId=self.vpc_id, EnableDnsSupport={'Value': True}, EnableDnsHostnames={'Value': True})

    def test_T1264_with_valid_attribute_and_invalid_vpc_id(self):
        vpcId = id_generator(size=10, chars=string.ascii_lowercase)
        try:
            self.a1_r1.fcu.ModifyVpcAttribute(VpcId=vpcId, EnableDnsSupport={'Value': True}, EnableDnsHostnames={'Value': True})
            assert False, "Call shouldn't successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidVpcID.NotFound", "The vpc ID '{}' does not exist".format(vpcId))

    def test_T4175_with_dns_support_false(self):
        try:
            self.a1_r1.fcu.ModifyVpcAttribute(VpcId=self.vpc_id, EnableDnsSupport={'Value': False})
        except OscApiException as error:
            assert_error(error, 400, "UnsupportedOperation", "enableDnsSupport can only be set to 'true'.")
