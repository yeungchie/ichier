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

    def test_connect_to_bus_by_identifier(self):
        code = """\
        module cell(in, out);
        input [1:0] in;
        output      out;
        endmodule

        module top(
            input [1:0] in,
            output      out
        );
        cell c0 (.in(in), .out(out));
        endmodule
        """
        code = dedent(code)
        design = fromString(code)
        top = design.modules["top"]
        top.rebuild(mute=True, verilog_style=True)
        connection = top.instances["c0"].connection
        assert len(connection) == 3
        assert isinstance(connection, dict)
        assert connection["in[0]"] == "in[0]"
        assert connection["in[1]"] == "in[1]"
        assert connection["out"] == "out"
