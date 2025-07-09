import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from processor.database import EmailDatabase
from processor.rules import RuleEngine
from processor.actions import EmailActions


class TestGmailProcessor:

    @pytest.fixture
    def integration_setup(self, temp_db, test_rules):
        """Setup for integration tests"""
        temp_dir = tempfile.mkdtemp()
        rules_path = os.path.join(temp_dir, 'integration_rules.json')

        with open(rules_path, 'w') as f:
            json.dump(test_rules, f)

        rule_engine = RuleEngine(rules_path)
        mock_service = Mock()
        actions = EmailActions(mock_service)

        actions.db = temp_db

        yield {
            'db': temp_db,
            'rule_engine': rule_engine,
            'actions': actions,
            'mock_service': mock_service,
            'rules_path': rules_path
        }

        if os.path.exists(rules_path):
            os.remove(rules_path)
        os.rmdir(temp_dir)

    def test_email_processing(self, integration_setup, sample_email_data):
        setup = integration_setup
        db = setup['db']
        rule_engine = setup['rule_engine']
        actions = setup['actions']
        mock_service = setup['mock_service']

        email_data = sample_email_data.copy()
        email_data['from'] = 'test@example.com'
        email_data['subject'] = 'Important Test'

        success = db.insert_email(email_data)
        assert success is True

        actions_to_apply = rule_engine.get_actions_for_email(email_data)
        assert len(actions_to_apply) == 2

        mock_service.users().messages().get().execute.return_value = {
            'labelIds': ['INBOX', 'UNREAD']
        }
        mock_service.users().messages().modify().execute.return_value = {}
        mock_service.users().labels().list().execute.return_value = {
            'labels': [{'id': 'INBOX', 'name': 'INBOX'}]
        }
        mock_service.users().labels().create().execute.return_value = {
            'id': 'Label_Important', 'name': 'Important'
        }

        success_count, failed_count = actions.execute_actions(actions_to_apply)

        assert success_count == 2
        assert failed_count == 0

    @patch('processor.actions.EmailActions.is_email_read')
    def test_email_duplicate_action_prevention(self, is_email_read, integration_setup, sample_email_data):
        setup = integration_setup
        db = setup['db']
        rule_engine = setup['rule_engine']
        actions = setup['actions']

        email_data = sample_email_data.copy()
        email_data['from'] = 'test@example.com'
        db.insert_email(email_data)

        actions_to_apply = rule_engine.get_actions_for_email(email_data)
        assert len(actions_to_apply) == 1

        db.record_action('test_email_123', 'Test Rule 1', 'mark_as_read')

        result = actions.execute_action(actions_to_apply[0])
        assert result is True

        is_email_read.assert_not_called()
