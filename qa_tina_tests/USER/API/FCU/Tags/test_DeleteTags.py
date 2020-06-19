from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error, get_export_value
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes


class Test_DeleteTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vol_id_list = None

        super(Test_DeleteTags, cls).setup_class()

        try:
            _, cls.vol_id_list = create_volumes(cls.a1_r1, count=3)

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.vol_id_list:
                delete_volumes(cls.a1_r1, cls.vol_id_list)
        finally:
            super(Test_DeleteTags, cls).teardown_class()

    def setup_method(self, method):
        OscTestSuite.setup_method(self, method)
        try:
            self.a1_r1.fcu.CreateTags(ResourceId=[self.vol_id_list[0]], Tag=[{'Value': 'value1', 'Key': 'key1'},
                                                                             {'Value': 'value1', 'Key': 'key2'},
                                                                             {'Value': '', 'Key': 'key3'}])
            self.a1_r1.fcu.CreateTags(ResourceId=[self.vol_id_list[1]], Tag=[{'Value': 'value1', 'Key': 'key1'},
                                                                             {'Value': 'value1', 'Key': 'key2'}])
            self.a1_r1.fcu.CreateTags(ResourceId=[self.vol_id_list[2]], Tag=[{'Value': 'value1', 'Key': 'key1'}])
        except OscApiException as error:
            try:
                self.teardown_method(method)
            except Exception:
                pass
            raise error

    def teardown_method(self, method):
        try:
            for tag in self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': self.vol_id_list}]).response.tagSet:
                self.a1_r1.fcu.DeleteTags(ResourceId=[tag.resourceId], Tag=[{'Key': tag.key, 'Value': tag.value}])
        finally:
            OscTestSuite.teardown_method(self, method)

    def check_vol_tags(self, data):
        for volId in data:
            tagSet = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [volId]}]).response.tagSet
            assert (not tagSet and len(data[volId]) == 0) or len(tagSet) == len(data[volId])
            if tagSet:
                keys = [tag.key for tag in tagSet]
                assert keys == data[volId]

    def test_T1781_missing_resource_id(self):
        try:
            self.a1_r1.fcu.DeleteTags(Tag=[{'Value': 'value1', 'Key': 'key1'}])
            assert False, 'Call should not have been successful, missing ResourceId'
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert_error(error, 400, 'MissingParameter', None)
                assert not error.message
                known_error('GTW-1360', 'Missing error message')
            assert_error(error, 400, 'MissingParameter', 'Parameter cannot be empty: ResourceID')

    def test_T1782_incorrect_type_resource_id(self):
        try:
            self.a1_r1.fcu.DeleteTags(ResourceId=self.vol_id_list[0], Tag=[{'Value': 'value1', 'Key': 'key1'}])
            self.check_vol_tags({self.vol_id_list[0]: ['key2', 'key3'], self.vol_id_list[1]: ['key1', 'key2'], self.vol_id_list[2]: ['key1']})
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert False, 'Remove known error code'
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert_error(error, 400, 'MissingParameter', None)
                assert not error.message
                known_error('GTW-1360', 'Unexpected failure')
            raise error

    def test_T1783_missing_tag(self):
        self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0]])
        self.check_vol_tags({self.vol_id_list[0]: [], self.vol_id_list[1]: ['key1', 'key2'], self.vol_id_list[2]: ['key1']})

    def test_T1784_incorrect_type_tag(self):
        try:
            self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0]], Tag={'Value': 'value1', 'Key': 'key1'})
            assert False, 'Call should not have been successful, incorrect tag type'
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert_error(error, 500, 'InternalError', None)
                assert not error.message
                known_error('GTW-1360', 'Unexpected internal error')
            assert_error(error, 400, 'InvalidParameterValue', "Value for parameter \'Tag\' is invalid: {\'Key\': \'key1\', \'Value\': \'value1\'}")

    def test_T1785_missing_tag_key(self):
        try:
            self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0]], Tag=[{'Value': 'value1'}])
            self.check_vol_tags({self.vol_id_list[0]: ['key1', 'key2', 'key3'], self.vol_id_list[1]: ['key1', 'key2'], self.vol_id_list[2]: ['key1']})
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert False, 'Remove known error code'
        except OscApiException as error:
            if get_export_value('OSC_USE_GATEWAY', default_value=False):
                assert_error(error, 400, 'InvalidParameterValue', None)
                assert not error.message
                known_error('GTW-1360', 'Unexpected failure')
            raise error

    def test_T1786_missing_tag_value(self):
        self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0]], Tag=[{'Key': 'key1'}])
        self.check_vol_tags({self.vol_id_list[0]: ['key2', 'key3'], self.vol_id_list[1]: ['key1', 'key2'], self.vol_id_list[2]: ['key1']})

    def test_T1787_empty_tag_value(self):
        self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0]], Tag=[{'Value': None, 'Key': 'key3'}])
        self.check_vol_tags({self.vol_id_list[0]: ['key1', 'key2'], self.vol_id_list[1]: ['key1', 'key2'], self.vol_id_list[2]: ['key1']})

    def test_T1788_single_resource_single_tag(self):
        self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0]], Tag=[{'Key': 'key1', 'Value': 'value1'}])
        self.check_vol_tags({self.vol_id_list[0]: ['key2', 'key3'], self.vol_id_list[1]: ['key1', 'key2'], self.vol_id_list[2]: ['key1']})

    def test_T1789_multi_resource_single_tag(self):
        self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0], self.vol_id_list[1]], Tag=[{'Key': 'key2', 'Value': 'value1'}])
        self.check_vol_tags({self.vol_id_list[0]: ['key1', 'key3'], self.vol_id_list[1]: ['key1'], self.vol_id_list[2]: ['key1']})

    def test_T1790_single_resource_multi_tag(self):
        self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0]], Tag=[{'Key': 'key1', 'Value': 'value1'},
                                                                         {'Key': 'key2', 'Value': 'value1'}])
        self.check_vol_tags({self.vol_id_list[0]: ['key3'], self.vol_id_list[1]: ['key1', 'key2'], self.vol_id_list[2]: ['key1']})

    def test_T1791_multi_resource_multi_tag(self):
        self.a1_r1.fcu.DeleteTags(ResourceId=[self.vol_id_list[0], self.vol_id_list[1]], Tag=[{'Key': 'key1', 'Value': 'value1'},
                                                                                              {'Key': 'key2', 'Value': 'value1'}])
        self.check_vol_tags({self.vol_id_list[0]: ['key3'], self.vol_id_list[1]: [], self.vol_id_list[2]: ['key1']})
