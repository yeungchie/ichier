from ichier.node import (
    Design,
    Module,
    ModuleCollection,
    Instance,
    InstanceCollection,
    Net,
    NetCollection,
    Terminal,
    TerminalCollection,
    ParameterCollection,
)


class TestBuf:
    def test_buf(self):
        design = Design(
            name="test_buf",
            modules=[
                Module(
                    name="inv",
                    terminals=[
                        Terminal(name="A", direction="input"),
                        Terminal(name="Z", direction="output"),
                    ],
                ),
                Module(
                    name="buf",
                    terminals=[
                        Terminal(
                            name="A",
                            direction="input",
                        ),
                        Terminal(
                            name="Z",
                            direction="output",
                        ),
                    ],
                    nets=[
                        Net(name="A"),
                        Net(name="Z"),
                        Net(name="inter"),
                    ],
                    instances=[
                        Instance(
                            reference="inv",
                            name="i1",
                            connection={
                                "A": "A",
                                "Z": "Z",
                            },
                            parameters={"size": "x2"},
                        ),
                        Instance(
                            reference="inv",
                            name="i2",
                            connection={
                                "A": "Z",
                                "Z": "A",
                            },
                            parameters={"size": "x4"},
                        ),
                    ],
                ),
            ],
        )
        assert design.name == "test_buf"
        assert isinstance(design.modules, ModuleCollection)

        buf = design.modules["buf"]
        assert buf.name == "buf"
        assert isinstance(buf, Module)
        assert isinstance(buf.terminals, TerminalCollection)
        assert isinstance(buf.nets, NetCollection)
        assert isinstance(buf.instances, InstanceCollection)
        assert isinstance(buf.parameters, ParameterCollection)
        assert len(buf.instances) == 2
        assert len(buf.nets) == 3
        assert len(buf.parameters) == 0

        i1 = buf.instances["i1"]
        assert i1.name == "i1"
        assert isinstance(i1, Instance)
        assert i1.reference == "inv"
        assert i1.parameters["size"] == "x2"
        assert isinstance(i1.collection, InstanceCollection)
        assert i1.collection == buf.instances
        assert i1.collection.parent == buf
