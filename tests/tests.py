import json
import re
import os
import yaml
from fix_pyorch.message_spec import Repository
from fix_pyorch.message import Message
import unittest

config = None

static_test_data = [
    "8=FIX.4.49=7535=A49=ICE34=152=20200323-22:55:02.50041756=11057=498=0108=30141=Y10=253",
    "8=FIX.4.49=5835=049=ICE34=6552=20200323-23:14:03.67247856=11057=410=239",
    "8=FIXT.1.19=65635=AE34=109049=TRDCAPSOURCE52=20220429-09:55:26.50156=TRDCAPCOMP57=TRDCAPCOMPFIX115=USD17=88888831=8812332=555=PVFV2260=20220429-08:50:0075=20200101150=0423=2568=TrdReq_TRDCAPFIX_20220428-23:24:02571=7d6f27b8-7bc1-4724-b634-3385d0488888748=6828=1854=11003=17788881300=Commodities2343=4552=254=1453=2448=SXYZ447=D452=7448=SXYZ447=D452=30578=TFU336=1625=358=Trace Capture Report Test1057=N2344=454=2453=6448=SQBC447=D452=7448=operations@mybroker.com447=D452=36448=SABC447=D452=30448=CLIENT1447=D452=1448=S777447=D452=4448=XXX447=D452=211=A4 SABC 88888578=TFU336=1625=358=Trader Name1057=N2344=310=079",
    "8=FIX.4.49=23635=634=47249=FCUAT50=jj@fincloud.io52=20220517-08:53:50.62156=XXUAT142=BROKERX IOI22=523=hvrMWbA7t5Fw2m0CeZjBO3___n8uxsXkbQ27=55028=N44=100.048=VOD.L54=255=VOD.L58=hello desk62=20220517-23:59:59130=Y215=1216=1217=XY10=225"
]

test_cases = ["Logon", "Heartbeat", "TradeCaptureReport", "IOI"]


class TestBasicRepositorySpecFunctions(unittest.TestCase):

    def __init__(self, methodName: str = ...):
        super().__init__(methodName)
        self.repo = None
        self.raw_data = None
        self.LINE_PARSER = None
        self.test_messages = None

    def setUp(self):
        global config
        if not config:
            config_location = os.getenv("FIX_PYORCH_TEST_CONFIG", default="config_test.yml")
            print('Loading config .. {0}'.format(config_location))
            with open(config_location) as file:
                config = yaml.load(file, Loader=yaml.Loader)
            if config.get('test_data', None):
                print('Loading test data .. {0}'.format(config.get('test_data')))
                with open(config.get('test_data')) as file:
                    self.raw_data = file.readlines()

        self.LINE_PARSER = re.compile(config['line_regex'])
        self.repo = Repository.parse_repository(config['repository'])

    def test_lookup_basic_field_spec(self):
        self.assertEqual(self.repo.field_spec_byid(11).name(), 'ClOrdID')
        self.assertEqual(self.repo.field_spec_byid(17).name(), 'ExecID')
        self.assertEqual(self.repo.field_spec_byid(37).name(), 'OrderID')
        self.assertEqual(self.repo.field_spec_byid(48).name(), 'SecurityID')
        self.assertEqual(self.repo.field_spec_byid(49).name(), 'SenderCompID')
        self.assertEqual(self.repo.field_spec_byid(50).name(), 'SenderSubID')

    def test_lookup_basic_message_spec(self):
        self.assertEqual(self.repo.message_spec_bytype('D').name(), 'NewOrderSingle')
        self.assertEqual(self.repo.message_spec_bytype('AE').name(), 'TradeCaptureReport')
        self.assertEqual(self.repo.message_spec_bytype('8').name(), 'ExecutionReport')
        self.assertEqual(self.repo.message_spec_bytype('A').name(), 'Logon')
        self.assertEqual(self.repo.message_spec_bytype('0').name(), 'Heartbeat')

    def test_lookup_basic_message_field_specs(self):
        for i, tm in enumerate(static_test_data):
            msg = Message.parse(tm, self.repo)
            json_msg = json.loads(msg.to_json())
            self.assertEqual(msg.get_field_by_id(35).value_name(), test_cases[i])

    def test_message_parsing(self):
        if self.raw_data:
            for line in self.raw_data:
                grp = self.LINE_PARSER.match(line)
                if not grp:
                    continue
                msg = Message.parse(grp['message'], self.repo)
                if msg.is_admin():
                    continue


if __name__ == '__main__':
    unittest.main()
