from typing import Sequence
from unittest.mock import MagicMock

import pytest
from mimikatz_credentials_collector.plugin import MIMIKATZ_EVENT_TAGS, Plugin
from mimikatz_credentials_collector.windows_credentials import WindowsCredentials

from common.agent_events import CredentialsStolenEvent
from common.credentials import Credentials, LMHash, NTHash, Password, Username
from common.event_queue import IAgentEventPublisher
from common.types import AgentID

PLUGIN_NAME = "TEST_MIMIKATZ"
AGENT_ID = AgentID("be11ad56-995d-45fd-be03-e7806a47b56b")


def patch_pypykatz(win_creds: Sequence[WindowsCredentials], monkeypatch):
    monkeypatch.setattr(
        "mimikatz_credentials_collector" ".plugin.get_windows_creds",
        lambda: win_creds,
    )


def collect_credentials() -> Sequence[Credentials]:
    mock_event_publisher = MagicMock(spec=IAgentEventPublisher)
    return Plugin(
        plugin_name=PLUGIN_NAME, agent_id=AGENT_ID, agent_event_publisher=mock_event_publisher
    ).run()


@pytest.mark.parametrize(
    "win_creds", [([WindowsCredentials(username="", password="", ntlm_hash="", lm_hash="")]), ([])]
)
def test_empty_results(monkeypatch, win_creds):
    patch_pypykatz(win_creds, monkeypatch)
    collected_credentials = collect_credentials()
    assert not collected_credentials


def test_pypykatz_result_parsing(monkeypatch):
    win_creds = [WindowsCredentials(username="user", password="secret", ntlm_hash="", lm_hash="")]
    patch_pypykatz(win_creds, monkeypatch)

    username = Username(username="user")
    password = Password(password="secret")
    expected_credentials = Credentials(identity=username, secret=password)

    collected_credentials = collect_credentials()
    assert len(collected_credentials) == 1
    assert collected_credentials[0] == expected_credentials


def test_pypykatz_result_parsing_duplicates(monkeypatch):
    win_creds = [
        WindowsCredentials(username="user", password="secret", ntlm_hash="", lm_hash=""),
        WindowsCredentials(username="user", password="secret", ntlm_hash="", lm_hash=""),
    ]
    patch_pypykatz(win_creds, monkeypatch)

    collected_credentials = collect_credentials()
    assert len(collected_credentials) == 1


def test_pypykatz_result_parsing_defaults(monkeypatch):
    win_creds = [
        WindowsCredentials(
            username="user2", password="secret2", lm_hash="0182BD0BD4444BF8FC83B5D9042EED2E"
        ),
    ]
    patch_pypykatz(win_creds, monkeypatch)

    # Expected credentials
    username = Username(username="user2")
    password = Password(password="secret2")
    lm_hash = LMHash(lm_hash="0182BD0BD4444BF8FC83B5D9042EED2E")
    expected_credentials = [
        Credentials(identity=username, secret=password),
        Credentials(identity=username, secret=lm_hash),
    ]

    collected_credentials = collect_credentials()
    assert len(collected_credentials) == 2
    assert collected_credentials == expected_credentials


def test_pypykatz_result_parsing_no_identities(monkeypatch):
    win_creds = [
        WindowsCredentials(
            username="",
            password="",
            ntlm_hash="E9F85516721DDC218359AD5280DB4450",
            lm_hash="0182BD0BD4444BF8FC83B5D9042EED2E",
        ),
    ]
    patch_pypykatz(win_creds, monkeypatch)

    lm_hash = LMHash(lm_hash="0182BD0BD4444BF8FC83B5D9042EED2E")
    nt_hash = NTHash(nt_hash="E9F85516721DDC218359AD5280DB4450")
    expected_credentials = [
        Credentials(identity=None, secret=lm_hash),
        Credentials(identity=None, secret=nt_hash),
    ]

    collected_credentials = collect_credentials()
    assert len(collected_credentials) == 2
    assert collected_credentials == expected_credentials


def test_pypykatz_result_parsing_no_secrets(monkeypatch):
    username = "user3"
    win_creds = [
        WindowsCredentials(
            username=username,
            password="",
            ntlm_hash="",
            lm_hash="",
        ),
    ]
    patch_pypykatz(win_creds, monkeypatch)

    expected_credentials = [Credentials(identity=Username(username=username), secret=None)]

    collected_credentials = collect_credentials()
    assert len(collected_credentials) == 1
    assert collected_credentials == expected_credentials


def test_mimikatz_credentials_stolen_event_published(monkeypatch):
    mock_event_publisher = MagicMock(spec=IAgentEventPublisher)
    patch_pypykatz([], monkeypatch)

    mimikatz_credential_collector = Plugin(
        plugin_name=PLUGIN_NAME, agent_id=AGENT_ID, agent_event_publisher=mock_event_publisher
    )
    mimikatz_credential_collector.run()

    mock_event_publisher.publish.assert_called_once()

    mock_event_publisher_call_args = mock_event_publisher.publish.call_args[0][0]

    assert isinstance(mock_event_publisher_call_args, CredentialsStolenEvent)


def test_mimikatz_credentials_stolen_event_tags(monkeypatch):
    mock_event_publisher = MagicMock(spec=IAgentEventPublisher)
    patch_pypykatz([], monkeypatch)

    mimikatz_credential_collector = Plugin(
        plugin_name=PLUGIN_NAME, agent_id=AGENT_ID, agent_event_publisher=mock_event_publisher
    )
    mimikatz_credential_collector.run()

    mock_event_publisher_call_args = mock_event_publisher.publish.call_args[0][0]

    assert mock_event_publisher_call_args.tags == MIMIKATZ_EVENT_TAGS


def test_mimikatz_credentials_stolen_event_stolen_credentials(monkeypatch):
    mock_event_publisher = MagicMock(spec=IAgentEventPublisher)
    win_creds = [
        WindowsCredentials(
            username="user2", password="secret2", lm_hash="0182BD0BD4444BF8FC83B5D9042EED2E"
        ),
    ]
    patch_pypykatz(win_creds, monkeypatch)

    mimikatz_credential_collector = Plugin(
        plugin_name=PLUGIN_NAME, agent_id=AGENT_ID, agent_event_publisher=mock_event_publisher
    )
    collected_credentials = mimikatz_credential_collector.run()

    mock_event_publisher_call_args = mock_event_publisher.publish.call_args[0][0]

    assert mock_event_publisher_call_args.stolen_credentials == collected_credentials
