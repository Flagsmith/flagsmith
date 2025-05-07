from metrics.metrics_service import build_metrics_section


def test_build_metrics_section_basic():
    data = {
        "total": 10,
        "enabled": 5,
        "disabled": 15,
    }
    definition = {
        "total": {"title": "Total", "description": "Total count"},
        "enabled": {"title": "Enabled", "description": "Enabled count"},
        "disabled": {"title": "Disabled", "description": "Disabled count", "disabled": True},
        "not_exist": {"title": "Not exist", "description": "Not exist count"},
    }
    
    result = build_metrics_section(data, definition)
    
    assert len(result) == 2
    assert result[0] == {
        "title": "Total",
        "description": "Total count",
        "value": 10,
    }
    assert result[1] == {
        "title": "Enabled",
        "description": "Enabled count",
        "value": 5,
    }

# def test_build_metrics_section_missing_keys():
#     data = {
#         "total": 10
#     }
#     definition = {
#         "total": {"title": "Total", "description": "Total count"},
#         "enabled": {"title": "Enabled", "description": "Enabled count"}
#     }
    
#     result = build_metrics_section(data, definition)
    
#     assert len(result) == 1
#     assert result[0] == {
#         "title": "Total",
#         "description": "Total count",
#         "value": 10,
#         "disabled": False
#     }

# def test_build_metrics_section_with_disabled():
#     data = {
#         "total": 10
#     }
#     definition = {
#         "total": {"title": "Total", "description": "Total count", "disabled": True}
#     }
    
#     result = build_metrics_section(data, definition)
    
#     assert len(result) == 1
#     assert result[0] == {
#         "title": "Total",
#         "description": "Total count",
#         "value": 10,
#         "disabled": True
#     }

# def test_build_metrics_section_empty():
#     data = {}
#     definition = {}
    
#     result = build_metrics_section(data, definition)
    
#     assert len(result) == 0