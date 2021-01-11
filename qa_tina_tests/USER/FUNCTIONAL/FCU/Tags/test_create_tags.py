import pytest

from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite, known_error
from qa_tina_tools.tools.tina.create_tools import create_vpc, create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_vpc
from qa_tina_tools.tools.tina.info_keys import SUBNETS, SUBNET_ID, VPC_ID, INSTANCE_ID_LIST, ROUTE_TABLE_ID
from qa_tina_tools.tools.tina.wait_tools import wait_images_state, wait_snapshots_state


class Test_create_tags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_create_tags, cls).setup_class()
        cls.tag = {'Key': 'Key', 'Value': 'Value'}
        cls.vpc_info1 = None
        cls.vpc_info2 = None
        cls.nat_gtw_id = None
        cls.vpc_peering_id = None
        cls.image_id = None
        cls.snapshot_id = None
        cls.vpc_endpoint_id = None
        cls.eip = cls.a1_r1.fcu.AllocateAddress(Domain='vpc').response
        try:
            cls.vpc_info1 = create_vpc(cls.a1_r1, nb_instance=1)
            cls.vpc_info2 = create_vpc(cls.a1_r1, nb_instance=1)
            ret = cls.a1_r1.fcu.CreateNatGateway(AllocationId=cls.eip.allocationId, SubnetId=cls.vpc_info1[SUBNETS][0][SUBNET_ID])
            cls.nat_gtw_id = ret.response.natGateway.natGatewayId
            ret = cls.a1_r1.fcu.CreateVpcPeeringConnection(VpcId=cls.vpc_info1[VPC_ID], PeerOwnerId=cls.a1_r1.config.account.account_id,
                                                           PeerVpcId=cls.vpc_info2[VPC_ID])
            cls.vpc_peering_id = ret.response.vpcPeeringConnection.vpcPeeringConnectionId
            ret = cls.a1_r1.fcu.CreateImage(InstanceId=cls.vpc_info1[SUBNETS][0][INSTANCE_ID_LIST][0], Name=id_generator(prefix='image_'))
            cls.image_id = ret.response.imageId
            wait_images_state(osc_sdk=cls.a1_r1, image_id_list=[cls.image_id], state='available')

            _, [cls.volume_id] = create_volumes(cls.a1_r1, state='available')
            ret = cls.a1_r1.fcu.CreateSnapshot(VolumeId=cls.volume_id, Name=id_generator(prefix='snapshot_'))
            cls.snapshot_id = ret.response.snapshotId
            wait_snapshots_state(osc_sdk=cls.a1_r1, snapshot_id_list=[cls.snapshot_id], state='completed')

            ret = cls.a1_r1.fcu.CreateVpcEndpoint(VpcId=cls.vpc_info1[VPC_ID], ServiceName='com.outscale.{}.api'.format(cls.a1_r1.config.region.name),
                                                  RouteTableId=cls.vpc_info1[ROUTE_TABLE_ID])
            cls.vpc_endpoint_id = ret.response.vpcEndpoint.vpcEndpointId
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vpc_endpoint_id:
                cls.a1_r1.fcu.DeleteVpcEndpoints(VpcEndpointId=[cls.vpc_endpoint_id])
            if cls.image_id:
                cls.a1_r1.fcu.DeregisterImage(ImageId=cls.image_id)
            if cls.snapshot_id:
                cls.a1_r1.fcu.DeleteSnapshot(SnapshotId=cls.snapshot_id)
            if cls.vpc_peering_id:
                cls.a1_r1.fcu.DeleteVpcPeeringConnection(VpcPeeringConnectionId=cls.vpc_peering_id)
            if cls.nat_gtw_id:
                cls.a1_r1.fcu.DeleteNatGateway(NatGatewayId=cls.nat_gtw_id)
            if cls.vpc_info1:
                delete_vpc(cls.a1_r1, cls.vpc_info1)
            if cls.vpc_info2:
                delete_vpc(cls.a1_r1, cls.vpc_info2)
        finally:
            super(Test_create_tags, cls).teardown_class()

    def create_tag(self, res_id):
        res_type_list = {'pcx': "vpc-peering-connection",
                         'nat': "natgateway",
                         'vpce': "vpc-endpoint",
                         'vpc': 'vpc',
                         'snap-export': "task",
                         'image-export': "task"
                        }
        self.a1_r1.fcu.CreateTags(ResourceId=[res_id], Tag=[self.tag])
        ret = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [res_id]}])
        assert len(ret.response.tagSet) == 1
        assert ret.response.tagSet[0].resourceId == res_id
        assert ret.response.tagSet[0].key == self.tag['Key']
        assert ret.response.tagSet[0].value == self.tag['Value']
        assert res_id.split('-')[0] in res_type_list
        try:
            assert ret.response.tagSet[0].resourceType == res_type_list[res_id.split('-')[0]]
            if res_id.split('-')[0] in ['vpce']:
                assert False, "Remove known error"
        except AssertionError:
            if res_id.split('-')[0] == 'vpce':
                known_error('TINA-5181', 'Wrong resourceType when DescribeTags on VPC Peering')
            else:
                raise
        # TODO: check Tag in call Describe<resource_type>(filter...)

    def test_T4139_nat_gateway(self):
        self.create_tag(self.nat_gtw_id)

    def test_T4141_vpc_peering_connection(self):
        self.create_tag(self.vpc_peering_id)

    def test_T1103_vpc(self):
        self.create_tag(self.vpc_info1[VPC_ID])

    @pytest.mark.region_synchro_osu
    @pytest.mark.region_osu
    def test_T4144_image_export_task(self):
        ret = self.a1_r1.fcu.CreateImageExportTask(ImageId=self.image_id,
                                                   ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test_image'})
        task_id = ret.response.imageExportTask.imageExportTaskId
        self.create_tag(task_id)

    @pytest.mark.region_synchro_osu
    @pytest.mark.region_osu
    def test_T4145_snapshot_export_task(self):
        ret = self.a1_r1.fcu.CreateSnapshotExportTask(SnapshotId=self.snapshot_id,
                                                      ExportToOsu={'DiskImageFormat': 'qcow2', 'OsuBucket': 'test_snapshot'})
        task_id = ret.response.snapshotExportTask.snapshotExportTaskId
        self.create_tag(task_id)

    def test_T4147_vpc_endpoint(self):
        self.create_tag(self.vpc_endpoint_id)
