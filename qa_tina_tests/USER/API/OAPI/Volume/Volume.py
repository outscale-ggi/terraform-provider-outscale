# -*- coding:utf-8 -*-


def validate_volume_response(volume, **kwargs):
    """
        int iops, 
        str az, 
        str volume_type, 
        str snapshot_id, 
        str volume_id,
        str state
        list(str, str) tags
    :param volume: 
    :param kwargs: 
    :volumeurn: 
    """
    assert volume.VolumeId.startswith('vol-')
    assert hasattr(volume, 'Size')
    assert hasattr(volume, 'State')
    assert hasattr(volume, 'VolumeType')
    assert hasattr(volume, 'Tags')
    assert hasattr(volume, 'SubregionName')
    assert hasattr(volume, 'LinkedVolumes')
    
    id = kwargs.get('volume_id')
    iops = kwargs.get('iops')
    az = kwargs.get('az')
    size = kwargs.get('size')
    volume_type = kwargs.get('volume_type')
    snapshot_id = kwargs.get('snapshot_id')
    state = kwargs.get('state')
    tags = kwargs.get('tags')
    linked_volumes = kwargs.get('linked_volumes')
    
    if id:
        assert volume.VolumeId == id
    if volume_type: 
        assert volume.VolumeType == volume_type
    if volume_type == 'io1':
        assert hasattr(volume, 'Iops')
    if iops:
        assert volume.Iops == iops
    if snapshot_id:
        assert volume.SnapshotId == snapshot_id
    if state:
        assert volume.State == state
    if az:
        assert volume.SubregionName == az
    if tags:
        assert len(volume.Tags) == len(tags)
        for tag in volume.Tags:
            assert (tag.Key, tag.Value) in tags
    if volume_type:
        assert volume.VolumeType == volume_type
    if linked_volumes:
        for link in volume.LinkedVolumes:
            for expected_link in linked_volumes:
                for k, v in expected_link.items():
                    assert getattr(link, k) == v, (
                        'In Main LinkedVolumes, {} is different of expected value {} for key {}'
                            .format(getattr(link, k), v, k))
    if size:
        assert volume.Size == size
