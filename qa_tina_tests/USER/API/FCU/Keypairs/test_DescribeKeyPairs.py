
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import assert_error
from qa_test_tools.test_base import OscTestSuite, known_error


class Test_DescribeKeyPairs(OscTestSuite):

    @classmethod
    def setup_class(cls):
        cls.kp_list = []
        cls.fingerprint = None
        super(Test_DescribeKeyPairs, cls).setup_class()
        try:
            for i in range(3):
                ret = cls.a1_r1.fcu.CreateKeyPair(KeyName='a1_keys_{}'.format(i))
                cls.kp_list.append({'name': ret.response.keyName, 'fingerprint': ret.response.keyFingerprint})
            cls.fingerprint = cls.a2_r1.fcu.CreateKeyPair(KeyName='a2_key_1').response.keyFingerprint
        except Exception as error1:
            try:
                cls.teardown_class()
            except Exception as error2:
                raise error2
            finally:
                raise error1

    @classmethod
    def teardown_class(cls):
        try:
            for kp in cls.kp_list:
                cls.a1_r1.fcu.DeleteKeyPair(KeyName=kp['name'])
            if cls.fingerprint:
                cls.a2_r1.fcu.DeleteKeyPair(KeyName='a2_key_1')
        finally:
            super(Test_DescribeKeyPairs, cls).teardown_class()

    def test_T938_without_param(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs()
        assert len(ret.response.keySet) == 3
        # TODO: check response content

    def test_T5069_with_keyname_dict(self):
        try:
            self.a1_r1.fcu.DescribeKeyPairs(KeyName={'toto': self.kp_list[0]['name']})
            known_error('TINA-5744', 'Call with incorrect argument type does not fail')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, 'InvalidParameterValue', None)

    def test_T5070_with_keyname_string(self):
        try:
            self.a1_r1.fcu.DescribeKeyPairs(KeyName=self.kp_list[0]['name'])
            known_error('TINA-5744', 'Call with incorrect argument type does not fail')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert False, 'Remove known error code'
            assert_error(error, 400, 'InvalidParameterValue', None)

    def test_T939_with_valid_keyname(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(KeyName=[self.kp_list[0]['name']])
        assert len(ret.response.keySet) == 1
        assert ret.response.keySet[0].keyName == self.kp_list[0]['name']
        assert ret.response.keySet[0].keyFingerprint == self.kp_list[0]['fingerprint']

    def test_T940_with_multiple_keynames(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(KeyName=[self.kp_list[1]['name'], self.kp_list[0]['name']])
        assert len(ret.response.keySet) == 2
        assert ret.response.keySet[0].keyName == self.kp_list[0]['name']
        assert ret.response.keySet[0].keyFingerprint == self.kp_list[0]['fingerprint']
        assert ret.response.keySet[1].keyName == self.kp_list[1]['name']
        assert ret.response.keySet[1].keyFingerprint == self.kp_list[1]['fingerprint']

    def test_T941_with_invalid_keyname(self):
        try:
            self.a1_r1.fcu.DescribeKeyPairs(KeyName=['toto'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidKeyPair.NotFound', 'The key pair does not exist: toto')

    def test_T942_with_keyname_from_another_account(self):
        try:
            self.a1_r1.fcu.DescribeKeyPairs(KeyName=['a2_key_1'])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidKeyPair.NotFound', 'The key pair does not exist: a2_key_1')

    def test_T943_with_filter_valid_fingerprint(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'fingerprint', 'Value': self.kp_list[1]['fingerprint']}])
        assert len(ret.response.keySet) == 1
        assert ret.response.keySet[0].keyName == self.kp_list[1]['name']
        assert ret.response.keySet[0].keyFingerprint == self.kp_list[1]['fingerprint']

    def test_T944_with_filter_invalid_fingerprint(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'fingerprint', 'Value': 'toto'}])
        assert not ret.response.keySet

    def test_T945_with_filter_fingerprint_from_another_account(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'fingerprint', 'Value': self.fingerprint}])
        assert not ret.response.keySet

    def test_T946_with_filter_valid_keyname(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'key-name', 'Value': self.kp_list[0]['name']}])
        assert len(ret.response.keySet) == 1
        assert ret.response.keySet[0].keyName == self.kp_list[0]['name']
        assert ret.response.keySet[0].keyFingerprint == self.kp_list[0]['fingerprint']

    def test_T947_with_filter_invalid_keyname(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'key-name', 'Value': 'toto'}])
        assert not ret.response.keySet

    def test_T948_with_filter_keyname_from_another_account(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'key-name', 'Value': 'a2_key_1'}])
        assert not ret.response.keySet

    def test_T949_with_invalid_filter(self):
        try:
            self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'foo', 'Value': 'toto'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidFilter", "The filter is invalid: foo")

    def test_T1906_with_filter_invalid_tag_key(self):
        try:
            self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'tag:foo', 'Value': 'bar'}])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidFilter", "The filter is invalid: tag:foo")

    def test_T950_with_filter_valid_keyname_and_fingerprint(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'fingerprint', 'Value': self.kp_list[1]['fingerprint']},
                                                      {'Name': 'key-name', 'Value': self.kp_list[1]['name']}])
        assert len(ret.response.keySet) == 1
        assert ret.response.keySet[0].keyName == self.kp_list[1]['name']

    def test_T951_with_valid_keyname_and_filter_fingerprint(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Keyname=self.kp_list[1]['name'],
                                              Filter=[{'Name': 'fingerprint', 'Value': self.kp_list[1]['fingerprint']}])
        assert len(ret.response.keySet) == 1
        assert ret.response.keySet[0].keyName == self.kp_list[1]['name']

    def test_T1389_filter_invalid_kn_fp(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(Filter=[{'Name': 'fingerprint', 'Value': self.kp_list[1]['fingerprint']},
                                                      {'Name': 'key-name', 'Value': self.kp_list[0]['name']}])
        assert not ret.response.keySet

    def test_T1390_invalid_param(self):
        ret = self.a1_r1.fcu.DescribeKeyPairs(foo='bar')
        assert len(ret.response.keySet) == 3
