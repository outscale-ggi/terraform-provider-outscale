
import pytest

from qa_common_tools.test_base import OscTestSuite
from qa_common_tools.ssh import SshTools


VMS = ['in2-pr-intel-main-1', 'in2-pr-intel-main-2', 'in2-pr-intel-main-3', 'in2-pr-intel-main-cron-1']
DEPENDENCIES = {'SQLAlchemy': '1.2', 'alembic': '0.8.10', 'amqp': '2.2.2', 'circus': '0.14.0',
                'cryptography': '1.7.1', 'elasticsearch': '5.0.1', 'futures': '3.0.5', 'iso8601': '0.1.10',
                'Jinja2': '2.7.3', 'netaddr': '0.7.18', 'psycopg2': '2.7.1',
                'pycrypto': '2.6', 'python-consul': '0.7.0', 'python-dateutil': '2.2', 'pytz': '2016.7',
                'simplejson': '3.3.0', 'uWSGI': '2.0.13.1', 'Werkzeug': '0.11.10'}

DEFAULT_VALUE = 'xxxxx'


class Test_Intel_Services(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_Intel_Services, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_Intel_Services, cls).teardown_class()

    # Note: the prefix test_ was eared to avoid having it marked as automated
    def T228_Intel_python_dependencies(self):

        key_ssh = DEFAULT_VALUE
        user_name = DEFAULT_VALUE
        passphrase = DEFAULT_VALUE
        if key_ssh == DEFAULT_VALUE:
            pytest.skip("Test can only be executed with user specific items (user name, ssh key and pass phrase)")

        inter = 'in2-adm'
        sshclient = None
        try:
            sshclient = SshTools.check_connection_paramiko(ip_address=inter, ssh_key=key_ssh, username=user_name, password=passphrase)
            for vm in VMS:

                sshclient_jhost = SshTools.check_connection_paramiko_nested(sshclient=sshclient,
                                                                            ip_address=vm,
                                                                            ssh_key=key_ssh,
                                                                            local_private_addr=inter,
                                                                            dest_private_addr=vm,
                                                                            username=user_name,
                                                                            password=passphrase)
                for key, value in list(DEPENDENCIES.items()):
                    cmd = "source /usr/local/outscale/virtualenv/bin/activate \n pip freeze | grep {}".format(key)
                    out, status, _ = SshTools.exec_command_paramiko_2(sshclient_jhost, cmd)
                    assert not status
                    assert value in out

        except AssertionError as _:
            self.logger.info("Dependency for key {} expected {} but was {}".format(key, value, out))
        finally:
            if sshclient:
                sshclient.close()
