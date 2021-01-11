# pylint: disable=missing-docstring

#import pytest

from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.base import StreamingBase


#from qa_tina_tests.ADMIN.FUNCTIONAL.streaming.utils import get_streaming_operation, wait_streaming_state, get_data_file_chain
#@pytest.mark.region_admin
#@pytest.mark.tag_qemu
class Test_example(StreamingBase):
    pass
    #@classmethod
    #def setup_class(cls):
    #    #self.w_size = 10
    #    #self.v_size = 10
    #    #self.qemu_version = '2.12'
    #    #self.inst_type = 'c4.large'
    #    #self.vol_type = 'standard'
    #    #self.iops = None
    #    #self.base_snap_id = 10
    #    #self.new_snap_count = 1 # > 1
    #    #self.branch_id = 0 # [0, new_snap_count-1]
    #    #self.fio = False
    #    super(Test_stream_example, cls).setup_class()

    #def setup_method(self, method):
    #    super(Test_stream_example, self).setup_method(method)
    #    try:
    #        pass
    #    except:
    #        try:
    #            self.teardown_method(method)
    #        except:
    #            pass
    #        raise

    #def teardown_method(self, method):
    #    try:
    #        pass
    #    finally:
    #        super(Test_stream_example, self).teardown_method(method)

    #def test_T0000_example(self):
        ## list data file before streaming
        #ret = get_data_file_chain(self.a1_r1, self.vol_1_id)
        #self.logger.debug(ret)
        ## start streaming
        #self.a1_r1.intel.streaming.start(resource_id=self.vol_1_id)
        ## display streaming task
        #ret = get_streaming_operation(self.a1_r1, self.vol_1_id)
        #self.logger.debug(ret.response.display())
        ## wait streaming
        #wait_streaming_state(self.a1_r1, self.vol_1_id, cleanup=True)
        ## list data file after streaming
        #ret = get_data_file_chain(self.a1_r1, self.vol_1_id)
        #self.logger.debug(ret)
