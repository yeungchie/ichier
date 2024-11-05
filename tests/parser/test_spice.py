from textwrap import dedent

from ichier.parser.spice import fromString
from ichier import Module


class TestSpiceParser:
    def test_dollar_comment(self):
        code = """\
        $ This is a dollar comment
        .SUBCKT buf in out
        $ This is another dollar comment
        i0 / inv $PINS in=in out=net1
        i1 / inv $PINS in=net1 out=out
        .ENDS
        """

        code = dedent(code)
        design = fromString(code)
        assert isinstance(design.modules["buf"], Module)
        assert design.modules["buf"].instances["i0"].reference == "inv"
        assert design.modules["buf"].instances["i1"].reference == "inv"
        assert design.modules["buf"].instances["i0"].connection == {
            "in": "in",
            "out": "net1",
        }
        assert design.modules["buf"].instances["i1"].connection == {
            "in": "net1",
            "out": "out",
        }
