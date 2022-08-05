import argparse
import re
from fix_pyorch import Message, Repository

LINE_PARSER = re.compile('(?P<timestamp>[0-9]{8}-[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{2,9}) : (?P<message>.*)')


def convert_to_json(file, repo, no_admin_messages):
    messages = parse_messages(file, repo, no_admin_messages)
    msgs = []
    for msg in messages:
        msgs.append(msg.to_json())
    return str(msgs)


def parse_messages(file, repo, no_admin_messages):
    messages = []
    with open(file, 'r') as fh:
        for line in fh.readlines():
            grp = LINE_PARSER.match(line)
            if not grp:
                continue
            msg = Message.parse(grp['message'], repo)
            if no_admin_messages and msg.is_admin():
                continue
            messages.append(msg)
    return messages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert fix message file to json')
    parser.add_argument('file', type=str, nargs='+', help='json file to parse')
    parser.add_argument("--repository", help="FIX Orchestra repository file")
    parser.add_argument("-na","--no_admin_messages", help="Skip admin messages on parsing", action="store_true")
    args = parser.parse_args()
    _repo = Repository.parse_repository(args.repository if args.repository else './FixRepository44.xml')
    for f in args.file:
        print(convert_to_json(f, _repo, args.no_admin_messages))
