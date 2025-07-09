import pytest
import os
import tempfile
from unittest.mock import Mock
from processor.database import EmailDatabase
from processor.rules import RuleEngine
from processor.actions import EmailActions


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_emails.db')
    db = EmailDatabase(db_path)
    yield db
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)


@pytest.fixture
def sample_email_data():
    """Sample email data for testing"""
    return {
        'id': 'test_email_123',
        'thread_id': 'thread_456',
        'from': 'test@example.com',
        'to': 'user@gmail.com',
        'subject': 'Test Email Subject',
        'body': 'This is a test email body content.',
        'date': 'Mon, 15 Jan 2024 10:30:00 +0000',
        'is_read': False,
        'labels': ['INBOX', 'UNREAD'],
        'snippet': 'This is a test email...'
    }


@pytest.fixture
def sample_gmail_message():
    """Mock Gmail API message response"""
    return {
        'id': 'test_email_123',
        'threadId': 'thread_456',
        'labelIds': ['INBOX', 'UNREAD'],
        'snippet': 'This is a test email...',
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'test@example.com'},
                {'name': 'To', 'value': 'user@gmail.com'},
                {'name': 'Subject', 'value': 'Test Email Subject'},
                {'name': 'Date', 'value': 'Mon, 15 Jan 2024 10:30:00 +0000'}
            ],
            'mimeType': 'text/plain',
            'body': {
                'data': 'VGhpcyBpcyBhIHRlc3QgZW1haWwgYm9keSBjb250ZW50Lg=='
            }
        }
    }


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service"""
    service = Mock()

    list_mock = Mock()
    list_mock.execute.return_value = {
        'messages': [
            {'id': 'test_email_123', 'threadId': 'thread_456'},
            {'id': 'test_email_456', 'threadId': 'thread_789'}
        ]
    }
    service.users().messages().list.return_value = list_mock

    get_mock = Mock()
    service.users().messages().get.return_value = get_mock

    modify_mock = Mock()
    modify_mock.execute.return_value = {}
    service.users().messages().modify.return_value = modify_mock

    labels_list_mock = Mock()
    labels_list_mock.execute.return_value = {
        'labels': [
            {'id': 'INBOX', 'name': 'INBOX'},
            {'id': 'UNREAD', 'name': 'UNREAD'},
            {'id': 'Label_1', 'name': 'Test Label'}
        ]
    }
    service.users().labels().list.return_value = labels_list_mock

    return service


@pytest.fixture
def test_rules():
    """Sample rules for testing"""
    return {
        "rules": [
            {
                "name": "Test Rule 1",
                "description": "Mark test emails as read",
                "predicate": "all",
                "conditions": [
                    {
                        "field": "from",
                        "operator": "contains",
                        "value": "test@example.com"
                    }
                ],
                "actions": [
                    {
                        "type": "mark_as_read"
                    }
                ]
            },
            {
                "name": "Test Rule 2",
                "description": "Move important emails",
                "predicate": "any",
                "conditions": [
                    {
                        "field": "subject",
                        "operator": "contains",
                        "value": "Important"
                    },
                    {
                        "field": "subject",
                        "operator": "contains",
                        "value": "Urgent"
                    }
                ],
                "actions": [
                    {
                        "type": "move_message",
                        "folder": "Important"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def temp_rules_file(test_rules):
    """Create a temporary rules file for testing"""
    import json
    temp_dir = tempfile.mkdtemp()
    rules_path = os.path.join(temp_dir, 'test_rules.json')

    with open(rules_path, 'w') as f:
        json.dump(test_rules, f)

    yield rules_path

    if os.path.exists(rules_path):
        os.remove(rules_path)
    os.rmdir(temp_dir)


@pytest.fixture
def rule_engine_with_temp_file(temp_rules_file):
    """Rule engine with temporary rules file"""
    return RuleEngine(temp_rules_file)


@pytest.fixture
def mock_email_actions(mock_gmail_service):
    """Mock EmailActions with mocked Gmail service"""
    return EmailActions(mock_gmail_service)
