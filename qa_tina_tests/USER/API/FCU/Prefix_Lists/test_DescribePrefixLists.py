import os

from qa_sdk_common.exceptions import OscApiException
from qa_test_tools import misc
from qa_test_tools.compare_objects import verify_response, create_hints
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest


class Test_DescribePrefixLists(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_DescribePrefixLists, cls).setup_class()
        ret = cls.a1_r1.fcu.DescribePrefixLists()
        hints = []
        prefix_list_names = sorted([prefix_list.prefixListName for prefix_list in ret.response.prefixListSet])
        for prefix_list_name in prefix_list_names:
            for prefix_list in ret.response.prefixListSet:
                if prefix_list_name == prefix_list.prefixListName:
                    hints.append(prefix_list.prefixListId)
                    hints.append(prefix_list.prefixListName)
                    for cidr in prefix_list.cidrSet:
                        hints.append(cidr)
                    break
        cls.hints = create_hints(hints)

    @classmethod
    def teardown_class(cls):
        super(Test_DescribePrefixLists, cls).teardown_class()

    def test_T5686_no_param(self):
        resp = self.a1_r1.fcu.DescribePrefixLists().response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_no_param.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5687_with_filter_prefix_list_id(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-id",
                                                           "Value": ["pl-dcbd245b", "pl-1b504c88"]}]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_filter_prefix_list_id.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5694_with_filter_empty_prefix_list_id(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-id", "Value": []}]).response
        assert not resp.prefixListSet

    def test_T5696_with_filter_unknown_prefix_list_id(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-id",
                                                           "Value": ["pl-99999999"]}]).response
        assert not resp.prefixListSet

    def test_T5708_with_filter_invalid_prefix_list_id(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-id",
                                                           "Value": ["foobar"]}]).response
        assert not resp.prefixListSet

    def test_T5698_with_filter_invalid_type_prefix_list_id(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name":"prefix-list-id", "Value": [["pl-dcbd245b"]]}])
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter Filter.1.Value.1.1")

    def test_T5709_with_filter_unknown_type_prefix_list_id(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-id",
                                                           "Value": {"foo": "bar"}}]).response
        assert not resp.prefixListSet

    def test_T5688_with_filter_prefix_list_name(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-name",
                                                           "Value": ["com.outscale.{}.fcu".format(self.a1_r1.config.region.name),
                                                                     "com.outscale.{}.kms".format(self.a1_r1.config.region.name)]}]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_filter_prefix_list_name.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5693_with_filter_empty_prefix_list_name(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-name", "Value":[]}]).response
        assert not resp.prefixListSet

    def test_T5695_with_filter_unknown_prefix_list_name(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-name",
                                                           "Value": ["tdiyfiy"]}]).response
        assert not resp.prefixListSet

    def test_T5697_with_filter_invalid_type_prefix_list_name(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "prefix-list-name",
                                                        "Value": [["com.outscale.in-west-1.fcu"]]}])
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter Filter.1.Value.1.1")

    def test_T5710_with_filter_unknown(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": "foo", "Value": ["bar"]}])
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidFilter", "The filter 'foo' is invalid")

    def test_T5711_with_filter_invalid_name_type(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Filter=[{"Name": {"foo": "bar"}, "Value":["bar"]}])
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter Filter.1.Name.foo")

    def test_T5689_with_prefix_list_ids(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(PrefixListId=["pl-dcbd245b", "pl-ce82d320"]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_prefix_list_ids.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5701_with_invalid_type_prefix_list_ids(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(PrefixListId={"foo": "bar"})
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidPrefixListId.NotFound",
                                     "The Prefix List Id 'bar' does not exist")

    def test_T5702_with_unknown_prefix_list_ids(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(PrefixListId=["pl-99999999"])
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidPrefixListId.NotFound",
                                     "The Prefix List Id 'pl-99999999' does not exist")

    def test_T5712_with_invalid_prefix_list_ids(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(PrefixListId=["foo bar"])
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidPrefixListId.NotFound",
                                     "The Prefix List Id 'foo bar' does not exist")

    def test_T5713_with_empty_prefix_list_ids(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(PrefixListId=[]).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_empty_prefix_list_ids.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5690_with_valid_next_token(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(MaxResults=5).response
        next_token = resp.nextToken
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_max_result.{}.json'.format(self.a1_r1.config.region.name)), self.hints)
        resp = self.a1_r1.fcu.DescribePrefixLists(NextToken=next_token).response
        if len(resp.prefixListSet) == 3:
            known_error('TINA-6563', 'Incorrect pagination')
        assert False, 'Remove known error code'
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_next_token.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5691_with_invalid_next_token(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(NextToken="foobar")
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidNextToken.Malformed", "Invalid value for 'NextToken': foobar")

    def test_T5692_with_invalid_type_next_token(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(NextToken={"foo": "bar"})
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidParameterValue", "Unexpected parameter NextToken.foo")

    def test_T5699_with_max_results_out_of_range(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(MaxResults=4).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_max_results_out_of_range.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5816_with_max_results_10000(self):
        resp = self.a1_r1.fcu.DescribePrefixLists(MaxResults=10000).response
        verify_response(resp, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'read_with_max_results_10000.{}.json'.format(self.a1_r1.config.region.name)), self.hints)

    def test_T5700_with_invalid_type_max_results(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(MaxResults="foo bar")
            assert False, "call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, "InvalidParameterValue",
                              "Invalid value for parameter 'MaxResults': 'foo bar'")

    def test_T5714_with_dry_run(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(DryRun=True)
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, 'DryRunOperation',
                              'Request would have succeeded, but DryRun flag is set.')

    def test_T5715_extra_param(self):
        try:
            self.a1_r1.fcu.DescribePrefixLists(Foo="bar")
            assert False, "Call should not have been successful"
        except OscApiException as error:
            misc.assert_error(error, 400, 'InvalidParameterValue', 'Unexpected parameter Foo')
