from ichier.utils.escape import needEscape, EscapeString, makeSafeString


class TestEscapeString:
    def test_id(self):
        assert makeSafeString("abc") == "abc"

    def test_esc_id(self):
        id_1 = EscapeString("\\123")
        assert id_1 == "123"
        id_2 = EscapeString(id_1)
        assert id_2 == "123"
        assert id_1 is not id_2

    def test_need_escape(self):
        assert needEscape("abc") is False
        assert needEscape("\\123") is True

    def test_make_safe_string(self):
        assert makeSafeString("abc") == "abc"
        id_1 = makeSafeString("\\123")
        assert id_1 == "123"
        id_2 = makeSafeString(id_1)
        assert id_2 == "123"
        assert id_1 is id_2
