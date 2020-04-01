from qa_test_tools.test_base import OscTestSuite
import time
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.error import group_errors, error_type


CALL_NUMBER = 2000


class Test_fcu_errors(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_fcu_errors, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_fcu_errors, cls).teardown_class()

    def test_T3992_load_errors_internet_gateway(self):

        start = time.time()
        call_number = 0
        errs = group_errors()
        for _ in range(CALL_NUMBER):
            igw_id = None
            try:
                call_number += 1
                ret = self.a1_r1.fcu.CreateInternetGateway()
                igw_id = ret.response.internetGateway.internetGatewayId
            except OscApiException as error:
                errs.handle_api_exception(error, error_type.Create)
            except OscTestException as error:
                errs.add_unexpected_error(error, error_type.Create)
            finally:
                try:
                    if not igw_id:
                        call_number += 1
                        ret = self.a1_r1.fcu.DescribeInternetGateways().response.internetGatewaySet
                        if ret and len(ret) == 1:
                            igw_id = ret[0].internetGatewayId
                except Exception:
                    print("Could not get created igw_id with error.")
                if igw_id:
                    try:
                        call_number += 1
                        self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)
                        igw_id = None
                    except OscApiException as error:
                        errs.handle_api_exception(error, error_type.Delete)
                    except OscTestException as error:
                        errs.add_unexpected_error(error)
                    finally:
                        try:
                            call_number += 1
                            ret = self.a1_r1.fcu.DescribeInternetGateways().response.internetGatewaySet
                            if not ret:
                                igw_id = None
                        except Exception:
                            print("Could not get deleted igw_id with error.")
                if igw_id:
                    try:
                        call_number += 1
                        self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)
                    except Exception:
                        print("Could not release address.")

        end = time.time()
        print("*************")
        print("call number = {}".format(call_number))
        print('time = {}'.format(end - start))
        errs.print_errors()
        errs.assert_errors()
