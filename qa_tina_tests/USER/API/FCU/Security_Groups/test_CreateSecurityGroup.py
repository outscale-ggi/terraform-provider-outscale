# -*- coding: utf-8 -*-

import re
import string
import pytest
from qa_test_tools.config.configuration import Configuration
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_vpcs


class Test_CreateSecurityGroup(OscTestSuite):
    """
        check that from a set of regions
        the others set regions are not available
    """

    @classmethod
    def setup_class(cls):
        super(Test_CreateSecurityGroup, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateSecurityGroup, cls).teardown_class()

    def test_T963_default(self):
        """
        :return:
        """
        sg_name = id_generator(prefix='qa')
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
            sg_id = ret.response.groupId
            assert re.search(r"(sg-[a-zA-Z0-9]{8})", ret.response.groupId)
            assert ret.response.osc_return == 'true'
            assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", ret.response.requestId)
        finally:
            if sg_id:
                self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)

    def test_T964_same_name(self):
        sg_name = id_generator(prefix='qa')
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
            sg_id = ret.response.groupId
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
            assert False, 'Duplicate security group name should have failed.'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.Duplicate', "The security group '{}' already exists".format(sg_name))
            assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", error.request_id)
        finally:
            try:
                self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
            except Exception:
                pytest.fail("An error happened deleting resources in the test")

    def test_T965_same_name_different_description(self):
        sg_name = id_generator(prefix='qa')
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
            sg_id = ret.response.groupId
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description1', GroupName=sg_name)
            assert False, 'Duplicate security group name should have failed.'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidGroup.Duplicate', "The security group '{}' already exists".format(sg_name))
            assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", error.request_id)
            assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", error.request_id)
        finally:
            try:
                self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
            except Exception:
                pytest.fail("An error happened deleting resources in the test")

    def test_T966_no_name_without_parameter(self):
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description')
            assert False, 'Missing security group name should have failed.'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter GroupName')
            assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", error.request_id)

    def test_T967_no_name_with_parameter(self):
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName='')
            assert False, 'Missing security group name should have failed.'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter GroupName')
            assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", error.request_id)

    def test_T968_no_description_with_parameter(self):
        sg_name = id_generator(prefix='qa')
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='', GroupName=sg_name)
            assert False, 'Missing security group description should have failed.'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter GroupDescription')
            assert re.search(r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{8})", error.request_id)

    def test_T969_no_description_without_parameter(self):
        sg_name = id_generator(prefix='qa')
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupName=sg_name)
            assert False, 'Missing security group description should have failed.'
        except OscApiException as error:
            assert_error(error, 400, 'MissingParameter', 'The request must contain the parameter GroupDescription')

    def test_T970_name_too_long(self):
        sg_name = id_generator(size=256)
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
            assert False, 'Too long security group name should have failed.'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidParameterValue'

    def test_T971_description_too_long(self):
        sg_desc = id_generator(size=300)
        sg_name = id_generator(size=10)
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name)
            assert False, 'Too long security group description should have failed.'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value for parameter 'GroupDescription' is invalid: {}. Max length allowed: 255".format(sg_desc))

    def test_T972_name_max_length(self):
        sg_name = id_generator(size=255)
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name)
            sg_id = ret.response.groupId
        finally:
            try:
                self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
            except Exception:
                pytest.fail("An error happened deleting resources in the test")

    def test_T973_description_max_length(self):
        sg_desc = id_generator(size=255)
        sg_name = id_generator(size=10)
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name)
            sg_id = ret.response.groupId
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pytest.fail("An error happened deleting resources in the test")

    def test_T974_name_allowed_characters(self):
        sg_desc = id_generator(size=10)
        sg_name = string.digits + string.ascii_letters + ' ._-:/()#,@[]+=&;{}!$*'
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name)
            sg_id = ret.response.groupId
        except OscApiException as error:
            raise error
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pytest.fail("An error happened deleting resources in the test")

    def test_T975_description_allowed_characters(self):
        sg_desc = string.digits + string.ascii_letters + ' ._-:/()#,@[]+=&;{}!$*'
        sg_name = id_generator(size=10)
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name)
            sg_id = ret.response.groupId
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pytest.fail("An error happened deleting resources in the test")

    def test_T976_special_characters_vpc_not_allowed(self):
        sg_name = "àé"
        vpc_id = None
        try:
            vpc_id = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16')).response.vpc.vpcId
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=id_generator(size=10), GroupName=sg_name, VpcId=vpc_id)

        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         'GroupName is invalid. Valid values are: a-z, A-Z, 0-9, spaces and _.-:/()#,@[]+=&;{}!$*')
        finally:
            if vpc_id:
                cleanup_vpcs(self.a1_r1, vpc_id_list=[vpc_id])

    def test_T1768_in_vpc_special_a(self):
        sg_name = "àààààààààà"
        vpc_id = None
        try:
            vpc_id = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16')).response.vpc.vpcId
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=id_generator(size=10), GroupName=sg_name, VpcId=vpc_id)

        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         'GroupName is invalid. Valid values are: a-z, A-Z, 0-9, spaces and _.-:/()#,@[]+=&;{}!$*')
        finally:
            if vpc_id:
                cleanup_vpcs(self.a1_r1, vpc_id_list=[vpc_id])

    def test_T1769_in_vpc_special_e(self):
        sg_name = "éééééééééé"
        vpc_id = None
        try:
            vpc_id = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16')).response.vpc.vpcId
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=id_generator(size=10), GroupName=sg_name, VpcId=vpc_id)
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         'GroupName is invalid. Valid values are: a-z, A-Z, 0-9, spaces and _.-:/()#,@[]+=&;{}!$*')
        finally:
            if vpc_id:
                cleanup_vpcs(self.a1_r1, vpc_id_list=[vpc_id])

    def test_T977_special_characters_vpc(self):
        string_vpc = string.ascii_uppercase + string.ascii_lowercase + "._-:/()#,@[]+=&;{}!$*"
        sg_desc = id_generator(size=10)
        sg_name = string_vpc
        sg_id = None
        vpc_id = None
        try:
            ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name, VpcId=vpc_id)
            sg_id = ret.response.groupId
        finally:
            error = False
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    error = True
            if vpc_id:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
                except Exception:
                    error = True
            if error:
                pytest.fail("An error happened deleting resources in the test")

    def test_T978_special_characters_public_sg_not_allowed(self):
        sg_desc = id_generator(size=255)
        sg_name = 'àé'
        sg_id = None
        try:
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name)
            sg_id = ret.response.groupId
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         'GroupName is invalid. Valid values are: a-z, A-Z, 0-9, spaces and _.-:/()#,@[]+=&;{}!$*')
        finally:
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    pytest.fail("An error happened deleting resources in the test")

    def test_T979_valid_vpc_id(self):
        """
        :return:
        """
        sg_name = id_generator(prefix='qa')
        sg_id = None
        vpc_id = None
        try:
            ret = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = ret.response.vpc.vpcId
            ret = self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=sg_name, VpcId=vpc_id)
            sg_id = ret.response.groupId
        finally:
            error = False
            if sg_id:
                try:
                    self.a1_r1.fcu.DeleteSecurityGroup(GroupId=sg_id)
                except Exception:
                    error = True
            if vpc_id:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
                except Exception:
                    error = True
            if error:
                pytest.fail("An error happened deleting resources in the test")

    def test_T980_invalid_vpc_id(self):
        sg_desc = id_generator(size=10)
        sg_name = id_generator(size=10)
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name, VpcId='foo')
            assert False, 'Security group invalid vpc id should have failed.'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidVpcID.Malformed'

