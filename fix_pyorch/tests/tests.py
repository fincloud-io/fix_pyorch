import re
import yaml
from fix_pyorch.message_spec import Repository
from fix_pyorch.message import Message
import unittest

initialised = False

static_test_data = [
    "8=FIX.4.49=7535=A49=ICE34=152=20200323-22:55:02.50041756=11057=498=0108=30141=Y10=253",
    "8=FIX.4.49=5835=049=ICE34=6552=20200323-23:14:03.67247856=11057=410=239",
]

test_cases = ["Logon", "Heartbeat"]


class TestBasicRepositorySpecFunctions(unittest.TestCase):

    def __init__(self, methodName: str = ...):
        super().__init__(methodName)
        self.repo = None
        self.raw_data = None
        self.LINE_PARSER = None
        self.test_messages = None
        self.initialised = False

    def setUp(self):
        if not self.initialised:
            with open(r'config_test.yml') as file:
                config = yaml.load(file, Loader=yaml.Loader)
            self.repo = Repository.parse_repository(config['repository'])
            if config.get('test_data', None):
                with open(config.get('test_data')) as file:
                    self.raw_data = file.readlines()
                self.LINE_PARSER = re.compile(config['line_regex'])
            self.test_messages = []
            self.initialised = True

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
            self.assertEqual(msg.get_field_by_id(35).value_name(), test_cases[i])

    def test_message_parsing(self):
        for line in self.raw_data:
            grp = self.LINE_PARSER.match(line)
            if not grp:
                continue
            msg = Message.parse(grp['message'], self.repo)
            if msg.is_admin():
                continue
            #self.test_messages.append(msg)
        #for msg in self.test_messages:
            #print(msg)
        #print(test_messages)


if __name__ == '__main__':
    unittest.main()
