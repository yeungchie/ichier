from textwrap import dedent
import re

from ichier.parser.verilog import fromCode, PreProc


class TestSpiceParser:
    def test_define_port_dir_in_head(self):
        code = """\
        module and2(
            input [1:0] in,
            output      out
        );
        wire net1;

        nand2   i0(in, net1);
        inv     i1(net1, out);
        endmodule
        """
        code = dedent(code)
        design = fromCode(code)
        design.modules.rebuild(mute=True, verilog_style=True)
        and2 = design.modules["and2"]
        assert and2.terminals["in[0]"].direction == "input"
        assert and2.terminals["in[1]"].direction == "input"
        assert and2.terminals["out"].direction == "output"
        assert set(map(str, and2.nets.figs)) == {"in[0]", "in[1]", "net1", "out"}

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
        design = fromCode(code)
        top = design.modules["top"]
        top.rebuild(mute=True, verilog_style=True)
        connection = top.instances["c0"].connection
        assert len(connection) == 3
        assert isinstance(connection, dict)
        assert connection["in[0]"] == "in[0]"
        assert connection["in[1]"] == "in[1]"
        assert connection["out"] == "out"

    def test_pre_proc(self):
        code = """\
        /*
         * comment
         */
        wire  [3:0] a;
        wire  b1, b2, b3;
        wire  /* comment */
              [1:0] c;
        wire  d;
        wire  e1  /* comment */,
              e2;
        """
        code = PreProc.process(dedent(code))
        assert code == re.sub(
            r"^-+",
            "",
            """\
------------
------------
------------
------------wire  [3:0] a;
------------
------------wire  
------------      [1:0] c;
------------
------------
------------
------------""",
            flags=re.MULTILINE,
        )
