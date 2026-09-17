"""
test_linear_pagination.py

Verifies the comment-truncation warning WITHOUT needing a real Linear
account or network access. It fakes Linear's API response so we can
control exactly what comes back and confirm the code reacts correctly.

Place this file in the SAME folder as connector.py
(e.g. onyx/connectors/linear/test_linear_pagination.py), then run it
from your repo root the same way you'd run the connector itself:

    python -m onyx.connectors.linear.test_linear_pagination

(Adjust the module path below and in the import statement if your
connector.py lives somewhere else.)
"""

import logging
from unittest.mock import patch

from onyx.connectors.linear.connector import LinearConnector


class FakeResponse:
    """Stands in for requests.Response so no real HTTP call is made."""

    ok = True

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def fake_linear_payload():
    """
    One fake issue that has MORE comments than _MAX_COMMENTS_PER_ISSUE
    (we simulate this by setting comments.pageInfo.hasNextPage = True).
    This should trigger the truncation warning.
    """
    return {
        "data": {
            "issues": {
                "edges": [
                    {
                        "node": {
                            "id": "issue-1",
                            "createdAt": "2024-01-01T00:00:00.000Z",
                            "updatedAt": "2024-01-02T00:00:00.000Z",
                            "identifier": "TEST-1",
                            "title": "Fake issue for pagination test",
                            "url": "https://linear.app/fake/issue/TEST-1",
                            "description": "This is a fake issue.",
                            "team": {"name": "Fake Team"},
                            "creator": {"name": "Someone", "email": "a@b.com"},
                            "assignee": None,
                            "state": {"id": "s1", "name": "Todo"},
                            "priority": 1,
                            "estimate": None,
                            "startedAt": None,
                            "completedAt": None,
                            "dueDate": None,
                            "comments": {
                                "nodes": [
                                    {"url": "https://linear.app/fake/issue/TEST-1#c1", "body": "comment 1"},
                                ],
                                # THIS is the important bit: hasNextPage=True
                                # means Linear has MORE comments than we
                                # fetched -> our warning should fire.
                                "pageInfo": {"hasNextPage": True},
                            },
                        }
                    }
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
    }


def main():
    # Make sure warnings actually print to the terminal.
    logging.basicConfig(level=logging.WARNING)

    connector = LinearConnector()
    # Fake key is fine -- we never actually send it anywhere in this test.
    connector.load_credentials({"linear_api_key": "fake-key-not-used"})

    fake_response = FakeResponse(fake_linear_payload())

    # Replace _make_query so it returns our fake response instead of
    # hitting Linear's real servers.
    with patch(
        "onyx.connectors.linear.connector._make_query",
        return_value=fake_response,
    ):
        batches = connector.load_from_state()
        documents = next(batches)

    print(f"\nGot {len(documents)} document(s) back.")
    print("If you saw a WARNING line above mentioning 'TEST-1' and")
    print("'truncated', the fix is working correctly.\n")


if __name__ == "__main__":
    main()
