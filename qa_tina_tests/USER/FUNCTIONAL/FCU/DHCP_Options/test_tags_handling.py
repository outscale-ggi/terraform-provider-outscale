import time

from qa_test_tools.test_base import OscTestSuite


class Test_tags_handling(OscTestSuite):

    @classmethod
    def setup_class(cls):
        super(Test_tags_handling, cls).setup_class()

        cls.dhcp_id = None

        try:

            dhcpconf = {'Key': 'domain-name', 'Value': ['outscale.qa']}
            ret = cls.a1_r1.fcu.CreateDhcpOptions(DhcpConfiguration=[dhcpconf])
            cls.dhcp_id = ret.response.dhcpOptions.dhcpOptionsId

        except Exception as error:
            try:
                cls.teardown_class()
            except Exception:
                pass
            raise error

    @classmethod
    def teardown_class(cls):
        try:
            if cls.dhcp_id:
                cls.a1_r1.fcu.DeleteDhcpOptions(DhcpOptionsId=cls.dhcp_id)

        finally:
            super(Test_tags_handling, cls).teardown_class()

    def test_T3309_handle_tags(self):
        self.a1_r1.fcu.CreateTags(ResourceId=self.dhcp_id, Tag=[{'Key': 'key', 'Value': 'value'}])
        # to avoid throttling
        time.sleep(1)
        ret = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [self.dhcp_id]}])
        assert len(ret.response.tagSet) == 1 and ret.response.tagSet[0].resourceId == self.dhcp_id
        ret = self.a1_r1.fcu.DeleteTags(ResourceId=[self.dhcp_id], Tag=[{'Key': 'key', 'Value': 'value'}])
        # to avoid throttling
        time.sleep(1)
        ret = self.a1_r1.fcu.DescribeTags(Filter=[{'Name': 'resource-id', 'Value': [self.dhcp_id]}])
        assert not ret.response.tagSet
