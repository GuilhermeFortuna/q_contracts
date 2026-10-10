from pathlib import Path

import yaml


def test_tick_paging_defines_bounded_lossless_cursor_protocol():
    contract = yaml.safe_load(Path("schema/edge/data-gateway.yaml").read_text())
    endpoint = contract["endpoints"]["/v1/ticks/page"]
    assert endpoint["query_parameters"]["end_msc"]["exclusive"] is True
    assert endpoint["query_parameters"]["limit"]["default"] == 250_000
    assert endpoint["query_parameters"]["limit"]["maximum"] == 1_000_000
    metadata = endpoint["response"]["metadata"]
    assert set(metadata) == {
        "next_cursor_msc",
        "exhausted",
        "first_msc",
        "last_msc",
        "row_count",
    }
