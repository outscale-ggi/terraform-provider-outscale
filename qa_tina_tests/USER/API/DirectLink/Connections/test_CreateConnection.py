
import pytest

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from specs.check_tools import check_directlink_error


@pytest.mark.region_directlink
class Test_CreateConnection(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 1, 'dl_interface_limit': 1}
        super(Test_CreateConnection, cls).setup_class()
        cls.known_error = False
        try:
            ret = cls.a1_r1.directlink.DescribeLocations()
            if cls.a1_r1.config.region.name == 'in-west-2':
                if len(ret.response.locations) == 0:
                    cls.known_error = True
                    return
                assert False, 'remove known error'
            cls.location = ret.response.locations[0].locationCode

        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        super(Test_CreateConnection, cls).teardown_class()

    def test_T1908_required_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        conn_id = None
        connection_name = misc.id_generator(prefix='dl_')
        try:
            ret = self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps', connectionName=connection_name)
            conn_id = ret.response.connectionId
            assert ret.response.bandwidth == '1Gbps'
            assert ret.response.connectionName == connection_name
            assert ret.response.connectionState == 'requested'
            assert ret.response.location == self.location
            assert ret.response.ownerAccount == self.a1_r1.config.account.account_id
            assert ret.response.region == self.a1_r1.config.region.name
            assert ret.response.connectionId.startswith('dxcon-')
        finally:
            if conn_id:
                self.a1_r1.directlink.DeleteConnection(connectionId=conn_id)

    def test_T4467_without_bandwidth(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a1_r1.directlink.CreateConnection(location=self.location, connectionName=misc.id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 7000, missing_parameters='bandwidth')

    def test_T4468_without_name(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 7000, missing_parameters='connectionName')

    def test_T4469_without_location(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a1_r1.directlink.CreateConnection(bandwidth='1Gbps', connectionName=misc.id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 7000, missing_parameters='location')

    def test_T4470_with_invalid_bandwidth(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='foo', connectionName=misc.id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 4129, param='Speed', value='foo', options='10Gbps, 1Gbps')

    def test_T4471_with_invalid_location(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        try:
            self.a1_r1.directlink.CreateConnection(location='foo', bandwidth='1Gbps', connectionName=misc.id_generator(prefix='dl_'))
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            check_directlink_error(error, 5052, id='foo')

    def test_T5733_with_extra_param(self):
        if self.known_error:
            known_error('OPS-14319', 'NEW IN2 : no Directlink on in2')
        conn_id = None
        connection_name = misc.id_generator(prefix='dl_')
        try:
            ret = self.a1_r1.directlink.CreateConnection(location=self.location, bandwidth='1Gbps', connectionName=connection_name, Foo='Bar')
            conn_id = ret.response.connectionId
        finally:
            if conn_id:
                self.a1_r1.directlink.DeleteConnection(connectionId=conn_id)
