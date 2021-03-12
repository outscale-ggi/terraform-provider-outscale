import random
import string

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error, id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_instances, create_vpc
from qa_tina_tools.tools.tina.delete_tools import delete_instances, delete_vpc
from qa_tina_tools.tools.tina.info_keys import INSTANCE_ID_LIST, SUBNETS, SUBNET_ID
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_test_tools.config.configuration import Configuration


class Test_DisassociateAddress(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        cls.inst_info_2 = None
        cls.net_id = None
        cls.vpc_info = None
        cls.vpc_eips = None
        try:
            super(Test_DisassociateAddress, cls).setup_class()
            cls.vpc_info = create_vpc(cls.a1_r1, nb_instance=1, nb_subnet=1, no_eip=True)
            cls.inst_info_2 = create_instances(cls.a1_r1, nb=1)
            cls.inst_info = create_instances(cls.a1_r1, nb=1, state='running')
            cls.net_id = cls.a1_r1.fcu.CreateNetworkInterface(SubnetId=cls.vpc_info[SUBNETS][0][SUBNET_ID]).response.networkInterface
            cls.standard_eips = cls.a1_r1.fcu.AllocateAddress(Domain='standard').response
            cls.vpc_eips = cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.net_id:
                cls.a1_r1.fcu.DeleteNetworkInterface(NetworkInterfaceId=cls.net_id.networkInterfaceId)
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
            if cls.vpc_info:
                delete_vpc(cls.a1_r1, cls.vpc_info)
            if cls.standard_eips:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.standard_eips.publicIp)
            if cls.vpc_eips:
                cls.a1_r1.fcu.ReleaseAddress(PublicIp=cls.vpc_eips.publicIp)
            if cls.inst_info_2:
                delete_instances(cls.a1_r1, cls.inst_info_2)
        finally:
            super(Test_DisassociateAddress, cls).teardown_class()

    def test_T4067_valid_public_ip(self):
        try:
            self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips.publicIp)
            self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips.publicIp)
        except Exception as error:
            raise error

    def test_T114_with_valid_association_id(self):
        try:
            ret = self.a1_r1.fcu.AssociateAddress(NetworkInterfaceId=self.net_id.networkInterfaceId, AllocationId=self.vpc_eips.allocationId)
            self.a1_r1.fcu.DisassociateAddress(AssociationId=ret.response.associationId)
        except Exception as error:
            raise error

    def test_T4053_with_incorrect_association_id(self):
        assoc_id = id_generator("eipasso-99", 6, chars=(string.hexdigits).lower())
        try:
            self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'InvalidIpAssociationID.Malformed', "Invalid ID received: {}. Expected format: eipassoc-".format(assoc_id))

    def test_T335_with_invalid_association_id(self):
        assoc_id = id_generator("eipassoc-99", 6, chars=(string.hexdigits).lower())
        try:
            self.a1_r1.fcu.DisassociateAddress(AssociationId=assoc_id)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'InvalidAssociationID.NotFound', "The association ID does not exist: {}".format(assoc_id))

    def test_T4054_with_association_id_and_with_another_account(self):
        try:
            ret = self.a1_r1.fcu.AssociateAddress(NetworkInterfaceId=self.net_id.networkInterfaceId, AllocationId=self.vpc_eips.allocationId)
            self.a2_r1.fcu.DisassociateAddress(AssociationId=ret.response.associationId)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'InvalidAssociationID.NotFound', "The association ID does not exist: {}".format(ret.response.associationId))

    def test_T4055_none_association(self):
        try:
            self.a1_r1.fcu.DisassociateAddress(AssociationId=None)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'OWS.Error':
                known_error('TINA-4988', "Incorrect error code")
            else:
                assert False, 'remove known error code'
                assert_error(error, 400, '', '')

    def test_T4056_empty_association_id(self):
        try:
            self.a1_r1.fcu.DisassociateAddress(AssociationId='')
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'MissingParameter', "Insufficient parameters provided out of: Ip, association. Expected at least: 1")

    def test_T4057_without_params(self):
        try:
            self.a1_r1.fcu.DisassociateAddress()
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'OWS.Error':
                known_error('TINA-4988', "Incorrect error code")
            else:
                assert False, 'remove known error code'
                assert_error(error, 400, '', '')

    def test_T4058_empty_public_ip(self):
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp='')
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'MissingParameter', "Insufficient parameters provided out of: Ip, association. Expected at least: 1")

    def test_T4059_none_public_ip(self):
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=None)
            assert False, "Call shouldn't be successful"
        except OscApiException as error:
            if error.status_code == 400 and error.error_code == 'OWS.Error':
                known_error('TINA-4988', "Incorrect error code")
            else:
                assert False, 'remove known error code'
                assert_error(error, 400, '', '')

    def test_T4060_local_host_as_public_ip(self):
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp="127.0.0.1")
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'AuthFailure', "The address '127.0.0.1' does not belong to you.")

    def test_T4061_private_ip_classe_a_as_public_ip(self):
        public_ip = '10.{}.{}.{}'.format(*random.sample(list(range(1, 254)), 3))
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=public_ip)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'AuthFailure', "The address '{}' does not belong to you.".format(public_ip))

    def test_T4062_private_ip_classe_b_as_public_ip(self):
        public_ip = '172.{}.{}.{}'.format(*random.sample(list(range(16, 31)), 1), *random.sample(list(range(1, 254)), 2))
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=public_ip)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'AuthFailure', "The address '{}' does not belong to you.".format(public_ip))

    def test_T4063_private_ip_classe_c_as_public_ip(self):
        public_ip = '192.168.{}.{}'.format(*random.sample(list(range(1, 254)), 2))
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=public_ip)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'AuthFailure', "The address '{}' does not belong to you.".format(public_ip))

    def test_T4064_invalid_public_ip(self):
        ip_address = Configuration.get('ipaddress', '0_0_0_0')
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=ip_address)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'AuthFailure', "The address '{}' does not belong to you.".format(ip_address))

    def test_T4065_incorrect_syntaxe_public_ip(self):
        public_ip = '{}.{}'.format(*random.sample(list(range(256, 999)), 2))
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=public_ip)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid IPv4 address: {}".format(public_ip))

    def test_T4066_out_of_range_public_ip(self):
        public_ip = '{}.{}.{}.{}'.format(*random.sample(list(range(256, 999)), 4))
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=public_ip)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'InvalidParameterValue', "Invalid IPv4 address: {}".format(public_ip))

    def test_T4068_non_existent_public_ip(self):
        public_ip = '{}.{}.{}.{}'.format(*random.sample(list(range(193, 240)), 4))
        try:
            self.a1_r1.fcu.DisassociateAddress(PublicIp=public_ip)
            assert False, "Call shouldn't be successful"
        except Exception as error:
            assert_error(error, 400, 'AuthFailure', "The address '{}' does not belong to you.".format(public_ip))

    def test_T320_reassociate_address(self):
        self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips.publicIp)
        self.a1_r1.fcu.DisassociateAddress(PublicIp=self.standard_eips.publicIp)
        wait_instances_state(self.a1_r1, [self.inst_info_2[INSTANCE_ID_LIST][0]], "running")
        self.a1_r1.fcu.AssociateAddress(InstanceId=self.inst_info_2[INSTANCE_ID_LIST][0], PublicIp=self.standard_eips.publicIp)
