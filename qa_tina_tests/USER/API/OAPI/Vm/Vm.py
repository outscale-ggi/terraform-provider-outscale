# -*- coding:utf-8 -*-
from qa_tina_tools.tools.tina.wait_tools import wait_instances_state
from qa_test_tools.config import config_constants as constants


def create_vms(ocs_sdk, image_id=None, state='running', VmType=None, **kwargs):
    if not image_id:
        image_id = ocs_sdk.config.region.get_info(constants.CENTOS7)
    if VmType:
        ret_value = ocs_sdk.oapi.CreateVms(ImageId=image_id, VmType=VmType, **kwargs)
    else:
        ret_value = ocs_sdk.oapi.CreateVms(ImageId=image_id, **kwargs)
    vm_id_list = [vm.VmId for vm in ret_value.response.Vms]
    if state:
        try:
            wait_instances_state(ocs_sdk, vm_id_list, state=state)
        except Exception as error:
            ocs_sdk.oapi.StopVms(VmIds=vm_id_list, ForceStop=True)
            ocs_sdk.oapi.DeleteVms(VmIds=vm_id_list)
            wait_instances_state(ocs_sdk, vm_id_list, state='terminated')
            raise error
    return ret_value, vm_id_list


def validate_vm_response(vm, **kwargs):
    """
    :param vm:
    :param kwargs:
        dict() expected_vm - {'key':'value'} (all following value will potentially working)
                str Architecture
                bool BsuOptimized
                str ClientToken
                str Hypervisor
                str ImageId
                bool IsSourceDestChecked
                str KeypairName
                int LaunchNumber
                str PrivateDnsName
                str PrivateIp
                str PublicDnsName
                str PublicIp
                str RootDeviceName
                str RootDeviceType
                str State
                str StateReason
                str VmType
            list(dict()) bdm
                str DeviceName
                dict() Bsu
                    bool DeleteOnVmDeletion
                    str State
                    bool VolumeId - just check startwith 'vol-' - just VolumeId
            list(dict()) sgs
                str SecurityGroupId
                str SecurityGroupName
            list(dict()) nic
                str SubnetId
                str NetId
            dict() placement
                str SubregionName
                str Tenancy
            list(str, str) tags
    :return:
    """
    assert vm.VmId.startswith('i-')
    expected_vm = kwargs.get('expected_vm')
    if expected_vm:
        for k, v in expected_vm.items():
            if k == 'PrivateDnsName' or k == 'PublicDnsName':
                assert v in getattr(vm, k)
            else:
                assert hasattr(vm, k) and v is None or getattr(vm, k) == v, (
                    'In Main Vm, {} is different of expected value {} for key {}'.format(getattr(vm, k), v, k))
    bdms = kwargs.get('bdm', [])
    for exp_bdm in bdms:
        for vm_bdm in vm.BlockDeviceMappings:
            if vm_bdm.DeviceName == exp_bdm['DeviceName']:
                for k, v in exp_bdm.get('Bsu', {}).items():
                    if k == 'VolumeId':
                        assert getattr(vm_bdm.Bsu, k).startswith('vol-')
                    else:
                        assert getattr(vm_bdm.Bsu, k) == v, (
                            'In BlockDeviceMapping, {} is different of expected value {} for key {}'
                            .format(getattr(vm_bdm.Bsu, k), v, k))
            else:
                pass
    nics = kwargs.get('nic', [])
    for nic in nics:
        local_nic_id = None
        if 'NicId' in nic:
            local_nic_id = nic['NicId']
        found_nic = False
        for vm_nic in vm.Nics:
            assert getattr(vm_nic, 'NicId').startswith('eni-')
            if local_nic_id and vm_nic.NicId != local_nic_id:
                continue
            if 'NicId' in nic:
                assert nic['NicId'] == vm_nic.NicId, 'Incorrect nicid'
            for k, v in nic.items():
                if k == 'NicId':
                    continue
                elif k == 'PrivateIps':
                    validate_private_ips_response(vm_nic.PrivateIps, v)
                elif k == 'LinkNic':
                    assert v.get('DeviceNumber') in range(8)
                    assert vm_nic.LinkNic.LinkNicId.startswith('eni-attach')
                #    break
                elif k in ['SubnetId', 'NetId']:
                    assert getattr(vm_nic, k) == v, ('In Vms[].Nics, {} is different of expected value {} for key {}'
                                                          .format(getattr(vm_nic, k), v, k))
                else:
                    assert False, 'Incorrect nic specification, unknown property {}'.format(k)
            found_nic = True
            break
        assert found_nic
    placement = kwargs.get('placement')
    if placement:
        for k, v in placement.items():
            assert getattr(vm.Placement, k) == v
    sgs = kwargs.get('sgs', [])
    for sg in sgs:
        for vm_sg in vm.SecurityGroups:
            for k, v in sg.items():
                assert getattr(vm_sg, k) == v
    tags = kwargs.get('tags')
    if tags:
        assert len(vm.Tags) == len(tags)
        for tag in vm.Tags:
            assert (tag.Key, tag.Value) in tags


def validate_vms_state_response(vm, **kwargs):
    state = kwargs.get('state')
    if state:
        for k, v in state.items():
            assert getattr(vm, k) == v, ('In Vms[].State, {} is different of expected value {} for key {}'
                                         .format(getattr(state, k), v, k))


def validate_private_ips_response(private_ips, expected_private_ips):
    for private_ip in private_ips:
        for epi in expected_private_ips:
            if private_ip.PrivateIp == epi['PrivateIp']:
                for k, v in epi.items():
                    assert getattr(private_ip, k) == v, (
                        'In Vms[].Nics[].PrivateIps, {} is different of expected value {} for key {}'
                        .format(getattr(private_ips, k), v, k))
