from ichier.parser.spice.p_inst import InstLexer, parse


def expand_token(t):
    return t.type, t.value


class TestSyntax:
    def test_inst_subckt1(self):
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

    def test_inst_subckt2(self):
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

    def test_inst_subckt3(self):
        lexer = InstLexer()

        lexer.input(
            "X0 nch m=1 length=4u width=10u $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4"
        )
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("ID", "nch"),
            ("ASSIGN", ("m", "1")),
            ("ASSIGN", ("length", "4u")),
            ("ASSIGN", ("width", "10u")),
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

        lexer.input("X0 nch $PINS")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("ID", "nch"),
            ("PINS", "$PINS"),
        )

        inst = parse(
            "X0 nch m=1 length=4u width=10u $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4"
        )
        assert inst.name == "X0"
        assert inst.reference.name == "nch"
        assert inst.parameters == {
            "m": "1",
            "length": "4u",
            "width": "10u",
        }
        assert inst.connection == {
            "pin1": "net1",
            "pin2": "net2",
            "pin3": "net3",
            "pin4": "net4",
        }

        inst = parse("X0 nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4")
        assert inst.name == "X0"
        assert inst.reference.name == "nch"
        assert inst.connection == {
            "pin1": "net1",
            "pin2": "net2",
            "pin3": "net3",
            "pin4": "net4",
        }

    def test_inst_subckt4(self):
        lexer = InstLexer()

        lexer.input(
            "X0 / nch m=1 length=4u width=10u $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4"
        )
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("/", "/"),
            ("ID", "nch"),
            ("ASSIGN", ("m", "1")),
            ("ASSIGN", ("length", "4u")),
            ("ASSIGN", ("width", "10u")),
            ("PINS", "$PINS"),
            ("ASSIGN", ("pin1", "net1")),
            ("ASSIGN", ("pin2", "net2")),
            ("ASSIGN", ("pin3", "net3")),
            ("ASSIGN", ("pin4", "net4")),
        )

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

        lexer.input("X0 / nch $PINS")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("/", "/"),
            ("ID", "nch"),
            ("PINS", "$PINS"),
        )

        lexer.input("X0 / nch")
        assert tuple(map(expand_token, lexer)) == (
            ("X", "X0"),
            ("/", "/"),
            ("ID", "nch"),
        )

        inst = parse(
            "X0 / nch m=1 length=4u width=10u $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4"
        )
        assert inst.name == "X0"
        assert inst.reference.name == "nch"
        assert inst.parameters == {
            "m": "1",
            "length": "4u",
            "width": "10u",
        }
        assert inst.connection == {
            "pin1": "net1",
            "pin2": "net2",
            "pin3": "net3",
            "pin4": "net4",
        }

        inst = parse("X0 / nch $PINS pin1=net1 pin2=net2 pin3=net3 pin4=net4")
        assert inst.name == "X0"
        assert inst.reference.name == "nch"
        assert inst.connection == {
            "pin1": "net1",
            "pin2": "net2",
            "pin3": "net3",
            "pin4": "net4",
        }

    def test_inst_2t(self):
        lexer = InstLexer()

        lexer.input("R0 net1 net2 pdk_res 1.2K length=10u width=1u")
        assert tuple(map(expand_token, lexer)) == (
            ("R", "R0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "pdk_res"),
            ("ID", "1.2K"),
            ("ASSIGN", ("length", "10u")),
            ("ASSIGN", ("width", "1u")),
        )

        lexer.input("R0 net1 net2 pdk_res r=1.2K length=10u width=1u")
        assert tuple(map(expand_token, lexer)) == (
            ("R", "R0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "pdk_res"),
            ("ASSIGN", ("r", "1.2K")),
            ("ASSIGN", ("length", "10u")),
            ("ASSIGN", ("width", "1u")),
        )

        inst = parse("R0 net1 net2 pdk_res 1.2K length=10u width=1u")
        assert inst.name == "R0"
        assert inst.reference.name == "pdk_res"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == ["1.2K"]
        assert inst.parameters == {
            "length": "10u",
            "width": "1u",
        }

        inst = parse("R0 net1 net2 pdk_res r=1.2K length=10u width=1u")
        assert inst.name == "R0"
        assert inst.reference.name == "pdk_res"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == []
        assert inst.parameters == {
            "r": "1.2K",
            "length": "10u",
            "width": "1u",
        }

    def test_inst_2td(self):
        lexer = InstLexer()

        lexer.input("R0 net1 net2 1.2K $[pdk_res] length=10u width=1u")
        assert tuple(map(expand_token, lexer)) == (
            ("R", "R0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "1.2K"),
            ("DESIGNATE", "pdk_res"),
            ("ASSIGN", ("length", "10u")),
            ("ASSIGN", ("width", "1u")),
        )

        lexer.input("R0 net1 net2 r=1.2K $[pdk_res] length=10u width=1u")
        assert tuple(map(expand_token, lexer)) == (
            ("R", "R0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ASSIGN", ("r", "1.2K")),
            ("DESIGNATE", "pdk_res"),
            ("ASSIGN", ("length", "10u")),
            ("ASSIGN", ("width", "1u")),
        )

        inst = parse("R0 net1 net2 1.2K $[pdk_res] length=10u width=1u")
        assert inst.name == "R0"
        assert inst.reference.name == "pdk_res"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == ["1.2K"]
        assert inst.parameters == {
            "length": "10u",
            "width": "1u",
        }

        inst = parse("R0 net1 net2 r=1.2K $[pdk_res] length=10u width=1u")
        assert inst.name == "R0"
        assert inst.reference.name == "pdk_res"
        assert inst.connection == ("net1", "net2")
        assert inst.orderparams == []
        assert inst.parameters == {
            "r": "1.2K",
            "length": "10u",
            "width": "1u",
        }

    def test_inst_3t(self):
        lexer = InstLexer()

        lexer.input("Q0 net1 net2 net3 pdk_pnp 25 length=5u width=5u")
        assert tuple(map(expand_token, lexer)) == (
            ("Q", "Q0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "pdk_pnp"),
            ("ID", "25"),
            ("ASSIGN", ("length", "5u")),
            ("ASSIGN", ("width", "5u")),
        )

        lexer.input("Q0 net1 net2 net3 pdk_pnp area=25 length=5u width=5u")
        assert tuple(map(expand_token, lexer)) == (
            ("Q", "Q0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "pdk_pnp"),
            ("ASSIGN", ("area", "25")),
            ("ASSIGN", ("length", "5u")),
            ("ASSIGN", ("width", "5u")),
        )

        inst = parse("Q0 net1 net2 net3 pdk_pnp 25 length=5u width=5u")
        assert inst.name == "Q0"
        assert inst.reference.name == "pdk_pnp"
        assert inst.connection == ("net1", "net2", "net3")
        assert inst.orderparams == ["25"]
        assert inst.parameters == {
            "length": "5u",
            "width": "5u",
        }

        inst = parse("Q0 net1 net2 net3 pdk_pnp area=25 length=5u width=5u")
        assert inst.name == "Q0"
        assert inst.reference.name == "pdk_pnp"
        assert inst.connection == ("net1", "net2", "net3")
        assert inst.orderparams == []
        assert inst.parameters == {
            "area": "25",
            "length": "5u",
            "width": "5u",
        }

    def test_inst_3td(self):
        lexer = InstLexer()

        lexer.input("Q0 net1 net2 net3 25 $[pdk_pnp] length=5u width=5u")
        assert tuple(map(expand_token, lexer)) == (
            ("Q", "Q0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "25"),
            ("DESIGNATE", "pdk_pnp"),
            ("ASSIGN", ("length", "5u")),
            ("ASSIGN", ("width", "5u")),
        )

        lexer.input("Q0 net1 net2 net3 area=25 $[pdk_pnp] length=5u width=5u")
        assert tuple(map(expand_token, lexer)) == (
            ("Q", "Q0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ASSIGN", ("area", "25")),
            ("DESIGNATE", "pdk_pnp"),
            ("ASSIGN", ("length", "5u")),
            ("ASSIGN", ("width", "5u")),
        )

        inst = parse("Q0 net1 net2 net3 25 $[pdk_pnp] length=5u width=5u")
        assert inst.name == "Q0"
        assert inst.reference.name == "pdk_pnp"
        assert inst.connection == ("net1", "net2", "net3")
        assert inst.orderparams == ["25"]
        assert inst.parameters == {
            "length": "5u",
            "width": "5u",
        }

        inst = parse("Q0 net1 net2 net3 area=25 $[pdk_pnp] length=5u width=5u")
        assert inst.name == "Q0"
        assert inst.reference.name == "pdk_pnp"
        assert inst.connection == ("net1", "net2", "net3")
        assert inst.orderparams == []
        assert inst.parameters == {
            "area": "25",
            "length": "5u",
            "width": "5u",
        }

    def test_inst_4t(self):
        lexer = InstLexer()

        lexer.input("M0 net1 net2 net3 net4 pdk_mos length=1u width=2u")
        assert tuple(map(expand_token, lexer)) == (
            ("M", "M0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "net4"),
            ("ID", "pdk_mos"),
            ("ASSIGN", ("length", "1u")),
            ("ASSIGN", ("width", "2u")),
        )

        inst = parse("M0 net1 net2 net3 net4 pdk_mos length=1u width=2u")
        assert inst.name == "M0"
        assert inst.reference.name == "pdk_mos"
        assert inst.connection == ("net1", "net2", "net3", "net4")
        assert inst.orderparams == []
        assert inst.parameters == {
            "length": "1u",
            "width": "2u",
        }

    def test_inst_4td(self):
        lexer = InstLexer()

        lexer.input("M0 net1 net2 net3 net4 $[pdk_mos] length=1u width=2u")
        assert tuple(map(expand_token, lexer)) == (
            ("M", "M0"),
            ("ID", "net1"),
            ("ID", "net2"),
            ("ID", "net3"),
            ("ID", "net4"),
            ("DESIGNATE", "pdk_mos"),
            ("ASSIGN", ("length", "1u")),
            ("ASSIGN", ("width", "2u")),
        )

        inst = parse("M0 net1 net2 net3 net4 $[pdk_mos] length=1u width=2u")
        assert inst.name == "M0"
        assert inst.reference.name == "pdk_mos"
        assert inst.connection == ("net1", "net2", "net3", "net4")
        assert inst.orderparams == []
        assert inst.parameters == {
            "length": "1u",
            "width": "2u",
        }
