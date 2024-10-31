from ichier.utils import parseMemName


class TestFig:
    def test_net(self):
        assert parseMemName("A") == "A"

    def test_group(self):
        assert parseMemName("{A,},") == ("A",)

    def test_nets(self):
        assert parseMemName("A, B, C") == ("A", "B", "C")

    def test_bit_net(self):
        assert parseMemName("A[1]") == "A[1]"

    def test_bus_nets(self):
        assert parseMemName("A[1:0]") == ("A[1]", "A[0]")

    def test_hier_nets(self):
        assert parseMemName("{A[1:0], B[1]}, C") == (("A[1]", "A[0]", "B[1]"), "C")

    def test_misc_nets(self):
        nets = parseMemName("{A<3>, {A<1:0>}, A[1]}, B[2:0], C, \\D[2:0]")
        assert nets == (
            ("A<3>", ("A<1>", "A<0>"), "A[1]"),
            "B[2]",
            "B[1]",
            "B[0]",
            "C",
            "\\D[2:0]",
        )
