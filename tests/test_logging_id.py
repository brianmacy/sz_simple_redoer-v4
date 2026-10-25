"""Regression tests for redo-record logging IDs (issue #15).

A REPAIR_ENTITY redo record is a UMF_PROC message with no DATA_SOURCE or
RECORD_ID. When one failed with SENZ0010 the failure path indexed
record["DATA_SOURCE"], raised KeyError and the whole process exited.
"""

import orjson
import pytest

import sz_simple_redoer as redoer

REPAIR_ENTITY_MSG = orjson.dumps(
    {
        "UMF_PROC": {
            "NAME": "REPAIR_ENTITY",
            "PARAMS": [
                {"PARAM": {"NAME": "ENTITY_ID", "VALUE": "12345"}},
                {"PARAM": {"NAME": "REEVAL_ITERATION", "VALUE": "1"}},
                {"PARAM": {"NAME": "REASON", "VALUE": "RESOLUTION"}},
            ],
        }
    }
).decode()

DSRC_MSG = orjson.dumps(
    {"DATA_SOURCE": "CUSTOMERS", "RECORD_ID": "1001", "DSRC_ACTION": "X"}
).decode()


def test_failure_message_repair_entity_does_not_raise():
    assert redoer.failure_message(REPAIR_ENTITY_MSG) == (
        "⚠️ FAILED due to bad data or timeout: 12345 : REPAIR_ENTITY"
    )


def test_failure_message_dsrc_record():
    assert redoer.failure_message(DSRC_MSG) == (
        "⚠️ FAILED due to bad data or timeout: CUSTOMERS : 1001"
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"UMF_PROC": {"NAME": "REPAIR_ENTITY"}}', "UMF_PROC : REPAIR_ENTITY"),
        ('{"UMF_PROC": {"PARAMS": []}}', "UMF_PROC : REPAIR_ENTITY"),
        ('{"SOMETHING": "ELSE"}', "UNKNOWN RECORD"),
        ('["not", "an", "object"]', "UNKNOWN RECORD"),
        ("not json", "UNKNOWN RECORD"),
        ("", "UNKNOWN RECORD"),
    ],
)
def test_msg_logging_id_never_raises(raw, expected):
    assert redoer.msg_logging_id(raw) == expected
