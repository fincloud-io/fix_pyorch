import argparse
import re

from fix_pyorch.message import Message
from fix_pyorch.message_spec import Repository

LINE_PARSER = re.compile('(?P<timestamp>[0-9]{8}-[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3}) : (?P<message>.*)')


def convert_to_json(file, repo):
    messages = []
    with open(file, 'r') as fh:
        for line in fh.readlines():
            grp = LINE_PARSER.match(line)
            if not grp:
                continue
            msg = Message.parse(grp['message'], repo)
            if msg.is_admin():
                continue
            messages.append(msg.to_json())
    for msg in messages:
        print(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert fix message file to json')
    parser.add_argument('file', type=str, nargs='+', help='json file to parse')
    parser.add_argument("--repository", help="FIX Orchestra repository file")
    args = parser.parse_args()
    _repo = Repository.parse_repository(args.repository if args.repository else './FixRepository44.xml')
    for f in args.file:
        convert_to_json(f, _repo)
