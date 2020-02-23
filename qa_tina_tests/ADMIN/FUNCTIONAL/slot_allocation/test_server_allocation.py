from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances
import base64
from qa_tina_tools.tools.tina.delete_tools import delete_instances
from qa_common_tools.ssh import SshTools
from qa_tina_tools.tools.tina.info_keys import PATH, KEY_PAIR, INSTANCE_SET
from qa_common_tools.constants import CENTOS_USER
from osc_common.exceptions.osc_exceptions import OscApiException
from qa_common_tools.misc import assert_error

METADATA_PACEMENT = 'curl http://169.254.169.254/latest/meta-data/placement/'


class Test_server_allocation(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.inst_info = None
        super(Test_server_allocation, cls).setup_class()
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_server_strict=attractserver
            tags.osc.fcu.repulse_server_strict=repulseserver
            tags.osc.fcu.attract_cluster_strict=attractcluster
            tags.osc.fcu.repulse_cluster_strict=repulsecluster
            -----END OUTSCALE SECTION-----"""
        cls.userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            cls.inst_info = create_instances(cls.a1_r1, state='ready', user_data=cls.userdata)
            connection = SshTools.check_connection_paramiko(cls.inst_info[INSTANCE_SET][0]['ipAddress'], cls.inst_info[KEY_PAIR][PATH],
                                                            cls.a1_r1.config.region.get_info(CENTOS_USER))
            cls.server, _, _ = SshTools.exec_command_paramiko_2(connection, METADATA_PACEMENT + 'server')
            cls.cluster, _, _ = SshTools.exec_command_paramiko_2(connection, METADATA_PACEMENT + 'cluster')
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_info:
                delete_instances(cls.a1_r1, cls.inst_info)
        finally:
            super(Test_server_allocation, cls).teardown_class()

    def check_placement(self, ref_cluster, ref_server, inst_info, same_server, same_cluster):
        connection = SshTools.check_connection_paramiko(inst_info[INSTANCE_SET][0]['ipAddress'], inst_info[KEY_PAIR][PATH],
                                                        self.a1_r1.config.region.get_info(CENTOS_USER))
        server, _, _ = SshTools.exec_command_paramiko_2(connection, METADATA_PACEMENT + 'server')
        cluster, _, _ = SshTools.exec_command_paramiko_2(connection, METADATA_PACEMENT + 'cluster')
        # print('CHECK PLACEMENT {} {}'.format(same_cluster, same_server))
        # print('inst1 --> {} {}'.format(ref_cluster, ref_server))
        # print('inst2 --> {} {}'.format(cluster, server))
        assert same_cluster is None or (not same_cluster and cluster != ref_cluster) or (same_cluster and cluster == ref_cluster)
        assert same_server is None or (not same_server and server != ref_server) or (same_server and server == ref_server)
        return cluster, server

    def test_T4237_attract_server(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_server_strict=attractserver
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, True, True)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4238_repulse_server(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.repulse_server_strict=repulseserver
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, False, None)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4239_attract_cluster(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_cluster_strict=attractcluster
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, None, True)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4240_repulse_cluster(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.repulse_cluster_strict=repulsecluster
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, None, False)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4241_attract_repulse_same_server(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_server_strict=attractserver
            tags.osc.fcu.repulse_server_strict=repulseserver
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, False, None)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 500, 'InsufficientInstanceCapacity', 'Insufficient Capacity')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4242_attract_repulse_same_cluster(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_cluster_strict=attractcluster
            tags.osc.fcu.repulse_cluster_strict=repulsecluster
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, None, False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 500, 'InsufficientInstanceCapacity', 'Insufficient Capacity')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4243_attract_server_attract_cluster(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_server_strict=attractserver
            tags.osc.fcu.attract_cluster_strict=attractcluster
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, True, True)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4244_attract_server_repulse_cluster(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.attract_server_strict=attractserver
            tags.osc.fcu.repulse_cluster_strict=repulsecluster
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, True, False)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 500, 'InsufficientInstanceCapacity', 'Insufficient Capacity')
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4245_repulse_server_attract_cluster(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.repulse_server_strict=repulseserver
            tags.osc.fcu.attract_cluster_strict=attractcluster
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, False, True)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

    def test_T4246_repulse_server_repulse_cluster(self):
        inst_info = None
        userdata = """-----BEGIN OUTSCALE SECTION-----
            tags.osc.fcu.repulse_server_strict=repulseserver
            tags.osc.fcu.repulse_cluster_strict=repulsecluster
            -----END OUTSCALE SECTION-----"""
        userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
        try:
            inst_info = create_instances(self.a1_r1, state='ready', user_data=userdata)
            self.check_placement(self.cluster, self.server, inst_info, False, False)
        finally:
            if inst_info:
                delete_instances(self.a1_r1, inst_info)

#     def test_Txxx_repulse_server_twice(self):
#         inst_info1 = None
#         inst_info2 = None
#         userdata = """-----BEGIN OUTSCALE SECTION-----
#             tags.osc.fcu.repulse_server_strict=repulseserver
#             -----END OUTSCALE SECTION-----"""
#         userdata = base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
#         try:
#             inst_info1 = create_instances(self.a1_r1, state='ready', user_data=userdata)
#             cluster, server = self.check_placement(self.cluster, self.server, inst_info1, False, None)
#             inst_info2 = create_instances(self.a1_r1, state='ready', user_data=userdata)
#             self.check_placement(self.cluster, self.server, inst_info2, False, None)
#             self.check_placement(cluster, server, inst_info2, False, None)
#         finally:
#             if inst_info1:
#                 delete_instances(self.a1_r1, inst_info1)
#             if inst_info2:
#                 delete_instances(self.a1_r1, inst_info2)
