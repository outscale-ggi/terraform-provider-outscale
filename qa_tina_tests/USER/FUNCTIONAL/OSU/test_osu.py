import pytest
import requests

from string import ascii_lowercase

from botocore.exceptions import ClientError
from qa_common_tools import constants
from qa_common_tools.misc import id_generator
from qa_common_tools.test_base import OscTestSuite, known_error


@pytest.mark.region_osu
class Test_osu(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_osu, cls).setup_class()

        try:
            cls.logger.debug("Initialize data in a bucket")

            #ret = cls.a1_r1.icu.CreateAccessKey()
            #cls.logger.debug(ret.response.display())

            # ret = cls.a1_r1.icu.DeleteAccessKey(AccessKeyId='D4CFG7NTYX07HQ6F4GG0')
            # cls.logger.debug(ret.response.display())

            #ret=cls.a1_r1.icu.ListAccessKeys()
            #cls.logger.debug(ret.response.display())

            cls.bucket_name = id_generator(prefix="bucket_", chars=ascii_lowercase)
            cls.key_name = id_generator(prefix="key_", chars=ascii_lowercase)
            cls.data = id_generator(prefix="data_", chars=ascii_lowercase)
            cls.known_error = False
            try:
                cls.a1_r1.osu.create_bucket(Bucket=cls.bucket_name)
                cls.a1_r1.osu.put_object(Bucket=cls.bucket_name, Key=cls.key_name, Body=str.encode(cls.data))
            except ClientError as error:
                if cls.a1_r1.config.region.name in ['us-west-1', 'us-east-2']:
                    cls.known_error = True
                else:
                    raise error
            # b_list = cls.a1_r1.osu.conn.list_buckets()['Buckets']
            # for b in b_list:
            #    cls.logger.debug(b['Name'])
            #    k_list = cls.a1_r1.osu.conn.list_objects(Bucket=b['Name'])
            #    #import pprint
            #    #pprint.pprint(k_list)
            #    if 'Contents' in list(k_list.keys()):
            #        for k in k_list['Contents']:
            #            cls.logger.debug("  "+k['Key'])
            #            d = cls.a1_r1.osu.conn.get_object(Bucket=b['Name'], Key=k['Key'])['Body']
            #            cls.logger.debug("    "+d.read().decode())
            #    #        cls.a1_r1.osu.conn.delete_object(Bucket=b['Name'], Key=k['Key'])
            #    #cls.a1_r1.osu.conn.delete_bucket(Bucket=b['Name'])
        except:
            try:
                cls.teardown_class()
            except:
                pass
            raise

    @classmethod
    def teardown_class(cls):
        try:
            cls.logger.debug("Remove data and bucket")
            if not cls.known_error:
                cls.a1_r1.osu.delete_object(Bucket=cls.bucket_name, Key=cls.key_name)
                cls.a1_r1.osu.delete_bucket(Bucket=cls.bucket_name)
        finally:
            super(Test_osu, cls).teardown_class()

    @pytest.mark.region_osu
    @pytest.mark.tag_redwire
    def test_T183_generated_url(self):
        if self.a1_r1.config.region.name in ['us-west-1', 'us-east-2']:
            if self.known_error:
                known_error('OPS-8714', 'Accounts not synchronize on OSU')
            else:
                assert False, 'Remove known error code'
        params = {'Bucket': self.bucket_name, 'Key': self.key_name}
        url = self.a1_r1.osu.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
        ret = requests.get(url=url, verify=self.a1_r1.config.region.get_info(constants.VALIDATE_CERTS))
        assert ret.status_code == 200
        assert ret.content.decode() == self.data

    def test_T184_read_key_in_bucket(self):
        d = self.a1_r1.osu.get_object(Bucket=self.bucket_name, Key=self.key_name)['Body']
        assert d.read().decode() == self.data

    # def test_T000_(self):
    #    pass
