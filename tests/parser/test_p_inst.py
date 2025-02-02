from ichier.parser.spice.p_inst import InstLexer, parse


def expand_token(t):
    return t.type, t.value


class TestSyntax:
    def test_syntax1(self):
        lexer = InstLexer()
        lexer.input("X0 net1 net2 net3 net4 nch m=1 length=4u width=10u")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "net4"),
            ("ID", "nch"),
            ("ASSIGN", ("m", "1")),
            ("ASSIGN", ("length", "4u")),
            ("ASSIGN", ("width", "10u")),
        )
        lexer.input("X0 net1 net2 net3 net4 nch")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "net4"),
            ("ID", "nch"),
        )
        inst = parse("X0 net1 net2 net3 net4 nch m=1 length=4u width=10u")
        assert inst.name == "X0"
        assert inst.reference.name == "nch"
        assert inst.connection == ("net1", "net2", "net3", "net4")
        assert inst.parameters == {"m": "1", "length": "4u", "width": "10u"}

    def test_syntax2(self):
        lexer = InstLexer()
        lexer.input("X0 net1 net2 net3 net4 / nch m=1 length=4u width=10u")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "net4"),
            ("/", "/"),
            ("ID", "nch"),
            ("ASSIGN", ("m", "1")),
            ("ASSIGN", ("length", "4u")),
            ("ASSIGN", ("width", "10u")),
        )
        lexer.input("X0 net1 net2 net3 net4 / nch")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "net4"),
            ("/", "/"),
            ("ID", "nch"),
        )
        inst = parse("X0 net1 net2 net3 net4 / nch m=1 length=4u width=10u")
        assert inst.name == "X0"
        assert inst.reference.name == "nch"
        assert inst.connection == ("net1", "net2", "net3", "net4")
        assert inst.parameters == {"m": "1", "length": "4u", "width": "10u"}

    def test_syntax3(self):
        lexer = InstLexer()
        lexer.input("X0 / nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("/", "/"),
            ("ID", "nch"),
            ("PINS", "$PINS"),
            ("ASSIGN", ("pin1", "net1")),
            ("ASSIGN", ("pin2", "net2")),
            ("ASSIGN", ("pin3", "net3")),
            ("ASSIGN", ("pin4", "net4")),
        )
        lexer.input("X0 nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("ID", "nch"),
            ("PINS", "$PINS"),
            ("ASSIGN", ("pin1", "net1")),
            ("ASSIGN", ("pin2", "net2")),
            ("ASSIGN", ("pin3", "net3")),
            ("ASSIGN", ("pin4", "net4")),
        )
        inst = parse("X0 / nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4")
        assert inst.name == "X0"
        assert inst.reference.name == "nch"
        assert inst.connection == {
            "pin1": "net1",
            "pin2": "net2",
            "pin3": "net3",
            "pin4": "net4",
        }

    def test_syntax4(self):
        lexer = InstLexer()

        lexer.input("R0 net1 net2 1.2 $[res]")
        assert tuple(map(expand_token, lexer)) == (
            ("R", "R0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "1.2"),
            ("DESIGNATE", "res"),
        )

        lexer.input("R0 net1 net2 1.2 $[res] w=1 l=2")
        assert tuple(map(expand_token, lexer)) == (
            ("R", "R0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "1.2"),
            ("DESIGNATE", "res"),
            ("ASSIGN", ("w", "1")),
            ("ASSIGN", ("l", "2")),
        )

        lexer.input("C0 net1 net2 1.2 $[cap] w=1 l=2")
        assert tuple(map(expand_token, lexer)) == (
            ("C", "C0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "1.2"),
            ("DESIGNATE", "cap"),
            ("ASSIGN", ("w", "1")),
            ("ASSIGN", ("l", "2")),
        )

        lexer.input("C0 net1 net2 1.2 w=1 l=2 $SUB=3 $[cap] $X=1 $Y=2 $D=3")
        assert tuple(map(expand_token, lexer)) == (
            ("C", "C0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "1.2"),
            ("ASSIGN", ("w", "1")),
            ("ASSIGN", ("l", "2")),
            ("ASSIGN", ("$SUB", "3")),
            ("DESIGNATE", "cap"),
            ("ASSIGN", ("$X", "1")),
            ("ASSIGN", ("$Y", "2")),
            ("ASSIGN", ("$D", "3")),
        )

        lexer.input("Q0 net1 net2 net3 1.2 $[pnp] $X=1 $Y=2 $D=3")
        assert tuple(map(expand_token, lexer)) == (
            ("Q", "Q0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "1.2"),
            ("DESIGNATE", "pnp"),
            ("ASSIGN", ("$X", "1")),
            ("ASSIGN", ("$Y", "2")),
            ("ASSIGN", ("$D", "3")),
        )

        inst = parse("R0 net1 net2 1.2 $[res]")
        assert inst.name == "R0"
        assert inst.reference.name == "res"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == ["1.2"]
        assert inst.parameters == {}

        inst = parse("R0 net1 net2 1.2 $[res] w=1 l=2")
        assert inst.name == "R0"
        assert inst.reference.name == "res"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == ["1.2"]
        assert inst.parameters == {
            "w": "1",
            "l": "2",
        }

        inst = parse("C0 net1 net2 1.2 $[cap] w=1 l=2")
        assert inst.name == "C0"
        assert inst.reference.name == "cap"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == ["1.2"]
        assert inst.parameters == {
            "w": "1",
            "l": "2",
        }

        inst = parse("C0 net1 net2 1.2 w=1 l=2 $SUB=3 $[cap] $X=1 $Y=2 $D=3")
        assert inst.name == "C0"
        assert inst.reference.name == "cap"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == ["1.2"]
        assert inst.parameters == {
            "w": "1",
            "l": "2",
            "$SUB": "3",
            "$X": "1",
            "$Y": "2",
            "$D": "3",
        }

        inst = parse("Q0 net1 net2 net3 1.2 $[pnp] $X=1 $Y=2 $D=3")
        assert inst.name == "Q0"
        assert inst.reference.name == "pnp"
        assert inst.connection == ("net1", "net2", "net3")
        assert inst.orderparams == ["1.2"]
        assert inst.parameters == {
            "$X": "1",
            "$Y": "2",
            "$D": "3",
        }
