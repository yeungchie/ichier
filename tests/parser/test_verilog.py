from textwrap import dedent

from ichier.parser.verilog import fromString


class TestSpiceParser:
    def test_define_port_dir_in_head(self):
        code = """\
        module buf(
            input [1:0] in,
            output      out
        );
        wire net1;

        inv i0(in, net1);
        inv i1(net1, out);
        endmodule
        """

        code = dedent(code)
        design = fromString(code)
        buf = design.modules["buf"]
        assert buf.terminals["in[0]"].direction == "input"
        assert buf.terminals["in[1]"].direction == "input"
        assert buf.terminals["out"].direction == "output"
        assert set(map(str, buf.nets.figs)) == {"in[0]", "in[1]", "net1", "out"}
