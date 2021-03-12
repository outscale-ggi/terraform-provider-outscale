
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.misc import id_generator, assert_error
from qa_test_tools.test_base import OscTestSuite
from qa_tina_tools.tina.check_tools import get_snapshot_id_list
from qa_tina_tools.tools.tina.cleanup_tools import cleanup_images
from qa_tina_tools.tools.tina.create_tools import create_instances_old, create_image
from qa_tina_tools.tools.tina.delete_tools import delete_instances_old

DESCRIPTION = id_generator(prefix="description")


class Test_ModifyImageAttribute(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_ModifyImageAttribute, cls).setup_class()
        cls.inst_id = None
        cls.image_name = id_generator(prefix='img_')
        cls.image_id = None
        cls.add_user_id = {'Add': [{'UserId': str(cls.a2_r1.config.account.account_id)}]}
        cls.remove_user_id = {'Remove': [{'UserId': str(cls.a2_r1.config.account.account_id)}]}
        cls.add_group = {'Add': [{'Group': 'all'}]}
        cls.remove_group = {'Remove': [{'Group': 'all'}]}
        try:
            # create 1 instance
            _, inst_id_list = create_instances_old(cls.a1_r1, state='running')
            cls.inst_id = inst_id_list[0]
            # create image
            ret, cls.image_id = create_image(cls.a1_r1, cls.inst_id, name=cls.image_name, state='available', description=DESCRIPTION)
            cls.img1_snap_id_list = get_snapshot_id_list(ret)
            assert len(cls.img1_snap_id_list) == 1, 'Could not find snapshots created when creating image'
        except Exception:
            try:
                cls.teardown_class()
            finally:
                raise

    @classmethod
    def teardown_class(cls):
        try:
            if cls.inst_id:
                delete_instances_old(cls.a1_r1, [cls.inst_id])
            if cls.image_id:
                cleanup_images(cls.a1_r1, image_id_list=[cls.image_id], force=True)
        finally:
            super(Test_ModifyImageAttribute, cls).teardown_class()

    def test_T1737_missing_image_id(self):
        try:
            self.a1_r1.fcu.ModifyImageAttribute(LaunchPermission=self.add_user_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAMIID.Malformed', "Invalid id: 'None' (expecting 'ami-...')")

    def test_T1738_unknown_image_id(self):
        try:
            self.a1_r1.fcu.ModifyImageAttribute(ImageId='ami-12345678', LaunchPermission=self.add_user_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAMIID.NotFound', "The AMI ID 'ami-12345678' does not exist")

    def test_T1739_incorrect_image_id(self):
        try:
            self.a1_r1.fcu.ModifyImageAttribute(ImageId='xxx-12345678', LaunchPermission=self.add_user_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidAMIID.Malformed', "Invalid id: 'xxx-12345678' (expecting 'ami-...')")

    def test_T1740_missing_permissions(self):
        try:
            self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id)
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'OWS.Error', 'Request is not valid.')

    def test_T1742_empty_permissions(self):
        try:
            self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission='')
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterType", "Value of parameter 'LaunchPermission' must be of type: dict. Received: ")

    def test_T1741_incorrect_type_permissions(self):
        msg_part_1 = "{'1': {'Add': {'1': {'UserId': '"
        msg_part_2 = "'}}}}"
        try:
            self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission=[self.add_user_id])
            assert False, 'Call should not have been successful'
        except OscApiException as error:
            assert_error(error, 400, 'InvalidParameterValue',
                         "Value of parameter 'LaunchPermission' " + \
                         "is not valid: {}{}{}. Supported values: Add, Remove".format(msg_part_1, self.a2_r1.config.account.account_id, msg_part_2))

    def test_T1540_lp_one_user(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission=self.add_user_id)
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
            assert hasattr(resp, 'launchPermission')
            assert isinstance(resp.launchPermission, list)
            assert len(resp.launchPermission) == 1
            assert hasattr(resp.launchPermission[0], 'userId')
            assert resp.launchPermission[0].userId == self.a2_r1.config.account.account_id
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission=self.remove_user_id)
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
                assert hasattr(resp, 'launchPermission')
                assert not resp.launchPermission

    def test_T1743_lp_one_group(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission=self.add_group)
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
            assert hasattr(resp, 'launchPermission')
            assert isinstance(resp.launchPermission, list)
            assert len(resp.launchPermission) == 1
            assert hasattr(resp.launchPermission[0], 'group')
            assert resp.launchPermission[0].group == 'all'
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission=self.remove_group)
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
                assert hasattr(resp, 'launchPermission')
                assert not resp.launchPermission

    def test_T1744_lp_multi_user(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id,
                                                      LaunchPermission={'Add': [{'UserId': str(self.a1_r1.config.account.account_id)},
                                                                                {'UserId': str(self.a2_r1.config.account.account_id)}]})
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
            assert hasattr(resp, 'launchPermission')
            assert isinstance(resp.launchPermission, list)
            assert len(resp.launchPermission) == 2
            assert hasattr(resp.launchPermission[0], 'userId')
            assert hasattr(resp.launchPermission[1], 'userId')
            user_ids = [perm.userId for perm in resp.launchPermission]
            assert self.a1_r1.config.account.account_id in user_ids
            assert self.a2_r1.config.account.account_id in user_ids
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id,
                                                          LaunchPermission={'Remove': [{'UserId': str(self.a1_r1.config.account.account_id)},
                                                                                       {'UserId': str(self.a2_r1.config.account.account_id)}]})
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
                assert hasattr(resp, 'launchPermission')
                assert not resp.launchPermission

    def test_T1745_lp_multi_same_user(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id,
                                                      LaunchPermission={'Add': [{'UserId': str(self.a2_r1.config.account.account_id)},
                                                                                {'UserId': str(self.a2_r1.config.account.account_id)}]})
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
            assert hasattr(resp, 'launchPermission')
            assert isinstance(resp.launchPermission, list)
            assert len(resp.launchPermission) == 1
            assert hasattr(resp.launchPermission[0], 'userId')
            assert resp.launchPermission[0].userId == self.a2_r1.config.account.account_id
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id,
                                                          LaunchPermission={'Remove': [{'UserId': str(self.a2_r1.config.account.account_id)},
                                                                                       {'UserId': str(self.a2_r1.config.account.account_id)}]})
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
                assert hasattr(resp, 'launchPermission')
                assert not resp.launchPermission

    def test_T1747_lp_multi_same_group(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission={'Add': [{'Group': 'all'}, {'Group': 'all'}]})
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
            assert hasattr(resp, 'launchPermission')
            assert isinstance(resp.launchPermission, list)
            assert len(resp.launchPermission) == 1
            assert hasattr(resp.launchPermission[0], 'group')
            assert resp.launchPermission[0].group == 'all'
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, LaunchPermission={'Remove': [{'Group': 'all'}, {'Group': 'all'}]})
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
                assert hasattr(resp, 'launchPermission')
                assert not resp.launchPermission

    def test_T1748_lp_multi_mixed(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id,
                                                      LaunchPermission={'Add': [{'UserId': str(self.a2_r1.config.account.account_id)},
                                                                                {'Group': 'all'}]})
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
            assert hasattr(resp, 'launchPermission')
            assert isinstance(resp.launchPermission, list)
            assert len(resp.launchPermission) == 2
            group_index = None
            user_index = None
            if hasattr(resp.launchPermission[0], 'userId'):
                user_index = 0
            if hasattr(resp.launchPermission[1], 'userId'):
                user_index = 1
            if hasattr(resp.launchPermission[0], 'group'):
                group_index = 0
            if hasattr(resp.launchPermission[1], 'group'):
                group_index = 1
            assert group_index is not None and user_index is not None
            assert resp.launchPermission[user_index].userId == self.a2_r1.config.account.account_id
            assert resp.launchPermission[group_index].group == 'all'
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id,
                                                          LaunchPermission={'Remove': [{'UserId': str(self.a2_r1.config.account.account_id)},
                                                                                       {'Group': 'all'}]})
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
                assert hasattr(resp, 'launchPermission')
                assert not resp.launchPermission

    def test_T1749_description(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, Description=DESCRIPTION + 'new')
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='description').response
            assert hasattr(resp, 'description')
            assert resp.description == DESCRIPTION + 'new'
        except OscApiException as error:
            assert_error(error, 400, "InvalidParameterType",
                         "Value of parameter 'Description' must be of type: dict. Received: {}".format(DESCRIPTION + 'new'))
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, Description=DESCRIPTION)
                assert False, 'Remove known error code'
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='description').response
                assert hasattr(resp, 'description')
                assert resp.description == DESCRIPTION

    def test_T1750_productCodes(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, ProductCode=['1', '2'])
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='productCodes').response
            assert hasattr(resp, 'productCodes')
            assert resp.productCodes == DESCRIPTION + 'new'
            assert False, 'Call should not have been successful'
        except OscApiException as err:
            assert_error(err, 400, 'InvalidProductInfo', None)
            assert err.message in ['The product codes are not valid: 2, 1', 'The product codes are not valid: 1, 2'], 'Incorrect error message'
        finally:
            if ret:
                # todo reset initial product code(s)
                pass

    def test_T1751_att_value(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, Attribute='description', Value=DESCRIPTION + 'new')
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='description').response
            assert hasattr(resp, 'description')
            assert resp.description == DESCRIPTION + 'new'
        except OscApiException as error:
            assert_error(error, 400, 'OWS.Error', 'Request is not valid.')
        finally:
            if ret:
                pass

    def test_T1752_op_type(self):
        ret = None
        try:
            ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, OperationType='add',
                                                      UserId=[str(self.a2_r1.config.account.account_id), str(self.a1_r1.config.account.account_id)])
            assert ret.response.osc_return
            resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
            assert hasattr(resp, 'launchPermission')
            assert isinstance(resp.launchPermission, list)
            assert len(resp.launchPermission) == 2
            assert hasattr(resp.launchPermission[0], 'userId')
            assert hasattr(resp.launchPermission[1], 'userId')
            user_ids = [perm.userId for perm in resp.launchPermission]
            assert self.a1_r1.config.account.account_id in user_ids
            assert self.a2_r1.config.account.account_id in user_ids
        finally:
            if ret:
                ret = self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, OperationType='remove',
                                                          UserId=[str(self.a2_r1.config.account.account_id),
                                                                  str(self.a1_r1.config.account.account_id)])
                assert ret.response.osc_return
                resp = self.a1_r1.fcu.DescribeImageAttribute(ImageId=self.image_id, Attribute='launchPermission').response
                assert hasattr(resp, 'launchPermission')
                assert not resp.launchPermission

    def test_T3086_valid_product_code(self):
        product_code = ['0002']
        self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, ProductCode=product_code)
        ret = self.a1_r1.fcu.DescribeImages(ImageId=self.image_id)
        assert len(ret.response.imagesSet[0].productCodes) == 1
        assert ret.response.imagesSet[0].productCodes[0].productCode == product_code[0]

    def test_T3087_multiple_valid_product_code(self):
        product_codes = ['0001', '0002', '0003', '0004', '0005']
        product_types = {'0001': 'Linux/UNIX', '0002': 'Windows', '0003': 'MapR', '0004': 'LINUX ORACLE', '0005': 'Windows 10'}
        self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, ProductCode=product_codes)
        ret = self.a1_r1.fcu.DescribeImages(ImageId=self.image_id)
        for i in range(5):
            assert ret.response.imagesSet[0].productCodes[i].type == product_types[ret.response.imagesSet[0].productCodes[i].productCode]

    def test_T3088_invalid_product_code(self):
        try:
            product_code = ['0009']
            self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, ProductCode=product_code)
        except OscApiException as err:
            assert_error(err, 400, 'InvalidProductInfo', 'The product codes are not valid: 0009')

    def test_T3089_empty_product_code(self):
        try:
            product_code = ['']
            self.a1_r1.fcu.ModifyImageAttribute(ImageId=self.image_id, ProductCode=product_code)
        except OscApiException as err:
            assert_error(err, 400, 'MissingParameter', 'Parameter cannot be empty: ProductCodes')
