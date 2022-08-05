import re
from collections import UserList
import json

TAG_VALUE_MATCH = r'(?P<tag>\d+)=(?P<value>.*?)\u0001'


class FIXObject:
    def __init__(self, repo, spec):
        self.spec = spec
        self._repo = repo


class Field(FIXObject):
    def __init__(self, tag, val, repo):
        FIXObject.__init__(self, repo, repo.field_spec_byid(tag))
        self.tag = int(tag)
        self.val = val

    def is_mesg_type(self):
        return self.tag == 35

    def tag_name(self):
        return self.spec.name() if self.spec else str(self.tag)

    def value_name(self):
        if not self.spec:
            return self.val
        val_name = self.val
        field_enum = self.spec.get_field_enumeration()
        if field_enum:
            for c in field_enum.spec.code:
                if c.attrib['value'] == self.val:
                    return c.attrib['name']
        return val_name

    def _to_json_string(self):
        return '"{}":"{}"'.format(self.tag_name(), self.value_name())

    def __str__(self):
        return self._to_json_string()


class Group(FIXObject):
    def __init__(self, repo, list_context, field):
        FIXObject.__init__(self, repo, list_context.spec)
        self.elements = []
        self.elements.append(field)
        self.parent_context = list_context
        list_context.add_element(self)

    def get_group_begin_field_id(self):
        return int(self.spec.spec.fieldRef[0].get('id'))

    def add_element(self, pair):
        self.elements.append(pair)

    def contains(self, pair):
        for e in self.elements:
            if not isinstance(e, Field):
                continue
            if e.tag == pair.tag:
                return True
        return False

    def get_num_field_id(self):
        self.spec.numInGroup.get('id')

    def get_first_field_id(self):
        self.spec.fieldRef[0].get('id')

    def _to_json_string(self):
        json_string = '{'
        for el in self.elements:
            json_string += el._to_json_string() + ','
        return json_string[:-1]+'}'

    def __str__(self):
        return self._to_json_string()


class GroupList(UserList, FIXObject):
    def __init__(self, repo, parent_context, num_items_field, group_specs):
        FIXObject.__init__(self, repo, self.get_associated_group_spec(num_items_field, group_specs))
        UserList.__init__(self)
        self.num_items_field = num_items_field
        self.parent_context = parent_context
        parent_context.add_element(self)

    def get_associated_group_spec(self, num_items_field, group_specs):
        for g in group_specs:
            if int(g.get_num_field_spec().id()) == num_items_field.tag:
                return g
        return None

    def get_group_begin_field_id(self):
        return int(self.spec.spec.fieldRef[0].get('id'))

    def add_element(self, element):
        self.append(element)

    def _to_json_string(self):
        json_string = ""
        for el in self.data:
            json_string += el._to_json_string() + ','
        return '"{0}":[{1}]'.format(self.spec.name(), json_string[:-1])

    def __str__(self):
        self._to_json_string()


class Message(FIXObject):
    def __init__(self, repo, field, pre_header):
        FIXObject.__init__(self, repo, repo.message_spec_bytype(field.val))
        self._elements = pre_header
        self._elements.append(field)
        self.parent_context = None

    def get_group_begin_field_id(self):
        return False

    def add_element(self, element):
        self._elements.append(element)

    def is_admin(self):
        return self.spec.category() == "Session"

    def get_field_by_id(self, _id):             # does not get repeating group fields..
        for el in self._elements:
            if isinstance(el, Field) and el.tag == _id:
                return el
        return None

    def _to_json_string(self):
        json_string = '{'
        for el in self._elements:
            json_string += el._to_json_string() + ','
        return json_string[:-1]+'}'

    def to_json(self):
        return json.loads(self._to_json_string())

    def __str__(self):
        return self._to_json_string()

    @classmethod
    def parse(cls, msg_string, repo):
        pre_header = []
        msg = None
        context = None
        for match in re.finditer(TAG_VALUE_MATCH, msg_string):
            field = Field(match.group('tag'), match.group('value'), repo)
            if field.is_mesg_type():
                msg = Message(repo, field, pre_header)
                context = msg
            elif not msg:
                pre_header.append(field)
                continue
            else:
                context = cls.add_field(field, repo, context)
        return msg

    @classmethod
    def add_field(cls, field, repo, context):
        if field.spec is None:                                  # tag not in repo (prob custom field)
            # print('Processing unknown tag: {0}'.format(field))
            context.add_element(field)
            return context

        elif field.spec.is_num_in_group():                  # start of a group list ?
            while not context.spec.in_spec(field):          # traverse upwards
                context = context.parent_context
            return GroupList(repo, context, field, context.spec.get_group_specs())

        else:                                               # context is grouplist / group
            if context.spec.in_spec(field):                 # field is in context
                if isinstance(context, GroupList):          # if we are in a GroupList,
                    return Group(repo, context, field)
                elif isinstance(context, Group):            # if we are in a group
                    if context.contains(field):             # is field is already present
                        return Group(repo, context.parent_context, field)
                context.add_element(field)
                return context
            else:                                           # field NOT in context
                while not context.spec.in_spec(field):      # traverse upwards
                    context = context.parent_context
                return cls.add_field(field, repo, context)
