import string
from typing import Generator, List
from _pytest.fixtures import SubRequest
import pytest

from specs import check_tools
from qa_sdk_common.exceptions.osc_exceptions import OscApiException
from qa_sdk_common.objects.osc_objects import OscObject
from qa_test_tools.misc import id_generator
from qa_tina_tools.test_base import OscTinaTest


class Test_ReadDirectLinks(OscTinaTest):

    @classmethod
    def setup_class(cls):
        cls.quotas = {'dl_connection_limit': 2}
        super(Test_ReadDirectLinks, cls).setup_class()

    # simple fixture: create 1 DirectLink
    @pytest.fixture(scope="class")
    def direct_link(self) -> OscObject:
        self.logger.debug("Create DirectLink")
        direct_link = None
        location = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
        direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
        direct_link = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location, Bandwidth='1Gbps').response.DirectLink
        self.logger.debug(direct_link.display())
        yield direct_link
        self.logger.debug("Delete DirectLink")
        self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link.DirectLinkId)

    # fixture with param (need parametrize with indirect): create n DirectLink
    @pytest.fixture(scope="class")
    def direct_link_list(self, request:SubRequest) -> List[OscObject]:
        self.logger.debug("Create DirectLink list")
        count = request.param
        direct_link_list = []
        location = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
        for _ in range(count):
            direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
            direct_link = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location, Bandwidth='1Gbps').response.DirectLink
            self.logger.debug(direct_link.display())
            direct_link_list.append(direct_link)
        yield direct_link_list
        self.logger.debug("Delete DirectLink list")
        for direct_link in direct_link_list:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link.DirectLinkId)

    # factory as fixture: return a 'DirectLink' generator
    @pytest.fixture(scope="class")
    def direct_link_factory(self) -> Generator:
        self.logger.debug("Init DirectLink Factory")
        direct_link_list = []
        location = self.a1_r1.oapi.ReadLocations().response.Locations[0].Code
        def _direct_link_factory() -> OscObject:
            direct_link_name = id_generator(size=8, chars=string.ascii_lowercase)
            direct_link = self.a1_r1.oapi.CreateDirectLink(DirectLinkName=direct_link_name, Location=location, Bandwidth='1Gbps').response.DirectLink
            self.logger.debug(direct_link.display())
            direct_link_list.append(direct_link)
            return direct_link
        yield _direct_link_factory
        self.logger.debug("Cleanup DirectLink Factory")
        for direct_link in direct_link_list:
            self.a1_r1.oapi.DeleteDirectLink(DirectLinkId=direct_link.DirectLinkId)

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T3904_empty_filters(self, direct_link_list:List[OscObject]):
        dl_list = self.a1_r1.oapi.ReadDirectLinks().response.DirectLinks
        assert len(dl_list) == 2
        assert direct_link_list[0].DirectLinkId in [dl.DirectLinkId for dl in dl_list]
        assert direct_link_list[1].DirectLinkId in [dl.DirectLinkId for dl in dl_list]

    #@pytest.mark.parametrize("direct_link_ids", [['dxcon-12345678'], ['foo'], [], "foo", True, None])
    #@pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    #def test_T3905_filters_direct_link_ids_invalid_value(self, direct_link_list:list[OscObject], direct_link_ids:list):
    #    _ = direct_link_list # fix Pylint: Unused argument
    #    dl_list = self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': direct_link_ids}).response.DirectLinks
    #    assert len(dl_list) == 0

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T3905_filters_direct_link_ids_not_exist(self, direct_link_list:List[OscObject]):
        _ = direct_link_list # fix Pylint: Unused argument
        dl_list = self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': ['dxcon-12345678']}).response.DirectLinks
        assert len(dl_list) == 0

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T6076_filters_direct_link_ids_invalid_value(self, direct_link_list:List[OscObject]):
        _ = direct_link_list # fix Pylint: Unused argument
        dl_list = self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': ['foo']}).response.DirectLinks
        assert len(dl_list) == 0

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T6077_filters_direct_link_ids_empty_list(self, direct_link_list:List[OscObject]):
        _ = direct_link_list # fix Pylint: Unused argument
        dl_list = self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': []}).response.DirectLinks
        assert len(dl_list) == 0

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T6078_filters_direct_link_ids_valid(self, direct_link_list:List[OscObject]):
        dl_list = self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': [direct_link_list[0].DirectLinkId]}).response.DirectLinks
        assert len(dl_list) == 1
        assert direct_link_list[0].DirectLinkId in [dl.DirectLinkId for dl in dl_list]

    #@pytest.mark.parametrize("direct_link_ids", [True, None])
    #@pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    #def test_T0000_filters_direct_link_ids_invalid_param(self, direct_link_list:list[OscObject], direct_link_ids):
    #    _ = direct_link_list # fix Pylint: Unused argument
    #    with pytest.raises(OscApiException) as error:
    #        self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': direct_link_ids})
    #    check_tools.check_oapi_error(error.value, 4110)

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T6079_filters_direct_link_ids_invalid_type_str(self, direct_link_list:List[OscObject]):
        _ = direct_link_list # fix Pylint: Unused argument
        with pytest.raises(OscApiException) as error:
            self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': "foo"})
        check_tools.check_oapi_error(error.value, 4110)

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T6080_filters_direct_link_ids_invalid_type_bool(self, direct_link_list:List[OscObject]):
        _ = direct_link_list # fix Pylint: Unused argument
        with pytest.raises(OscApiException) as error:
            self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': True})
        check_tools.check_oapi_error(error.value, 4110)

    @pytest.mark.parametrize("direct_link_list", [2], indirect=True)
    def test_T6081_filters_direct_link_ids_none(self, direct_link_list:List[OscObject]):
        _ = direct_link_list # fix Pylint: Unused argument
        with pytest.raises(OscApiException) as error:
            self.a1_r1.oapi.ReadDirectLinks(Filters={'DirectLinkIds': None})
        check_tools.check_oapi_error(error.value, 4110)
