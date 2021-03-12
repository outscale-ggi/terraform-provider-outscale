
import pytest

from qa_common_tools.ssh import SshTools
from qa_test_tools.test_base import OscTestSuite


VMS = ['in2-pr-intel-lbu-1']
DEPENDENCIES = {'SQLAlchemy': '1.2', 'alembic': '0.8.10', 'Jinja2': '2.7.3', 'pytz': '2016.7'}

DEFAULT_VALUE = 'xxxxx'


class Test_Lbu_Services(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_Lbu_Services, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_Lbu_Services, cls).teardown_class()

    # Note: the prefix test_ was eared to avoid having it marked as automated
    def test_T232_lbu_python_dependencies(self):

        key_ssh = DEFAULT_VALUE
        user_name = DEFAULT_VALUE
        passphrase = DEFAULT_VALUE
        if key_ssh == DEFAULT_VALUE:
            pytest.skip("Test can only be executed with user specific items (user name, ssh key and pass phrase)")

        inter = 'in2-adm'
        sshclient = None
        try:
            sshclient = SshTools.check_connection_paramiko(ip_address=inter, ssh_key=key_ssh, username=user_name, password=passphrase)
            for inst in VMS:

                sshclient_jhost = SshTools.check_connection_paramiko_nested(sshclient=sshclient,
                                                                            ip_address=inst,
                                                                            ssh_key=key_ssh,
                                                                            local_private_addr=inter,
                                                                            dest_private_addr=inst,
                                                                            username=user_name,
                                                                            password=passphrase)
                for key, value in list(DEPENDENCIES.items()):
                    cmd = "source /usr/local/outscale/virtualenv/bin/activate \n pip freeze | grep {}".format(key)
                    out, status, _ = SshTools.exec_command_paramiko(sshclient_jhost, cmd)
                    assert not status
                    assert value in out

        except AssertionError as _:
            self.logger("Dependency for key %s expected %s but was %s", key, value, out)
        finally:
            if sshclient:
                sshclient.close()
