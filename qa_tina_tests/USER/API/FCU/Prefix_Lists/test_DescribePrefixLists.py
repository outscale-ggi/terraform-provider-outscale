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

    def test_T5686_no_param(self):
        resp = self.a1_r1.fcu.DescribePrefixLists().response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'read_no_param.json'), None)

    def test_T5687_with_filter_prefix_id_list(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-id", "Value":["pl-dcbd245b"]}]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_filter_prefix_id_list.json'), None)

    def test_T5688_with_filter_prefix_name_list(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-name",
                                                           "Value":["com.outscale.in-west-1.fcu"]}]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_filter_prefix_name_list.json'), None)

    def test_T5689_with_prefix_list_ids(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(PrefixListId=["pl-dcbd245b"]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_prefix_list_ids.json'), None)

    def test_T5690_with_valid_next_token(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(MaxResults=5).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_max_result.json'), None)
        resp = self.a1_r1.fcu.DescribePrefixLists(NextToken=resp.nextToken).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_next_token.json'), None)

    def test_T5691_with_invalid_next_token(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(NextToken="foobar")
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidNextToken.Malformed", "Invalid value for 'NextToken': foobar")

    def test_T5692_with_invalid_type_next_token(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(NextToken={"foo": "bar"})
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter NextToken.foo")

    def test_T5693_with_filter_empty_prefix_name_list(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-name", "Value":[]}]).response
        assert not resp.prefixListSet
        #assert False, "call should not have been successful"

    def test_T5694_with_filter_empty_prefix_id_list(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-id", "Value":[]}]).response
        assert not resp.prefixListSet
        #assert False, "call should not have been successful"

    def test_T5695_with_filter_unknown_prefix_name_list(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-name", "Value":["tdiyfiy"]}]).response
        assert not resp.prefixListSet
        #assert False, "call should not have been successful"

    def test_T5696_with_filter_unknown_prefix_id_list(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-id", "Value":["hg-cescqz"]}]).response
        assert not resp.prefixListSet
        #assert False, "call should not have been successful"

    def test_T5697_with_filter_invalid_type_prefix_name_list(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-name",
                                                        "Value":[["com.outscale.in-west-1.fcu"]]}])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter Filter.1.Value.1.1")

    def test_T5698_with_filter_invalid_type_prefix_id_list(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-id", "Value":[["pl-dcbd245b"]]}])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter Filter.1.Value.1.1")

    def test_T5699_with_max_results_out_of_range(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(MaxResults=4).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_max_results_out_of_range.json'), None)

    def test_T5700_with_invalid_type_max_results(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(MaxResults={"foo": "bar"})
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter MaxResults.foo")

    def test_T5701_with_invalid_type_prefix_list_ids(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(PrefixListId={"foo": "bar"})
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidPrefixListId.NotFound",
                                     "The Prefix List Id 'bar' does not exist")

    def test_T5702_with_unknown_prefix_list_ids(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(PrefixListId=["foo"])
            assert False, "call should not have been successful"
        except OscApiException as error:
            assert_error(error, 400, "InvalidPrefixListId.NotFound",
                                     "The Prefix List Id 'foo' does not exist")
