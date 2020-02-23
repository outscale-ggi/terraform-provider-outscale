
from qa_common_tools.config.configuration import Configuration
from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_instances_old, create_keypair
from qa_tina_tools.tools.tina.delete_tools import delete_keypair
from qa_tina_tools.tina.info_keys import NAME
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state


class Test_linux_instance(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_linux_instance, cls).setup_class()
        cls.sg_name = id_generator(prefix='sg_')
        cls.sg_name_vpc = id_generator(prefix='sg_vpc_')
        IP_Ingress = Configuration.get('cidr', 'allips')
        cls.kp_info = None
        cls.sg_id = None
        try:
            # create security group
            sg_response = cls.a1_r1.fcu.CreateSecurityGroup(GroupDescription='test_sg_description', GroupName=cls.sg_name)
            cls.sg_id = sg_response.response.groupId
            # authorize rules
            cls.a1_r1.fcu.AuthorizeSecurityGroupIngress(GroupId=cls.sg_id, IpProtocol='tcp', FromPort=22, ToPort=22, CidrIp=IP_Ingress)
            # create keypair
            cls.kp_info = create_keypair(cls.a1_r1)
        except Exception as error:
            cls.teardown_class()
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.kp_info:
                delete_keypair(cls.a1_r1, cls.kp_info)
            if cls.sg_id:
                cls.a1_r1.fcu.DeleteSecurityGroup(GroupId=cls.sg_id)
        finally:
            super(Test_linux_instance, cls).teardown_class()

    def create_instance(self, Instance_Type=None, dedicated=False, subnet=None, BlockDeviceMapping=None, security_group_id=None, placement=None):
        public_ip_inst = None
        inst_id_list = None
        if security_group_id is None:
            security_group_id = self.sg_id
        if dedicated:
            _, inst_id_list = create_instances_old(self.a1_r1, security_group_id_list=[security_group_id], key_name=self.kp_info[NAME],
                                                   inst_type=Instance_Type, placement={'Tenancy': 'dedicated'})
        else:
            _, inst_id_list = create_instances_old(self.a1_r1, security_group_id_list=[security_group_id], key_name=self.kp_info[NAME],
                                                   inst_type=Instance_Type, subnet_id=subnet, bdm=BlockDeviceMapping, placement=placement)
        # get instance ID
        inst_id = inst_id_list[0]
        # wait instance to become ready check for login page
        ret_wait_state = wait_instances_state(osc_sdk=self.a1_r1, instance_id_list=[inst_id], state='ready')
        if subnet:
            ret = self.a1_r1.fcu.AssociateAddress(AllocationId=self.eip_allo_id, InstanceId=inst_id)
            ret.response.display()
            public_ip_inst = self.eip.response.publicIp
        else:
            # get public IP
            public_ip_inst = ret_wait_state.response.reservationSet[0].instancesSet[0].ipAddress
        return inst_id, public_ip_inst
