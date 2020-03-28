from qa_common_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina.create_tools import create_volumes
from qa_tina_tools.tools.tina.delete_tools import delete_volumes
from qa_common_tools.misc import id_generator, assert_error
import string
from osc_common.exceptions.osc_exceptions import OscApiException


class Test_CreateTags(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.vol_id_list = None
        super(Test_CreateTags, cls).setup_class()
        try:
            _, cls.vol_id_list = create_volumes(cls.a1_r1)
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
            super(Test_CreateTags, cls).teardown_class()

    def test_T1774_no_value(self):
        try:
            self.a1_r1.fcu.CreateTags(ResourceId=self.vol_id_list, Tag=[{'Key': 'key1774'}])
        finally:
            self.a1_r1.fcu.DeleteTags(ResourceId=self.vol_id_list, Tag=[{'Key': 'key1774'}])

    def test_T1775_empty_key(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.CreateTags(ResourceId=self.vol_id_list, Tag=[{'Key': '', 'Value': 'value1'}])
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': self.vol_id_list}]).response.tagSet
            assert isinstance(resp, list) and len(resp) == 1
            assert resp[0].resourceId == self.vol_id_list[0]
            assert resp[0].resourceType == 'volume'
            assert resp[0].value == 'value1'
            assert resp[0].key == 'None'
        finally:
            if ret:
                self.a1_r1.fcu.DeleteTags(ResourceId=self.vol_id_list, Tag=[{'Key': '', 'Value': 'value1'}])

    def test_T1776_empty_value(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.CreateTags(ResourceId=self.vol_id_list, Tag=[{'Key': 'key1776', 'Value': ''}])
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': self.vol_id_list}]).response.tagSet
            assert isinstance(resp, list) and len(resp) == 1
            assert resp[0].key == 'key1776'
            assert resp[0].resourceId == self.vol_id_list[0]
            assert resp[0].resourceType == 'volume'
            assert resp[0].value is None
        finally:
            if ret:
                self.a1_r1.fcu.DeleteTags(ResourceId=self.vol_id_list, Tag=[{'Key': 'key1776', 'Value': ''}])

    def test_T1773_no_key(self):
        self.a1_r1.fcu.CreateTags(ResourceId=self.vol_id_list, Tag=[{'Value': 'value1'}])
        self.a1_r1.fcu.DeleteTags(ResourceId=self.vol_id_list, Tag=[{'Value': 'value1'}])

    def test_T1109_vol_special_character_value(self):
        key = id_generator(prefix='key', size=4, chars=string.digits)
        self.a1_r1.fcu.CreateTags(ResourceId=self.vol_id_list, Tag=[{'Key': key, 'Value': '@&é"(§è!çà)-$^`ù=:;,<#°_¨*%£/+.?>'}])
        self.a1_r1.fcu.DeleteTags(ResourceId=self.vol_id_list, Tag=[{'Key': key, 'Value': '@&é"(§è!çà)-$^`ù=:;,<#°_¨*%£/+.?>'}])

    def test_T1110_vol_special_character_key(self):
        value = id_generator(prefix='value', size=4, chars=string.digits)
        self.a1_r1.fcu.CreateTags(ResourceId=self.vol_id_list, Tag=[{'Key': '@&é"(§è!çà)-$^`ù=:;,<#°_¨*%£/+.?>', 'Value': value}])
        self.a1_r1.fcu.DeleteTags(ResourceId=self.vol_id_list, Tag=[{'Key': '@&é"(§è!çà)-$^`ù=:;,<#°_¨*%£/+.?>', 'Value': value}])

    def test_T1094_invalid_tag(self):
        try:
            self.a1_r1.fcu.CreateTags(ResourceId=self.vol_id_list, Tag=['Key', 'key_value'])
            assert False, "Call shouln't be successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", "Value for parameter \'Tag\' is invalid: {\'1\': \'Key\', \'2\': \'key_value\'}")
