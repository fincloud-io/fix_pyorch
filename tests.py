import re
import yaml
import fix
from fix.message_spec import Repository
from fix.message import Message
import unittest
import json

initialised = False


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

    def test_lookup_basic_message_spec(self):
        self.assertEqual(self.repo.message_spec_bytype('D').name(), 'NewOrderSingle')

    def test_lookup_basic_message_field_specs(self):
        # New Order Single message has a PartyGroup
        nos = self.repo.message_spec_bytype('D')
        #field_specs = nos.get_field_specs()
        group_specs = nos.get_group_specs()
        self.assertEqual(self.repo.message_spec_bytype('D').name(), 'NewOrderSingle')

    def test_message_parsing(self):
        for line in self.raw_data:
            grp = self.LINE_PARSER.match(line)
            if not grp:
                continue
            msg = Message.parse(grp['message'], self.repo)
            if msg.is_admin():
                continue
            self.test_messages.append(msg)
        for msg in self.test_messages:
            print(msg)
        #print(test_messages)


if __name__ == '__main__':
    unittest.main()
