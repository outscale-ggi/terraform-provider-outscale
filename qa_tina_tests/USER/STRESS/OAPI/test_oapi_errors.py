import time

from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_pub import osc_api
from qa_sdk_pub.osc_api import disable_throttling
from qa_test_tools.error import load_errors, error_type
from qa_test_tools.exceptions.test_exceptions import OscTestException
from qa_test_tools.test_base import OscTestSuite


CALL_NUMBER = 2000


class Test_oapi_errors(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_oapi_errors, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_oapi_errors, cls).teardown_class()

    def test_T3989_load_errors_internet_service(self):

        disable_throttling()
        start = time.time()
        call_number = 0
        errs = load_errors()
        for _ in range(CALL_NUMBER):
            net_id = None
            try:
                call_number += 1
                ret = self.a1_r1.oapi.CreateInternetService(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                net_id = ret.response.InternetService.InternetServiceId
            except OscApiException as error:
                errs.handle_api_exception(error, error_type.Create)
            except OscTestException as error:
                errs.add_unexpected_error(error, error_type.Create)
            finally:
                try:
                    if not net_id:
                        call_number += 1
                        ret = self.a1_r1.oapi.ReadInternetServices(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.InternetServices
                        if ret and len(ret) == 1:
                            net_id = ret[0].InternetServiceId
                except Exception:
                    print("Could not get created pub_ip with error.")
                if net_id:
                    try:
                        call_number += 1
                        self.a1_r1.oapi.DeleteInternetService(InternetServiceId=net_id, exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                        net_id = None
                    except OscApiException as error:
                        errs.handle_api_exception(error, error_type.Delete)
                    except OscTestException as error:
                        errs.add_unexpected_error(error, error_type.Delete)
                    finally:
                        try:
                            call_number += 1
                            ret = self.a1_r1.oapi.ReadInternetServices(exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0}).response.InternetServices
                            if not ret:
                                net_id = None
                        except Exception:
                            print("Could not get deleted pub_ip with error.")
                if net_id:
                    try:
                        call_number += 1
                        self.a1_r1.oapi.DeleteInternetService(PublicIp=net_id, exec_data={osc_api.EXEC_DATA_MAX_RETRY: 0})
                    except Exception:
                        print("Could not release address.")

        end = time.time()
        print("*************")
        print("call number = {}".format(call_number))
        print('time = {}'.format(end - start))
        errs.print_errors()
        errs.assert_errors()
