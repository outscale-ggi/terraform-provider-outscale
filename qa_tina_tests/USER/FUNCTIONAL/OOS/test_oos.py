from string import ascii_lowercase

from botocore.exceptions import ClientError
import pytest
import requests

from qa_test_tools.config import config_constants as constants
from qa_test_tools.misc import id_generator
from qa_test_tools.test_base import OscTestSuite, known_error


@pytest.mark.region_oos
class Test_oos(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_oos, cls).setup_class()

        try:
            cls.logger.debug("Initialize data in a bucket")

            #ret = cls.a1_r1.icu.CreateAccessKey()
            #cls.logger.debug(ret.response.display())

            # ret = cls.a1_r1.icu.DeleteAccessKey(AccessKeyId='D4CFG7NTYX07HQ6F4GG0')
            # cls.logger.debug(ret.response.display())

            #ret=cls.a1_r1.icu.ListAccessKeys()
            #cls.logger.debug(ret.response.display())

            cls.bucket_name = id_generator(prefix="bucket", chars=ascii_lowercase)
            cls.public_bucket_name = id_generator(prefix="publicbucket", chars=ascii_lowercase)
            cls.key_name = id_generator(prefix="key_", chars=ascii_lowercase)
            cls.data = id_generator(prefix="data_", chars=ascii_lowercase)
            cls.a1_r1.oos.create_bucket(Bucket=cls.bucket_name)
            cls.a1_r1.oos.put_object(Bucket=cls.bucket_name, Key=cls.key_name, Body=str.encode(cls.data))
            cls.a1_r1.oos.create_bucket(Bucket=cls.public_bucket_name, ACL='public-read')
            cls.a1_r1.oos.put_object(Bucket=cls.public_bucket_name, Key=cls.key_name, Body=str.encode(cls.data))
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
            cls.a1_r1.oos.delete_object(Bucket=cls.bucket_name, Key=cls.key_name)
            cls.a1_r1.oos.delete_bucket(Bucket=cls.bucket_name)
        finally:
            super(Test_oos, cls).teardown_class()


    @pytest.mark.tag_redwire
    def test_T5132_generated_url(self):
        params = {'Bucket': self.bucket_name, 'Key': self.key_name}
        url = self.a1_r1.oos.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
        ret = requests.get(url=url, verify=self.a1_r1.config.region.get_info(constants.VALIDATE_CERTS))
        assert ret.status_code == 200
        assert ret.content.decode() == self.data

    def test_T5133_read_key_in_bucket(self):
        ret = self.a1_r1.oos.get_object(Bucket=self.bucket_name, Key=self.key_name)['Body']
        assert ret.read().decode() == self.data

    def test_T5134_verify_display_name(self):
        res = self.a1_r1.oos.list_objects(Bucket=self.public_bucket_name)
        assert res['Contents'][0]['Owner']['DisplayName'] == self.a1_r1.config.account.account_id
