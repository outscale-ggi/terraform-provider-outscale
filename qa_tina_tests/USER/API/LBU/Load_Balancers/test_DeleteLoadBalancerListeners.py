from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_load_balancer, create_self_signed_cert
from qa_tina_tools.tools.tina.wait_tools import wait_load_balancer_state
from qa_tina_tools.tools.tina.delete_tools import delete_lbu
from qa_test_tools.misc import id_generator
import os
import pytest


class Test_DeleteLoadBalancerListeners(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DeleteLoadBalancerListeners, cls).setup_class()
        try:
            pass
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            pass
        finally:
            super(Test_DeleteLoadBalancerListeners, cls).teardown_class()

    def test_T4007_with_ssl_listener(self):
        ret_lbu = None
        ret_up = None
        ports = [25, 443, 465, 587, 2222]
        # ports = [2222]
        lbu_name = id_generator(prefix='lbu-')
        crtpath = None
        keypath = None
        try:
            crtpath, keypath = create_self_signed_cert()
            key = open(keypath).read()
            cert = open(crtpath).read()
            ret_up = self.a1_r1.eim.UploadServerCertificate(ServerCertificateName=id_generator(prefix='cc-'), CertificateBody=cert, PrivateKey=key)
            arn = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.Arn
            name = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.ServerCertificateName
            # cert_id = ret.response.UploadServerCertificateResult.ServerCertificateMetadata.ServerCertificateId
            ret_lbu = create_load_balancer(self.a1_r1, lbu_name, listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                           availability_zones=[self.a1_r1.config.region.az_name])
            for port in ports:
                self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=lbu_name,
                                                           Listeners=[{'InstancePort': port, 'Protocol': 'SSL', 'LoadBalancerPort': port,
                                                                       'SSLCertificateId': arn}])
            wait_load_balancer_state(self.a1_r1, [lbu_name])
            self.a1_r1.lbu.DeleteLoadBalancerListeners(LoadBalancerName=lbu_name, LoadBalancerPorts=ports)
        # for debug
        except OscApiException as err:
            raise err
        finally:
            if ret_lbu:
                try:
                    delete_lbu(self.a1_r1, lbu_name)
                except:
                    pass
            if ret_up:
                try:
                    self.a1_r1.eim.DeleteServerCertificate(ServerCertificateName=name)
                except:
                    pass
            if crtpath:
                os.remove(crtpath)
            if keypath:
                os.remove(keypath)

    def test_T4008_with_http_listener(self):
        ret_lbu = None
        ports = [25, 443, 465, 587, 2222]
        # ports = [2222]
        lbu_name = id_generator(prefix='lbu-')
        try:
            ret_lbu = create_load_balancer(self.a1_r1, lbu_name,
                                           listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                           availability_zones=[self.a1_r1.config.region.az_name])
            wait_load_balancer_state(self.a1_r1, [lbu_name])
            for port in ports:
                self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=lbu_name,
                                                           Listeners=[{'InstancePort': port, 'Protocol': 'HTTP', 'LoadBalancerPort': port}])
            self.a1_r1.lbu.DeleteLoadBalancerListeners(LoadBalancerName=lbu_name, LoadBalancerPorts=ports)
        # for debug
        except OscApiException as err:
            raise err
        finally:
            if ret_lbu:
                try:
                    delete_lbu(self.a1_r1, lbu_name)
                except:
                    pass

    def test_T4009_with_tcp_listener(self):
        ret_lbu = None
        ports = [25, 443, 465, 587, 2222]
        # ports = [2222]
        lbu_name = id_generator(prefix='lbu-')
        try:
            ret_lbu = create_load_balancer(self.a1_r1, lbu_name,
                                           listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                           availability_zones=[self.a1_r1.config.region.az_name])
            for port in ports:
                self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=lbu_name,
                                                           Listeners=[{'InstancePort': port, 'Protocol': 'TCP', 'LoadBalancerPort': port}])
            wait_load_balancer_state(self.a1_r1, [lbu_name])
            self.a1_r1.lbu.DeleteLoadBalancerListeners(LoadBalancerName=lbu_name, LoadBalancerPorts=ports)
        # for debug
        except OscApiException as err:
            raise err
        finally:
            if ret_lbu:
                try:
                    delete_lbu(self.a1_r1, lbu_name)
                except:
                    pass

    def test_T4010_with_https_listener(self):
        ret_lbu = None
        ret_up = None
        ports = [25, 443, 465, 587, 2222]
        # ports = [2222]
        lbu_name = id_generator(prefix='lbu-')
        crtpath = None
        keypath = None
        try:
            crtpath, keypath = create_self_signed_cert()
            key = open(keypath).read()
            cert = open(crtpath).read()
            ret_up = self.a1_r1.eim.UploadServerCertificate(ServerCertificateName=id_generator(prefix='cc-'), CertificateBody=cert, PrivateKey=key)
            arn = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.Arn
            name = ret_up.response.UploadServerCertificateResult.ServerCertificateMetadata.ServerCertificateName
            # cert_id = ret.response.UploadServerCertificateResult.ServerCertificateMetadata.ServerCertificateId
            ret_lbu = create_load_balancer(self.a1_r1, lbu_name,
                                           listeners=[{'InstancePort': 65535, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                           availability_zones=[self.a1_r1.config.region.az_name])
            wait_load_balancer_state(self.a1_r1, [lbu_name])
            for port in ports:
                self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=lbu_name,
                                                           Listeners=[{'InstancePort': port, 'Protocol': 'HTTPS', 'LoadBalancerPort': port,
                                                                       'SSLCertificateId': arn}])
            self.a1_r1.lbu.DeleteLoadBalancerListeners(LoadBalancerName=lbu_name, LoadBalancerPorts=ports)
        # for debug
        except OscApiException as err:
            raise err
        finally:
            if ret_lbu:
                try:
                    delete_lbu(self.a1_r1, lbu_name)
                except:
                    pass
            if ret_up:
                try:
                    self.a1_r1.eim.DeleteServerCertificate(ServerCertificateName=name)
                except:
                    pass
            if crtpath:
                os.remove(crtpath)
            if keypath:
                os.remove(keypath)

    @pytest.mark.tag_sec_confidentiality
    def test_T4171_with_other_account(self):
        lbu_name1 = id_generator(prefix='lbu-')
        lbu_name2 = id_generator(prefix='lbu-')
        lbu_name3 = id_generator(prefix='lbu-')
        lbu_names = [lbu_name1, lbu_name2]
        try:
            for lbuname in lbu_names:
                create_load_balancer(self.a1_r1, lbuname, listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                     availability_zones=[self.a1_r1.config.region.az_name])
            create_load_balancer(self.a2_r1, lbu_name3, listeners=[{'InstancePort': 80, 'Protocol': 'HTTP', 'LoadBalancerPort': 80}],
                                 availability_zones=[self.a1_r1.config.region.az_name])
            wait_load_balancer_state(self.a1_r1, [lbu_name1, lbu_name2])
            wait_load_balancer_state(self.a2_r1, [lbu_name3])
            self.a1_r1.lbu.DeleteLoadBalancerListeners(LoadBalancerName=lbu_names[0], LoadBalancerPorts=[80])
            ret = self.a1_r1.lbu.DescribeLoadBalancers(LoadBalancerNames=[lbu_names[1]])
            assert ret.response.DescribeLoadBalancersResult.LoadBalancerDescriptions[0].ListenerDescriptions
            ret = self.a2_r1.lbu.DescribeLoadBalancers(LoadBalancerNames=[lbu_name3])
            assert ret.response.DescribeLoadBalancersResult.LoadBalancerDescriptions[0].ListenerDescriptions
        except OscApiException as err:
            raise err
        finally:
            try:
                for lbuname in lbu_names:
                    delete_lbu(self.a1_r1, lbuname)
                delete_lbu(self.a2_r1, lbu_name3)
            except:
                pass

    def test_T4312_with_udp_listener(self):
        ret_lbu = None
        ports = [25, 443, 465, 587, 2222]
        # ports = [2222]
        lbu_name = id_generator(prefix='lbu-')
        try:
            ret_lbu = create_load_balancer(self.a1_r1, lbu_name,
                                           listeners=[{'InstancePort': 65535, 'Protocol': 'UDP', 'LoadBalancerPort': 80}],
                                           availability_zones=[self.a1_r1.config.region.az_name])
            for port in ports:
                self.a1_r1.lbu.CreateLoadBalancerListeners(LoadBalancerName=lbu_name,
                                                           Listeners=[{'InstancePort': port, 'Protocol': 'UDP', 'LoadBalancerPort': port}])
            wait_load_balancer_state(self.a1_r1, [lbu_name])
            self.a1_r1.lbu.DeleteLoadBalancerListeners(LoadBalancerName=lbu_name, LoadBalancerPorts=ports)
        # for debug
        except OscApiException as err:
            raise err
        finally:
            if ret_lbu:
                try:
                    delete_lbu(self.a1_r1, lbu_name)
                except:
                    pass
