from ichier.parser import fromVerilogCode


class TestMakeModule:
    def test_make_module(self):
        code = """\
        module inv (in, out);
        input       in;
        output      out;
        endmodule


        module buf (in, out);
        input       in;
        output      out;
        wire        net;

        inv i0 (.in(in), .out(net));
        inv i1 (.in(net), .out(out));
        endmodule


        module buf2 (in, out);
        input           in;
        output  [1:0]   out;

        buf b0 (.in(in), .out(out[0]));
        buf b1 (.in(in), .out(out[1]));
        endmodule


        module buf4 (in, out);
        input           in;
        output  [3:0]   out;

        buf b0 (.in(in), .out(out[0]));
        buf b1 (.in(in), .out(out[1]));
        buf b2 (.in(in), .out(out[2]));
        buf b3 (.in(in), .out(out[3]));
        endmodule
        """
        design = fromVerilogCode(code)
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
