import os

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools.compare_objects import verify_response
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite


class Test_DescribePrefixLists(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_DescribePrefixLists, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_DescribePrefixLists, cls).teardown_class()

    def test_Txxx_no_param(self):
        resp = self.a1_r1.fcu.DescribePrefixLists().response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_Txxx_with_params(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter="pl-dcbd245b",
                                                  MaxResults=432,
                                                  NextToken="fjv",
                                                  PrefixListId=["pl-dcbd245b"]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_Txxx_with_filter_by_valid_name(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter="com.outscale.in-west-1.fcu").response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_Txxx_with_filter_by_invalid_name(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter="gvzesvdcsd").response
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "",
                                     "".format())

    def test_Txxx_with_filter_by_valid_value(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=["pl-8a30327d"]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_Txxx_with_filter_by_invalid_value(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter=["vbkhebzkbv"]).response
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "",
                                     "".format())

    def test_Txxx_with_valid_maxresults(self,):
        resp = self.a1_r1.fcu.DescribePrefixLists(MaxResults=15).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_Txxx_with_invalid_max_results_max(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(MaxResults=3243).response
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "",
                                     "".format())

    def test_Txxx_with_invalid_max_results_min(self):
        try:
            resp = self.a1_r1.fcu.DescribePrefixLists(MaxResults=2).response
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "",
                                     "".format())

    def test_Txxx_with_valid_next_token(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(NextToken="vsed").response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_Txxx_with_invalid_next_token(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(NextToken="vrbfdsv").response
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "",
                                     "".format())

    def test_Txxx_valid_prefixlistid(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(PrefixListId=["pl-e07ba6f8"]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_Txxx_empty_prefixlistid(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(PrefixListId=[]).response
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidPrefixListId.NotFound",
                                     "The Prefix List Id does not exist")

    def test_Txxx_invalid_prefixlistid(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(PrefixListId="tcut").response
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidPrefixListId.NotFound",
                                     "The Prefix List Id {} does not exist".format("tcut"))