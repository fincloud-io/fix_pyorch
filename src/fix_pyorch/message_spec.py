from lxml import objectify


class Repository:
    def __init__(self, tree):
        _root = tree.getroot()
        self.messages = self._populate_message_specs(_root.messages)
        self.fields = self._populate_field_specs(_root.fields)
        self.groups = self._populate_group_specs(_root.groups)
        self.components = _root.components
        self.codeSets = self._populate_codeset_specs(_root.codeSets)

    def _populate_message_specs(self, messages):
        specs_by_type = {}
        for m in messages.message:
            spec = MessageSpec(self, m)
            specs_by_type[spec.msgType()] = spec
        return specs_by_type

    def _populate_field_specs(self, fields):
        specs_by_id = {}
        for f in fields.field:
            spec = FieldSpec(self, f)
            specs_by_id[spec.id()] = spec
        return specs_by_id

    def _populate_group_specs(self, groups):
        specs_by_id = {}
        for f in groups.group:
            spec = GroupSpec(self, f)
            specs_by_id[spec.id()] = spec
        return specs_by_id

    def _populate_codeset_specs(self, codeSets):
        specs_by_id = {}
        for c in codeSets.codeSet:
            spec = CodeSetSpec(self, c)
            specs_by_id[spec.id()] = spec
        return specs_by_id

    def message_spec_bytype(self, _type):
        return self.messages.get(_type, None)

    def codeset_spec_byid(self, _id):
        return self.codeSets.get(str(_id), None)

    def field_spec_byid(self, _id):
        return self.fields.get(str(_id), None)

    def group_spec_byid(self, _id):
        return self.groups.get(str(_id), None)

    @classmethod
    def parse_repository(cls, repo_file):
        return Repository(objectify.parse(repo_file))


class ObjectSpec:
    def __init__(self, repo, spec):
        self.repo = repo
        self.spec = spec

    def name(self):
        return self.spec.get('name')

    def id(self):
        return self.spec.get('id')

    def type(self):
        return self.spec.get('type')


class CodeSetSpec(ObjectSpec):
    def __init__(self, repo, codeset_spec):
        ObjectSpec.__init__(self, repo, codeset_spec)


class MessageSpec(ObjectSpec):
    def __init__(self, repo, message_spec):
        ObjectSpec.__init__(self, repo, message_spec)

    def msgType(self):
        return self.spec.get('msgType')

    def category(self):
        return self.spec.get('category')

    def get_field_specs(self):
        specs = []
        for fr in self.spec.structure.fieldRef:
            _id = fr.attrib.get('id', None)
            specs.append(self.repo.field_spec_byid(_id))
        return specs

    def get_group_specs(self):
        specs = []
        for gr in self.spec.structure.groupRef:
            _id = gr.attrib.get('id', None)
            specs.append(self.repo.group_spec_byid(_id))
        return specs

    def get_group_spec_byname(self, name):
        for gr in self.spec.structure.groupRef:
            _name = gr.attrib.get('name', None)
            if _name == name:
                return gr
        return None


class FieldSpec(ObjectSpec):
    def __init__(self, repo, field_spec):
        ObjectSpec.__init__(self, repo, field_spec)

    def is_num_in_group(self):
        if self.type() == "NumInGroup":
            return True
        enum = self.get_codeset_spec()
        if enum and enum.type() == "NumInGroup":
            return True

    def get_codeset_spec(self):
        return self.repo.codeset_spec_byid(self.id())


class GroupSpec(ObjectSpec):
    def __init__(self, repo, group_spec):
        ObjectSpec.__init__(self, repo, group_spec)

    def get_num_field_spec(self):
        return self.repo.field_spec_byid(self.get_num_field_id())

    def get_num_field_id(self):
        return self.spec.numInGroup.get('id')

    def get_field_specs(self):
        specs = []
        try :
            for fr in self.spec.fieldRef:
                _id = fr.attrib.get('id', None)
                specs.append(self.repo.field_spec_byid(_id))
        except AttributeError:
            pass
        return specs

    def get_group_specs(self):                                      # Nested groups
        specs = []
        try :
            for gr in self.spec.groupRef:
                _id = gr.attrib.get('id', None)
                specs.append(self.repo.group_spec_byid(_id))
        except AttributeError:
            pass
        return specs
