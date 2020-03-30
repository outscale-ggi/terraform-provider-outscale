from qa_test_tools.test_base import OscTestSuite


class Test_CreateInternetGateway(OscTestSuite):

    def test_T3918_without_params(self):
        igw_id = None
        try:
            ret = self.a1_r1.fcu.CreateInternetGateway().response
            igw_id = ret.internetGateway.internetGatewayId
            assert not ret.internetGateway.tagSet and not ret.internetGateway.attachmentSet
        finally:
            if igw_id:
                self.a1_r1.fcu.DeleteInternetGateway(InternetGatewayId=igw_id)
