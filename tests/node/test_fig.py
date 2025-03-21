from ichier.node import (
    Design,
    Module,
    ModuleCollection,
    Instance,
    InstanceCollection,
    NetCollection,
    TerminalCollection,
    ParameterCollection,
)


class TestFig:
    def test_create_design(self):
        name = "design"
        d = Design(name)
        assert d.name == name
        assert isinstance(d, Design)
        assert isinstance(d.modules, ModuleCollection)
        assert isinstance(d.parameters, ParameterCollection)

    def test_create_module(self):
        name = "module"
        m = Module(name)
        assert m.name == name
        assert isinstance(m, Module)
        assert isinstance(m.instances, InstanceCollection)
        assert isinstance(m.terminals, TerminalCollection)
        assert isinstance(m.nets, NetCollection)
        assert isinstance(m.parameters, ParameterCollection)

    def test_create_instance(self):
        name = "instance"
        i = Instance("module", name)
        assert i.name == name
        assert i.reference == "module"
        assert isinstance
