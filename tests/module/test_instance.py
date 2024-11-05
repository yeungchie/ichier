from ichier import Instance


class TestInstance:
    def test_floating_connect_by_name(self):
        inst = Instance(
            name="inst_1",
            reference="ref_1",
            connection={
                "Term": None,
            },
        )
        inst.rebuild()
        assert isinstance(inst.connection, dict)
        assert "Term" not in inst.connection

    def test_floating_connect_by_order(self):
        inst = Instance(
            name="inst_1",
            reference="ref_1",
            connection=[None],
        )
        inst.rebuild()
        assert isinstance(inst.connection, tuple)
        assert "Term" not in inst.connection
