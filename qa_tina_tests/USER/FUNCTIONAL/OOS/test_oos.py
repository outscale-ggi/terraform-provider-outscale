from string import ascii_lowercase

import filecmp
import hashlib
import json
import os
import pytest
import requests

from qa_test_tools import misc
from qa_test_tools.config import config_constants as constants
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tina import storage


@pytest.mark.region_oos
class Test_oos(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_oos, cls).setup_class()
        cls.bucket_created = False
        try:
            cls.logger.debug("Initialize data in a bucket")

            #ret = cls.a1_r1.icu.CreateAccessKey()
            #cls.logger.debug(ret.response.display())

            # ret = cls.a1_r1.icu.DeleteAccessKey(AccessKeyId='D4CFG7NTYX07HQ6F4GG0')
            # cls.logger.debug(ret.response.display())

            #ret=cls.a1_r1.icu.ListAccessKeys()
            #cls.logger.debug(ret.response.display())

            cls.bucket_name = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            cls.public_bucket_name = misc.id_generator(prefix="publicbucket", chars=ascii_lowercase)
            cls.key_name = misc.id_generator(prefix="key_", chars=ascii_lowercase)
            cls.data = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            cls.a1_r1.oos.create_bucket(Bucket=cls.bucket_name)
            cls.bucket_created = True
            cls.a1_r1.oos.put_object(Bucket=cls.bucket_name, Key=cls.key_name, Body=str.encode(cls.data))
            cls.a1_r1.oos.create_bucket(Bucket=cls.public_bucket_name, ACL='public-read')
            cls.a1_r1.oos.put_object(Bucket=cls.public_bucket_name, Key=cls.key_name, Body=str.encode(cls.data))

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
            cls.logger.debug("Remove data and bucket")
            if cls.bucket_created:
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

    def test_T5887_static_website_bucket(self):
        """
            Create a static website in the bucket and request this website by the endpoint oos-website
            and check the text in the response
        """
        bucket_name = None
        obj_name = None
        try:
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            self.a1_r1.oos.create_bucket(Bucket=tmp)
            bucket_name = tmp
            bucket_policy = {
                'Version': '2012-10-17',
                'Statement': [{
                    'Sid': 'AddPerm',
                    'Effect': 'Allow',
                    'Principal': '*',
                    'Action': ['s3:GetObject'],
                    'Resource': "arn:aws:s3:::%s/*" % bucket_name
                }]
            }
            bucket_policy = json.dumps(bucket_policy)
            self.a1_r1.oos.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
            self.a1_r1.oos.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration={
                    'ErrorDocument': {'Key': 'error.html'},
                    'IndexDocument': {'Suffix': 'index.html'},
                }
            )
            filename = ['index.html', 'error.html']
            for file in filename:
                file_tmp = open(file, 'w')
                file_tmp.write("""<!DOCTYPE html>
                                 <html>
                                 <body>
                                 <h1>Hello World it's the {} !</h1>
                                 </body>
                                 </html>
                                 """.format(file[:-5]))
                file_tmp.close()
            for file in filename:
                data = open(file)
                self.a1_r1.oos.put_object(Bucket=bucket_name, Key=file, Body=str.encode(data.read()), ContentType='text/html')
            obj_name = filename
            service = 'oos'
            response = requests.get(
                'https://{}.{}-website.{}.outscale.com'.format(bucket_name, service, self.a1_r1.config.region.name),
                verify=self.a1_r1.config.region.get_info(constants.VALIDATE_CERTS)
            )
            if self.a1_r1.config.region.name == 'in-west-1':
                if "InvalidURI" in response.text:
                    known_error('OPS-14142', "OOS website bucket issue on IN1")
                else:
                    assert False, 'Remove known error'
                assert "Hello World it's the index !" in response.text
        finally:
            errors = []
            if obj_name:
                try:
                    for obj in obj_name:
                        self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=obj)
                except Exception as error:
                    errors.append(error)
            if bucket_name:
                try:
                    self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise errors[0]

    def test_T5888_cors_bucket(self):
        """
            Create two buckets
            Create the first website with a suffix index.html , a key error.html and a load.html
            Check that the loading by javascript works by loading load.html in index.html
            Create the second website in the second bucket
            Put only the load.html in the second bucket
            Request the endpoint oos-website/load.html of the the second website to check that we get this object
            Modify the index.html of the first website by loading the last object of the second domain with javascript
            Put this object in the first bucket and request the website to check that we have the goog response
        """
        #TODO html modification to active javascript and active this test by removing comments in requests
        bucket_names = []
        filename_dict = {}
        obj_name = None
        try:
            tmp_1 = misc.id_generator(prefix="website1", chars=ascii_lowercase)
            tmp_2 = misc.id_generator(prefix="website2", chars=ascii_lowercase)
            self.a1_r1.oos.create_bucket(Bucket=tmp_1)
            self.a1_r1.oos.create_bucket(Bucket=tmp_2)
            bucket_names = [tmp_1, tmp_2]
            for bucket_name in bucket_names:
                bucket_policy = {
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Sid': 'AddPerm',
                        'Effect': 'Allow',
                        'Principal': '*',
                        'Action': ['s3:GetObject'],
                        'Resource': "arn:aws:s3:::%s/*" % bucket_name
                    }]
                }
                bucket_policy = json.dumps(bucket_policy)

                self.a1_r1.oos.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
            self.a1_r1.oos.put_bucket_website(
                Bucket=bucket_names[0],
                WebsiteConfiguration={
                    'ErrorDocument': {'Key': 'error.html'},
                    'IndexDocument': {'Suffix': 'index.html'},
                }
            )

            content_error = """<!DOCTYPE html>
                                    <html>
                                    <body>
                                    <h1>something is wrong</h1>
                                    </body>
                                    </html>
                                    """

            content_load = "Hello this is from load.html"
            filename_dict = {"index.html": storage.generate_indexhtml('load.html'), "error.html": content_error, "load.html": content_load}
            for file in filename_dict:
                file_tmp = open(file, 'w')
                file_tmp.write(filename_dict[file])
                file_tmp.close()
            for file in filename_dict:
                data = open(file)
                self.a1_r1.oos.put_object(Bucket=bucket_names[0], Key=file, Body=str.encode(data.read()),
                                          ContentType='text/html')

            service = 'oos'
            requests.get('https://{}.{}-website.{}.outscale.com'.format(bucket_names[0], service, self.a1_r1.config.region.name),
                         verify=self.a1_r1.config.region.get_info(constants.VALIDATE_CERTS))
            #assert response.text == "Hello this is from load.html"
            obj_name = filename_dict
            self.a1_r1.oos.put_bucket_website(
                Bucket=bucket_names[1],
                WebsiteConfiguration={
                    'IndexDocument': {'Suffix': 'index.html'}
                }
            )
            data = open('load.html')
            self.a1_r1.oos.put_object(Bucket=bucket_names[1], Key=file, Body=str.encode(data.read()),
                                      ContentType='text/html')
            # source = "todo website endpoint"
            file_tmp = open('index.html', 'w')
            file_tmp.write(storage.generate_indexhtml("https://bucket_2_name.oos-website.{}.outscale.com/load.html".
                                                      format(self.a1_r1.config.region.name)))
            file_tmp.close()
            data = open('index.html')
            self.a1_r1.oos.put_object(Bucket=bucket_names[0], Key='index.html', Body=str.encode(data.read()),
                                      ContentType='text/html')
            cors_configuration = {
                'CORSRules': [{
                    'AllowedHeaders': ['Authorization'],
                    'AllowedMethods': ['GET', 'PUT'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['GET', 'PUT'],
                    'MaxAgeSeconds': 3000
                }]
            }
            self.a1_r1.oos.put_bucket_cors(Bucket=bucket_names[1], CORSConfiguration=cors_configuration)
            requests.get(
                'https://{}.{}-website.{}.outscale.com'.format(bucket_name, service, self.a1_r1.config.region.name),
                verify=self.a1_r1.config.region.get_info(constants.VALIDATE_CERTS))
            # assert response.text == "Hello this is from load.html"
        finally:
            errors = []
            if obj_name:
                try:
                    self.a1_r1.oos.delete_object(Bucket=bucket_names[1], Key='load.html')
                    for obj in obj_name:
                        self.a1_r1.oos.delete_object(Bucket=bucket_names[0], Key=obj)
                except Exception as error:
                    errors.append(error)
            if bucket_names:
                try:
                    for bucket_name in bucket_names:
                        self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            for file in filename_dict:
                os.remove(file)
            if errors:
                raise errors[0]

    def test_T5889_acl_bucket(self):
        """
            Create an object in a bucket and create after a public_read acl for this object
            Get this object with a second account
        """
        if not hasattr(self, 'a2_r1'):
            pytest.skip('This test requires two users')
        bucket_name = None
        obj_name_1 = None
        obj_name_2 = None
        try:
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            self.a1_r1.oos.create_bucket(Bucket=tmp)
            bucket_name = tmp
            tmp_1 = misc.id_generator(prefix="obj_", chars=ascii_lowercase)
            tmp_2 = misc.id_generator(prefix="obj_", chars=ascii_lowercase)
            data_1 = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            data_2 = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            self.a1_r1.oos.put_object(Bucket=bucket_name, Key=tmp_1, Body=str.encode(data_1))
            obj_name_1 = tmp_1
            obj_name_2 = tmp_2
            ret_account_1 = self.a1_r1.oos.list_buckets()
            ret_account_2 = self.a2_r1.oos.list_buckets()
            access_policy = {
                'Grants': [
                    {
                        'Grantee': {
                            'DisplayName': ret_account_2['Owner']['DisplayName'],
                            'ID': ret_account_2['Owner']['ID'],
                            'Type': 'CanonicalUser',
                        },
                        'Permission': 'FULL_CONTROL'
                    },
                ],
                'Owner': {
                    'DisplayName': ret_account_1['Owner']['DisplayName'],
                    'ID': ret_account_1['Owner']['ID']
                }
            }
            self.a1_r1.oos.put_bucket_acl(Bucket=bucket_name, AccessControlPolicy=access_policy)
            self.a2_r1.oos.put_object(Bucket=bucket_name, Key=tmp_2, Body=str.encode(data_2))
            self.a1_r1.oos.put_object_acl(Bucket=bucket_name, AccessControlPolicy=access_policy, Key=obj_name_1)
            obj = self.a2_r1.oos.get_object(Bucket=bucket_name, Key=obj_name_1)['Body']
            assert obj.read().decode() == data_1
        finally:
            errors = []
            if obj_name_1:
                try:
                    self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=obj_name_1)
                except Exception as error:
                    errors.append(error)
            if obj_name_2:
                try:
                    self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=obj_name_2)
                except Exception as error:
                    errors.append(error)
            if bucket_name:
                try:
                    self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise errors[0]

    def test_T5890_object(self):
        """
            Create a html object in a bucket and request the endpoint oos scality to check the object.
        """
        bucket_name = None
        obj_name = None
        try:
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            self.a1_r1.oos.create_bucket(Bucket=tmp)
            bucket_name = tmp
            bucket_policy = {
                'Version': '2012-10-17',
                'Statement': [{
                    'Sid': 'AddPerm',
                    'Effect': 'Allow',
                    'Principal': '*',
                    'Action': ['s3:GetObject'],
                    'Resource': "arn:aws:s3:::%s/*" % bucket_name
                }]
            }
            bucket_policy = json.dumps(bucket_policy)
            self.a1_r1.oos.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
            filename = ['index.html', 'error.html']
            for file in filename:
                file_tmp = open(file, 'w')
                file_tmp.write("Hello World it s the {}".format(file[:-5]))
                file_tmp.close()
            for file in filename:
                data = open(file)
                self.a1_r1.oos.put_object(Bucket=bucket_name, Key=file, Body=str.encode(data.read()), ContentType='text/html')
            obj_name = filename
            service = 'oos'
            for file in filename:
                response = requests.get(
                    'https://{}.{}.{}.outscale.com/{}'.format(bucket_name, service, self.a1_r1.config.region.name, file),
                    verify=self.a1_r1.config.region.get_info(constants.VALIDATE_CERTS))
                assert response.text == "Hello World it s the {}".format(file[:-5])
        finally:
            errors = []
            if obj_name:
                try:
                    for obj in obj_name:
                        self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=obj)
                except Exception as error:
                    errors.append(error)
            if bucket_name:
                try:
                    self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            for file in filename:
                os.remove(file)
            if errors:
                raise errors[0]

    def test_T5891_multiple_upload(self):
        """
            Create a bucket
            Create file data.txt
            Abort all multipart uploads for this bucket
            Create new multipart upload
            Upload parts
            Complete multipart upload
            Download the file data_generated.txt from the bucket
            Compare data.txt with data_generated.txt
        """
        bucket_name = None
        md5s = []
        paths = []
        try:
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            filename = misc.id_generator(prefix="data", chars=ascii_lowercase) + '.txt'
            downloaded_file_name = misc.id_generator(prefix="data_generated", chars=ascii_lowercase) + '.txt'
            self.a1_r1.oos.create_bucket(Bucket=tmp)
            bucket_name = tmp
            path_to_file = storage.write_data(pow(10, 1), filename)
            paths.append(path_to_file)
            mpu = storage.s3multipartupload(
                self.a1_r1,
                'oos',
                bucket_name,
                'data.txt',
                path_to_file)
            # abort all multipart uploads for this bucket (optional, for starting over)
            mpu.abort_all()
            # create new multipart upload
            mpu_id = mpu.create()
            self.a1_r1.oos.list_multipart_uploads(Bucket=bucket_name)
            # upload parts
            parts = mpu.upload(mpu_id)
            # complete multipart upload
            response = self.a1_r1.oos.list_parts(Bucket=bucket_name, Key='data.txt', UploadId=mpu_id)
            assert len(response['Parts']) >= 1
            multiple_upload = self.a1_r1.oos.list_multipart_uploads(Bucket=bucket_name)
            assert multiple_upload['Uploads'][0]['Key'] == 'data.txt'
            ret = mpu.complete(mpu_id, parts)
            print(ret)
            objects = self.a1_r1.oos.list_objects(
                Bucket=bucket_name,
            )
            assert objects['Contents'][0]['Key'] == 'data.txt'
            path_to_downloaded_file = os.path.join('/tmp', downloaded_file_name)
            self.a1_r1.oos.download_file(Bucket=bucket_name, Key='data.txt', Filename=path_to_downloaded_file)
            paths.append(path_to_downloaded_file)
            assert filecmp.cmp(path_to_downloaded_file, path_to_file)
            for file in paths:
                fichier = open(file, 'r')
                md5s.append(hashlib.sha256(str.encode(fichier.read())).hexdigest())
            assert md5s.count(md5s[0]) == 2
        finally:
            errors = []
            self.a1_r1.oos.delete_object(Bucket=bucket_name, Key='data.txt')
            if bucket_name:
                try:
                    self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            for file in paths:
                os.remove(file)
            if errors:
                raise errors[0]

    def test_T5892_multiple_upload_copy(self):
        """
            Create a bucket
            Create file data.txt
            Put an object in bucket with the data of the created file
            Abort all multipart uploads for this bucket
            Create new multipart upload
            Upload copy parts
            Complete multipart upload
            Download the file data_generated.txt from the bucket
            Compare data.txt with data_generated.txt
        """
        bucket_name = None
        md5s = []
        paths = []
        try:
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            filename = misc.id_generator(prefix="data", chars=ascii_lowercase) + '.txt'
            downloaded_file_name = misc.id_generator(prefix="data_generated", chars=ascii_lowercase) + '.txt'
            self.a1_r1.oos.create_bucket(Bucket=tmp)
            bucket_name = tmp
            path_to_file = storage.write_data(pow(10, 1), filename)
            paths.append(path_to_file)
            mpu = storage.s3multipartupload(
                self.a1_r1,
                'oos',
                bucket_name,
                'data.txt',
                path_to_file)
            # abort all multipart uploads for this bucket (optional, for starting over)
            mpu.abort_all()
            # create new multipart upload
            mpu_id = mpu.create()
            self.a1_r1.oos.list_multipart_uploads(Bucket=bucket_name)
            # upload parts
            parts = mpu.upload(mpu_id, copy=True)
            # complete multipart upload
            response = self.a1_r1.oos.list_parts(
                Bucket=bucket_name,
                Key='data.txt',
                UploadId=mpu_id,
            )
            assert len(response['Parts']) >= 1
            multiple_upload = self.a1_r1.oos.list_multipart_uploads(Bucket=bucket_name)
            assert multiple_upload['Uploads'][0]['Key'] == 'data.txt'
            ret = mpu.complete(mpu_id, parts)
            print(ret)
            objects = self.a1_r1.oos.list_objects(
                Bucket=bucket_name,
            )
            assert objects['Contents'][0]['Key'] == 'data.txt'
            path_to_downloaded_file = os.path.join('/tmp', downloaded_file_name)
            self.a1_r1.oos.download_file(Bucket=bucket_name, Key='data.txt', Filename=path_to_downloaded_file)
            paths.append(path_to_downloaded_file)
            assert filecmp.cmp(path_to_downloaded_file, path_to_file)
            for file in paths:
                fichier = open(file, 'r')
                md5s.append(hashlib.sha256(str.encode(fichier.read())).hexdigest())
            assert md5s.count(md5s[0]) == 2
        finally:
            errors = []
            self.a1_r1.oos.delete_object(Bucket=bucket_name, Key='data.txt')
            if bucket_name:
                try:
                    self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            for file in paths:
                os.remove(file)
            if errors:
                raise errors[0]

    def test_T5893_bucket_versioning(self):
        """
            Create bucket
            Enable the versionning
            Create an object and put it in the bucket
            Modify this object et put it an other time in the bucket
            Get object versionning et check that we have 2 versions of the object

        """
        bucket_name = None
        obj_name = None
        try:
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            self.a1_r1.oos.create_bucket(Bucket=tmp)
            bucket_name = tmp
            response = self.a1_r1.oos.put_bucket_versioning(Bucket=bucket_name,
                                                            VersioningConfiguration={'MFADelete': 'Disabled',
                                                                                     'Status': 'Enabled'})
            tmp = misc.id_generator(prefix="obj_", chars=ascii_lowercase)
            data_version_1 = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            data_version_2 = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            self.a1_r1.oos.put_object(Bucket=bucket_name, Key=tmp, Body=str.encode(data_version_1))
            self.a1_r1.oos.put_object(Bucket=bucket_name, Key=tmp, Body=str.encode(data_version_2))
            obj_name = tmp
            response = self.a1_r1.oos.get_bucket_versioning(
                Bucket=bucket_name
            )
            assert response["Status"] == 'Enabled'
            response = self.a1_r1.oos.list_object_versions(
                Bucket=bucket_name,
                Prefix=obj_name,
            )
            assert len(response['Versions']) == 2
            obj_version_1 = self.a1_r1.oos.get_object(Bucket=bucket_name, Key=obj_name,
                                                      VersionId=response["Versions"][1]["VersionId"])['Body']
            obj_version_2 = self.a1_r1.oos.get_object(Bucket=bucket_name, Key=obj_name,
                                                      VersionId=response["Versions"][0]["VersionId"])['Body']
            assert obj_version_1.read().decode() == data_version_1
            assert obj_version_2.read().decode() == data_version_2

        finally:
            errors = []
            if obj_name:
                try:
                    for version in [response["Versions"][1]["VersionId"], response["Versions"][0]["VersionId"]]:
                        self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=obj_name, VersionId=version)
                except Exception as error:
                    errors.append(error)
            if bucket_name:
                try:
                    self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise errors[0]

    def test_T5894_url_presigned(self):
        """
            Create and delete an object in a bucket.
        """
        bucket_name = None
        obj_name = None
        try:
            tmp = misc.id_generator(prefix="bucket", chars=ascii_lowercase)
            self.a1_r1.oos.create_bucket(Bucket=tmp)
            bucket_name = tmp
            tmp = misc.id_generator(prefix="obj_", chars=ascii_lowercase)
            data = misc.id_generator(prefix="data_", chars=ascii_lowercase)
            self.a1_r1.oos.put_object(Bucket=bucket_name, Key=tmp, Body=str.encode(data))
            obj_name = tmp
            params = {'Bucket': bucket_name, 'Key': obj_name}
            url = self.a1_r1.oos.generate_presigned_url(ClientMethod='get_object', Params=params, ExpiresIn=3600)
            response = requests.get(url, verify=self.a1_r1.config.region.get_info(constants.VALIDATE_CERTS))
            assert response.text == data
        finally:
            errors = []
            if obj_name:
                try:
                    self.a1_r1.oos.delete_object(Bucket=bucket_name, Key=obj_name)
                except Exception as error:
                    errors.append(error)
            if bucket_name:
                try:
                    self.a1_r1.oos.delete_bucket(Bucket=bucket_name)
                except Exception as error:
                    errors.append(error)
            if errors:
                raise errors[0]
