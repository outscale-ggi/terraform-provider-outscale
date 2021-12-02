import argparse
import logging
import ssl
from qa_sdks.osc_sdk import OscSdk
from qa_test_tools.config import OscConfig
from qa_test_tools.config import config_constants as constants


setattr(ssl, '_create_default_https_context', getattr(ssl, '_create_unverified_context'))
# ssl._create_default_https_context = ssl._create_unverified_context

LOGGING_LEVEL = logging.DEBUG


def test(args, num, reps):

    logger.info("Initialize environment")
    config = OscConfig.get(account_name=args.account, az_name=args.az, credentials=constants.CREDENTIALS_CONFIG_FILE)
    oscsdk = OscSdk(config=config)

    for _ in range(reps):
        ips = []
        try:
            for _ in range(num):
                ret_alloc = oscsdk.fcu.AllocateAddress()
                ips.append(ret_alloc.response.publicIp)
        except Exception as error:
            print(error)
            raise error
        finally:
            for ip in ips:
                oscsdk.fcu.ReleaseAddress(PublicIp=ip)

if __name__ == '__main__':

    logger = logging.getLogger('allocate_address')

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter('[%(asctime)s] ' +
                          '[%(levelname)8s]' +
                          '[%(threadName)s] ' +
                          '[%(module)s.%(funcName)s():%(lineno)d]: ' +
                          '%(message)s', '%m/%d/%Y %H:%M:%S'))

    logger.setLevel(level=LOGGING_LEVEL)
    logger.addHandler(log_handler)

    logging.getLogger('tools').addHandler(log_handler)
    logging.getLogger('tools').setLevel(level=LOGGING_LEVEL)

    args_p = argparse.ArgumentParser(description="Test platform performances",
                                     formatter_class=argparse.RawTextHelpFormatter)

    args_p.add_argument('-r', '--region-az', dest='az', action='store',
                        required=True, type=str,
                        help='Selected Outscale region AZ for the test')
    args_p.add_argument('-a', '--account', dest='account', action='store',
                        required=True, type=str, help='Set account used for the test')

    main_args = args_p.parse_args()

    print('start')
    test(main_args, 40, 5)
    print('end')
