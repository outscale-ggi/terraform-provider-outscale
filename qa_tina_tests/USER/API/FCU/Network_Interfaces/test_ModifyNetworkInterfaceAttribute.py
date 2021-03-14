from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tina.check_tools import check_obj_equal
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_security_group
from qa_tina_tools.tools.tina.delete_tools import delete_vpc, delete_security_group
from qa_tina_tools.tools.tina.info_keys import VPC_ID, SECURITY_GROUP_ID, SUBNETS


class Test_ModifyNetworkInterfaceAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.sg_pub_name = id_generator(prefix='sgnpub-')
        cls.sg_priv_name = id_generator(prefix='sgpriv-')
        cls.vpc_info = None
        cls.ni = None
        super(Test_ModifyNetworkInterfaceAttribute, cls).setup_class()
        try:
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=1)
            cls.net_int = cls.a1_r1.fcu.DescribeNetworkInterfaces(Filter=[{'Name': 'vpc-id',
                                                                      'Value': [cls.vpc_info[VPC_ID]]}]).response.networkInterfaceSet[0]
            cls.sg_pub_id = create_security_group(cls.a1_r1, cls.sg_pub_name, cls.sg_pub_name)
            cls.sg_priv_id = create_security_group(cls.a1_r1, cls.sg_priv_name, cls.sg_priv_name, cls.vpc_info[VPC_ID])
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.sg_pub_id:
                delete_security_group(cls.a1_r1, cls.sg_pub_id)
            if cls.sg_priv_id:
                delete_security_group(cls.a1_r1, cls.sg_priv_id)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
        finally:
            super(Test_ModifyNetworkInterfaceAttribute, cls).teardown_class()

    def test_T1954_missing_ni_id(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(Description={'Value': 'description'})
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: NetworkInterfaceId')

    def test_T1955_unknown_ni_id(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId='eni-12345678', Description={'Value': 'description'})
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidNetworkInterfaceID.NotFound', "The networkInterface ID 'eni-12345678' does not exist")

    def test_T1956_incorrect_ni_id(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId='xxx-12345678', Description={'Value': 'description'})
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidNetworkInterfaceID.Malformed', 'Invalid ID received: xxx-12345678. Expected format: eni-')

    def test_T1957_incorrect_type_ni_id(self):
        ni_id = self.net_int.networkInterfaceId
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=[ni_id], Description={'Value': 'description'})
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterType',
                         "Value of parameter 'NetworkInterfaceID' must be of type: string. Received: {'1': '" + ni_id + "'}")

    def test_T1958_incorrect_type_description(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, Description='description')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            if error.status_code == 500:
                known_error('TINA-4521', 'Internal error on incorrect param type')
            assert False, 'Remove known error code'
            assert_error(error, 400, 'xxx', 'xxx')

    def test_T1959_incorrect_type_attachment(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, Attachment='AttachmentId')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            if error.status_code == 500:
                known_error('TINA-4521', 'Internal error on incorrect param type')
            assert False, 'Remove known error code'
            assert_error(error, 400, 'xxx', 'xxx')

    def test_T1960_empty_sg_ids(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, SecurityGroupId=[])
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination', 'No attributes specified.')

    def test_T1961_unknown_sg_ids(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, SecurityGroupId=['sg-12345678'])
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group 'sg-12345678' does not exist.")

    def test_T1962_incorrect_sg_ids(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, SecurityGroupId=['xxx-12345678'])
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidSecurityGroupID.Malformed', 'Invalid ID received: xxx-12345678. Expected format: sg-')

    def test_T1963_incorrect_type_sg_ids(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId,
                                                           SecurityGroupId={'SecurityGroupId': self.vpc_info[SUBNETS][0][SECURITY_GROUP_ID]})
            known_error('TINA-4521', 'Call with incorrect param has been successful')
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, 'xxx', 'xxx')

    def test_T1968_pub_sg_id(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, SecurityGroupId=[self.sg_pub_id])
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.NotFound', "The security group '" + self.sg_pub_id + "' does not exist in this VPC.")

    def test_T1964_missing_change(self):
        try:
            self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId)
            assert False, 'call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterCombination', 'No attributes specified.')

    def test_T1965_modify_description(self):
        self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, Description={'Value': 'description'})
        net_int = self.a1_r1.fcu.DescribeNetworkInterfaces(NetworkInterfaceId=[self.net_int.networkInterfaceId]).response.networkInterfaceSet[0]
        assert check_obj_equal(net_int, self.net_int, attr=['description'], attr_value=['description'], no_compare=['description'])

    def test_T1966_modify_attachment(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId,
                                                                 Attachment={'AttachmentId': self.net_int.attachment.attachmentId,
                                                                             'DeleteOnTermination': False})
            net_int = self.a1_r1.fcu.DescribeNetworkInterfaces(NetworkInterfaceId=[self.net_int.networkInterfaceId]).response.networkInterfaceSet[0]
            assert check_obj_equal(net_int, self.net_int, no_compare=['description', 'attachment'])
            assert net_int.attachment.deleteOnTermination == 'false'
        finally:
            if ret:
                self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId,
                                                               Attachment={'AttachmentId': self.net_int.attachment.attachmentId,
                                                                           'DeleteOnTermination': True})

    def test_T1967_modify_security_group(self):
        current_sg_id = self.net_int.groupSet[0].groupId
        try:
            ret = self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId,
                                                                 SecurityGroupId=[self.sg_priv_id])
            net_int = self.a1_r1.fcu.DescribeNetworkInterfaces(NetworkInterfaceId=[self.net_int.networkInterfaceId]).response.networkInterfaceSet[0]
            assert check_obj_equal(net_int, self.net_int, no_compare=['description', 'attachment', 'groupSet'])
            assert net_int.groupSet[0].groupId == self.sg_priv_id
        finally:
            if ret:
                self.a1_r1.fcu.ModifyNetworkInterfaceAttribute(NetworkInterfaceId=self.net_int.networkInterfaceId, SecurityGroupId=[current_sg_id])
