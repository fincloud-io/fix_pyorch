from lxml import objectify


class Repository:
    def __init__(self, tree):
        _root = tree.getroot()
        self.messages = self._populate_message_specs(_root.messages)
        self.fields = self._populate_field_specs(_root.fields)
        self.groups = self._populate_group_specs(_root.groups)
        self.components = self._populate_component_specs(_root.components)
        self.codeSets = self._populate_codeset_specs(_root.codeSets)

    def _populate_component_specs(self, components):
        specs_by_id = {}
        for c in components.component:
            spec = ComponentSpec(self, c)
            specs_by_id[spec.id()] = spec
        return specs_by_id

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

    def group_spec_bynum_field(self, _id):
        for grp in self.groups.values():
            if grp.get_num_field_spec().id() == str(_id):
                return grp
        return None

    def component_spec_byid(self, _id):
        return self.components.get(str(_id), None)

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

    def in_spec(self, field):                   # All fields are in context at message level (dont validate at this point)
        return True

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

    def get_component_specs(self):
        specs = []
        for fr in self.spec.structure.componentRef:
            _id = fr.attrib.get('id', None)
            specs.append(self.repo.component_spec_byid(_id))
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

    def type(self):
        super_type = super().type()
        if super_type[-7:] == 'CodeSet':
            return self.get_field_enumeration().spec.get('type')
        else:
            return super_type

    def is_num_in_group(self):
        return self.type() == "NumInGroup"

    def get_associated_group_spec(self):
        if self.is_num_in_group():
            return self.repo.group_spec_bynum_field(self.id())

    def get_field_enumeration(self):
        return self.repo.codeset_spec_byid(self.id())


class GroupSpec(ObjectSpec):
    def __init__(self, repo, group_spec):
        ObjectSpec.__init__(self, repo, group_spec)

    def in_spec(self, field):
        try:
            if int(self.spec.numInGroup.get('id')) == field.tag:
                return True
            for ref in self.get_field_specs():                                     # Check field against all possible fields
                if int(ref.spec.get('id')) == field.tag:
                    return True
        except AttributeError:
            pass
        try:
            for ref in self.get_component_specs():
                if ref.in_spec(field):
                    return True
        except AttributeError:
            pass

        try:
            for ref in self.get_group_specs():
                if ref.in_spec(field):
                    return True
        except AttributeError:
            pass
        return False

    def get_num_field_spec(self):
        return self.repo.field_spec_byid(self.spec.numInGroup.get('id'))

    def get_field_specs(self):
        specs = []
        for fr in self.spec.fieldRef:
            _id = fr.attrib.get('id', None)
            specs.append(self.repo.field_spec_byid(_id))
        return specs

    def get_group_specs(self):
        specs = []
        for gr in self.spec.groupRef:
            _id = gr.attrib.get('id', None)
            specs.append(self.repo.group_spec_byid(_id))
        return specs

    def get_component_specs(self):
        specs = []
        for gr in self.spec.componentRef:
            _id = gr.attrib.get('id', None)
            specs.append(self.repo.component_spec_byid(_id))
        return specs


class ComponentSpec(ObjectSpec):
    def __init__(self, repo, component_spec):
        ObjectSpec.__init__(self, repo, component_spec)

    def in_spec(self, field):
        for ref in self.get_field_specs():
            if int(ref.spec.get('id')) == field.tag:
                return True
        try:
            for ref in self.get_group_specs():                                                  # Check subgroups for num field..
                if ref.in_spec(field):
                    return True
        except AttributeError:
            pass
        return False

    def get_field_specs(self):
        specs = []
        for fr in self.spec.fieldRef:
            _id = fr.attrib.get('id', None)
            specs.append(self.repo.field_spec_byid(_id))
        return specs

    def get_group_specs(self):
        specs = []
        for gr in self.spec.groupRef:
            _id = gr.attrib.get('id', None)
            specs.append(self.repo.group_spec_byid(_id))
        return specs
