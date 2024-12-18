from depends_on.common import filter_comments


def test_filter_comments():
    data = {
        "description": """<!--
    This is a comment
    -->"""
    }
    assert filter_comments(data) == {"description": ""}


# test_common.py ends here
