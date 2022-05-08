import re
from collections import UserList

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

    def to_json(self):
        return '"{}":"{}"'.format(self.tag_name(), self.value_name())

    def __str__(self):
        return '{} : {} '.format(self.tag, self.val)


class Group(FIXObject):
    def __init__(self, repo, parent_context, field):
        if isinstance(parent_context, GroupList):
            spec = parent_context.num_items_field.spec.get_associated_group_spec()
        else:
            spec = parent_context.spec
        FIXObject.__init__(self, repo, spec)
        self.elements = []
        self.elements.append(field)
        self.parent_context = parent_context

    def contains(self, field):
        for ref in self.spec.spec.fieldRef:
            if int(ref.get('id')) == field.tag:
                return True
        return False

    def get_group_begin_field_id(self):
        return int(self.spec.spec.fieldRef[0].get('id'))

    def add_element(self, pair):
        self.elements.append(pair)

    def get_num_field_id(self):
        self.spec.numInGroup.get('id')

    def get_first_field_id(self):
        self.spec.fieldRef[0].get('id')

    def to_json(self):
        json = '{'
        for el in self.elements:
            json += el.to_json() + ','
        return json[:-1]+'}'

    def __str__(self):
        display = ''
        for element in self.elements:
            display += str(element)+', '
        return '['+display+']'


class GroupList(UserList, FIXObject):
    def __init__(self, repo, parent_context, num_items_field):
        FIXObject.__init__(self, repo, num_items_field.spec.get_associated_group_spec())
        UserList.__init__(self)
        self.num_items_field = num_items_field
        self.parent_context = parent_context

    def contains(self, field):
        for ref in self.spec.spec.fieldRef:
            if ref.get('id') == field.tag:
                return True
        return False

    def get_group_begin_field_id(self):
        return int(self.spec.spec.fieldRef[0].get('id'))

    def add_element(self, element):
        self.append(element)

    def to_json(self):
        json = ""
        for el in self.data:
            json += el.to_json() + ','
        return '"{0}":[{1}]'.format(self.spec.name(), json[:-1])

    def __str__(self):
        display = ''
        for element in self.data:
            display += str(element)+', '
        return '['+display+']'


class Message(FIXObject):
    def __init__(self, repo, field, pre_header):
        FIXObject.__init__(self, repo, repo.message_spec_bytype(field.val))
        self._elements = pre_header
        self._elements.append(field)
        self.parent_context = None

    def contains(self, field):                   # All fields are in context at message level (dont validate at this point)
        return True

    def get_group_begin_field_id(self):
        return False

    def add_element(self, element):
        self._elements.append(element)

    def is_admin(self):
        return self.spec.category() == "Session"

    def get_tag_by_id(self, tag):
        val = None
        for field in self._elements:
            if field.tag == tag:
                val = field.val
                break
        return val

    def to_json(self):
        json = '{'
        for el in self._elements:
            json += el.to_json() + ','
        return json[:-1]+'}'

    def __str__(self):
        out = ""
        for element in self._elements:
            out += str(element)
        return out

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
        if field.spec is None:
            # print('Processing unknown tag: {0}'.format(field))
            context.add_element(field)
            return context
        elif field.spec.is_num_in_group():                      # is this is the start of a group list ?
            group_list = GroupList(repo, context, field)
            context.add_element(group_list)
            return group_list                                   # Change context to the group list

        elif field.tag == context.get_group_begin_field_id():
            if context.contains(field):                         # If the context already contains the begin field, add a sibling
                grp = Group(repo, context.parent_context, field)
                context.parent_context.add_element(grp)
            else:
                grp = Group(repo, context, field)
                context.add_element(grp)
            return grp

        elif not context.contains(field):                       # if the field is not in our context
            while not context.contains(field):
                context = context.parent_context                # check the parent (root accepts all fields)
            return cls.add_field(field, repo, context)

        context.add_element(field)
        return context

