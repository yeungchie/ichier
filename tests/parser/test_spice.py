from textwrap import dedent

from ichier.parser.spice import fromCode
from ichier import Module


class TestSpiceParser:
    def test_dollar_comment(self):
        code = """\
        $ This is a dollar comment
        .SUBCKT buf in out
        $ This is another dollar comment
        X0 / inv $PINS in=in out=net1
        X1 / inv $PINS in=net1 out=out
        .ENDS
        """
        code = dedent(code)
        design = fromCode(code)
        assert isinstance(design.modules["buf"], Module)
        assert design.modules["buf"].instances["X0"].reference == "inv"
        assert design.modules["buf"].instances["X1"].reference == "inv"
        assert design.modules["buf"].instances["X0"].connection == {
            "in": "in",
            "out": "net1",
        }
        assert design.modules["buf"].instances["X1"].connection == {
            "in": "net1",
            "out": "out",
        }

    def test_subckt_parameter(self):
        code = """\
        .SUBCKT module in out a=1 b=2
        .ENDS
        """
        code = dedent(code)
        design = fromCode(code)
        assert tuple(map(str, design.modules["module"].terminals)) == ("in", "out")
        assert design.modules["module"].parameters == {"a": "1", "b": "2"}
