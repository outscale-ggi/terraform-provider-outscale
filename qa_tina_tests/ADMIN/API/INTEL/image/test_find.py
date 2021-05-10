from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tools.tina import info_keys
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_instances, create_image
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old


class Test_find(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_find, cls).setup_class()
        cls.inst_id = None
        cls.image_id1 = None
        cls.image_id2 = None
        cls.image_id3 = None

        cls.inst_info = create_instances(cls.a1_r1)
        cls.inst_id = cls.inst_info[info_keys.INSTANCE_ID_LIST][0]
        _, cls.image_id1 = create_image(cls.a1_r1, cls.inst_id, state='available')
        _, cls.image_id2 = create_image(cls.a1_r1, cls.inst_id, state='available')
        _, cls.image_id3 = create_image(cls.a1_r1, cls.inst_id, state='available')
        cls.a1_r1.fcu.CreateTags(ResourceId=cls.image_id1, Tag=[{'Key': 'key1', 'Value': 'value1'}])
        cls.a1_r1.fcu.CreateTags(ResourceId=cls.image_id2, Tag=[{'Key': 'key1', 'Value': 'value2'}])
        cls.a1_r1.fcu.CreateTags(ResourceId=cls.image_id3, Tag=[{'Key': 'key2', 'Value': 'value2'}])

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_id:
                delete_instances_old(cls.a1_r1, [cls.inst_id])
            if cls.image_id1:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image_id1], force=True)
            if cls.image_id2:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image_id2], force=True)
            if cls.image_id3:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image_id3], force=True)
        except Exception as error:
            cls.logger.exception(error)
        finally:
            super(Test_find, cls).teardown_class()

    def test_T5571_with_valid_tags(self):
        ret = self.a1_r1.intel.image.find(tags={'key1': 'value1'})
        assert len(ret.response.result) == 1

    def test_T5572_with_key(self):
        ret = self.a1_r1.intel.image.find(tags={'key1': None})
        assert len(ret.response.result) == 2

    def test_T5574_with_inexistant_value(self):
        ret = self.a1_r1.intel.image.find(tags={'image': 'xxxx'})
        assert len(ret.response.result) == 0

    def test_T5575_with_inexistant_key(self):
        ret = self.a1_r1.intel.image.find(tags={'xxxx': ['image1']})
        assert len(ret.response.result) == 0

    def test_T5576_with_empty_tags(self):
        ret = self.a1_r1.intel.image.find(tags={})
        assert len(ret.response.result) != 0
