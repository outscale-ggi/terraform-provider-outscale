from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from specs import check_oapi_error
from qa_test_tools.config.configuration import Configuration
from qa_test_tools.misc import assert_dry_run
from qa_test_tools.test_base import known_error
from qa_tina_tools.test_base import OscTinaTest
from qa_tina_tools.tools.tina.wait_tools import wait_vpcs_state


class Test_CreateNet(OscTinaTest):

    @classmethod
    def setup_class(cls):
        super(Test_CreateNet, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(Test_CreateNet, cls).teardown_class()

    def test_T2232_valid_params(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16')).response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2233_valid_params_dry_run(self):
        ret = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), DryRun=True)
        assert_dry_run(ret)

    def test_T2384_without_params(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet().response.Net.NetId
            assert False, "call should not have been successful, bad number of parameter"
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        except OscApiException as err:
            check_oapi_error(err, 7000)
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2385_with_unknown_param(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), toto='toto').response.Net.NetId
            assert False, "call should not have been successful, bad parameter"
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        except OscApiException as err:
            check_oapi_error(err, 3001)

        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2386_with_valid_tenancy(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='dedicated').response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2387_with_invalid_tenancy(self):
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='toto').response.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        except OscApiException as err:
            check_oapi_error(err, 4047)

        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2388_with_different_dryrun_strings(self):
        tested_values = [['kjg', False], ['False', False], ['True', False], ['true', True], ['True', False]]
        net_ids = []
        try:
            for val in tested_values:
                net_id = None
                ret = None
                ret = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), DryRun=val[0])
                if val[1]:
                    assert_dry_run(ret)
                else:
                    assert ret.response.Net.NetId
                    net_id = ret.response.Net.NetId
                    net_ids.append(net_id)
                    wait_vpcs_state(self.a1_r1, [net_id], state='available')
        except OscApiException as err:
            # DryRun value is a Bool, String doesn't work into DryRun.
            check_oapi_error(err, 4110)
        finally:
            if net_ids:
                for net_id in net_ids:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2389_verify_response_content(self):
        net_id = None
        try:
            resp = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', '10_0_0_0_16'), Tenancy='default').response
            net_id = resp.Net.NetId
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
            assert hasattr(resp.Net, 'DhcpOptionsSetId'), 'DhcpOptionsSetId does not exist in the response'
            assert hasattr(resp.Net, 'IpRange'), 'IpRange does not exist in the response'
            assert hasattr(resp.Net, 'NetId'), 'NetId does not exist in the response'
            assert hasattr(resp.Net, 'State'), 'State does not exist in the response'
            assert hasattr(resp.Net, 'Tags'), 'Tags does not exist in the response'
            for tag in resp.Net.Tags:
                assert hasattr(tag, 'Key'), 'Key does not exist in the tag'
                assert hasattr(tag, 'Value'), 'Value does not exist in the tag'
            assert hasattr(resp.Net, 'Tenancy') and resp.Net.Tenancy in ['default', 'dedicated'], 'Tenancy does not exist in the response'
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2390_with_valid_iprange(self):
        net_ids = []
        try:
            for addr in ['10_0_0_0_16', '1_0_0_0_16', '10_0_0_0_16', '172_16_0_0_16', '192_168_0_0_24']:
                net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc', addr)).response.Net.NetId
                wait_vpcs_state(self.a1_r1, [net_id], state='available')
                net_ids.append(net_id)
        finally:
            if net_ids:
                for net_id in net_ids:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)

    def test_T2391_with_invalid_iprange(self):
        net_id = None
        try:
            cidrblock = Configuration.get('vpc_invalid', '158_8_4_21_29')
            net_id = self.a1_r1.oapi.CreateNet(IpRange=cidrblock).response.Net.NetId
            assert False, 'Call should not have been successful, Invalid IpRange'
        except OscApiException as error:
            assert error.data == \
                "The provided value ('{cidrBlock}') for the parameter 'IpRange' is invalid. The block size has to be between {min} and {max}."
            known_error('GTW-XXXX', 'Incorrect error message')
            check_oapi_error(error, 4014, cidrBlock=cidrblock, min='/28', max='/16')
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    print('Could not delete net')
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc_invalid', '0_0_0_0_17')).response.Net.NetId
            assert False, 'Invalid IpRange'
            wait_vpcs_state(self.a1_r1, [net_id], state='available')
        except OscApiException as err:
            check_oapi_error(err, 9050)
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    print('Could not delete net')
        net_id = None
        try:
            cidrblock = Configuration.get('vpc_invalid', '255_255_255_0_15')
            net_id = self.a1_r1.oapi.CreateNet(IpRange=cidrblock).response.Net.NetId
            assert False, 'Invalid IpRange'
        except OscApiException as error:
            if error.data != 'The provided value (\'{cidrBlock}\') for the parameter \'IpRange\' is invalid. ' \
                             'The block size has to be between {min} and {max}.':
                assert False, 'Remove known error'
                check_oapi_error(error, 4014, cidrBlock=cidrblock, min='/28', max='/16')
            known_error('TINA-6823', 'Erreur 4014 has a problem with its error message')
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    print('Could not delete net')
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc_invalid', '10_0_0_0_42')).response.Net.NetId
            assert False, 'Invalid IpRange'
        except OscApiException as err:
            check_oapi_error(err, 4047)
        finally:
            if net_id:
                try:
                    self.a1_r1.oapi.DeleteNet(NetId=net_id)
                except:
                    print('Could not delete net')
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc_invalid', '255_255_0_256_16')).response.Net.NetId
            assert False, 'Invalid IpRange'
        except OscApiException as err:
            check_oapi_error(err, 4047)
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)
        net_id = None
        try:
            net_id = self.a1_r1.oapi.CreateNet(IpRange=Configuration.get('vpc_invalid', '105333_0_0_0_16')).response.Net.NetId
            assert False, 'Invalid IpRange'
        except OscApiException as err:
            check_oapi_error(err, 4047)
        finally:
            if net_id:
                self.a1_r1.oapi.DeleteNet(NetId=net_id)
