from ichier.utils import flattenMemName


class TestFig:
    def test_net(self):
        nets = flattenMemName("A")
        assert nets == ["A"]

    def test_nets(self):
        nets = flattenMemName("{A, B, C}")
        assert nets == ["A", "B", "C"]

    def test_bit_net(self):
        nets = flattenMemName("A[1]")
        assert nets == ["A[1]"]

    def test_bus_nets(self):
        nets = flattenMemName("A[1:0]")
        assert nets == ["A[1]", "A[0]"]

    def test_misc_nets(self):
        nets = flattenMemName("{A<3>, A<1:0>, A[1], B[2:0], C, \\D[2:0] ,}")
        assert nets == [
            "A<3>",
            "A<1>",
            "A<0>",
            "A[1]",
            "B[2]",
            "B[1]",
            "B[0]",
            "C",
            "\\D[2:0]",
        ]