#     def test_T000_non_ascii_characters_public_sg(self):
#         pytest.skip('non testable')
#
#     # TODO:implement when IN1 is available
#     def test_T000_with_id_from_another_account(self):
#         pytest.skip('TO BE DEFINED')

    def test_T1392_with_valid_vpc_id_non_existing(self):
        vpc_id = 'vpc-12345678'
        sg_desc = id_generator(size=10)
        sg_name = id_generator(size=10)
        try:
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription=sg_desc, GroupName=sg_name, VpcId=vpc_id)
            assert False, 'Security group invalid vpc id should have failed.'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidVpcID.NotFound'

    def test_T1393_with_long_vpc_id(self):
        vpc_id = None
        try:
            vpc = self.a1_r1.fcu.CreateVpc(CidrBlock=Configuration.get('vpc', '10_0_0_0_16'))
            vpc_id = vpc.response.vpc.vpcId
            vpc_id_error = '{}xxx{}'.format(vpc_id[:4], vpc_id[-8:])
            self.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName='test_sg', VpcId=vpc_id_error)
            assert False, 'Security group invalid vpc id should have failed.'
        except OscApiException as error:
            assert error.status_code == 400
            assert error.error_code == 'InvalidVpcID.Malformed'
        finally:
            if vpc_id:
                try:
                    self.a1_r1.fcu.DeleteVpc(VpcId=vpc_id)
                except Exception:
                    pytest.fail("An error happened deleting resources in the test")
