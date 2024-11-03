from pathlib import Path
from ichier.parser import fromVerilog

verilog = Path(__file__).parent.parent.parent / "tmp" / "netlist" / "buf.v"


class TestMakeModule:
    def test_make_module(self):
        design = fromVerilog(verilog)
        buf4 = design.modules["buf4"]
        buf3 = buf4.makeModule("buf3", instances=["b0", "b1", "b2"])
        assert buf3.name == "buf3"
        assert len(buf3.instances) == 3
        assert buf3.getDesign() is design
        assert buf3.terminals["in"].direction == "input"
        assert buf3.terminals["out[0]"].direction == "output"
        assert buf3.terminals["out[1]"].direction == "output"
        assert buf3.terminals["out[2]"].direction == "output"
        assert {*map(str, buf3.nets)} == {"in", "out[0]", "out[1]", "out[2]"}
