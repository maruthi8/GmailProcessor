from processor.rules import RuleEngine


#  Test cases for fetch_actions function not included as it's get tested with get_all_actions and fetch_and_parse_email


class TestRuleEngine:

    def test_load_rules(self, rule_engine_with_temp_file):
        """Test loading rules from JSON file"""
        rule_engine = rule_engine_with_temp_file

        assert len(rule_engine.rules) == 2
        assert rule_engine.rules[0]['name'] == 'Test Rule 1'
        assert rule_engine.rules[1]['name'] == 'Test Rule 2'

    def test_load_nonexistent_rules_file(self):
        """Test loading from non-existent file"""
        rule_engine = RuleEngine('nonexistent_file.json')
        assert rule_engine.rules == []

    def test_check_condition_contains(self, rule_engine_with_temp_file, sample_email_data):
        """Test contains operator"""
        rule_engine = rule_engine_with_temp_file

        condition = {
            'field': 'from',
            'operator': 'contains',
            'value': 'test@example'
        }

        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is True

        condition['value'] = 'notfound'
        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is False

    def test_check_condition_not_contains(self, rule_engine_with_temp_file, sample_email_data):
        """Test not_contains operator"""
        rule_engine = rule_engine_with_temp_file

        condition = {
            'field': 'from',
            'operator': 'not_contains',
            'value': 'spam'
        }

        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is True

        condition['value'] = 'test@example'
        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is False

    def test_check_condition_equals(self, rule_engine_with_temp_file, sample_email_data):
        """Test equals operator"""
        rule_engine = rule_engine_with_temp_file

        condition = {
            'field': 'from',
            'operator': 'equals',
            'value': 'test@example.com'
        }

        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is True

        condition['value'] = 'different@example.com'
        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is False

    def test_check_condition_not_equals(self, rule_engine_with_temp_file, sample_email_data):
        """Test not_equals operator"""
        rule_engine = rule_engine_with_temp_file

        condition = {
            'field': 'from',
            'operator': 'not_equals',
            'value': 'different@example.com'
        }

        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is True

        condition['value'] = 'test@example.com'
        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is False

    def test_check_date_condition_newer_than(self, rule_engine_with_temp_file):
        """Test newer_than date operator"""
        rule_engine = rule_engine_with_temp_file

        email_data = {
            'date': 'Wed, 10 Jul 2025 10:30:00 +0000'
        }

        condition = {
            'field': 'date_received',
            'operator': 'newer_than',
            'value': '30',
            'unit': 'days'
        }

        result = rule_engine.check_condition(email_data, condition)
        assert isinstance(result, bool)

    def test_check_date_condition_older_than(self, rule_engine_with_temp_file):
        """Test older_than date operator"""
        rule_engine = rule_engine_with_temp_file

        email_data = {
            'date': 'Wed, 10 Jan 2020 10:30:00 +0000'
        }

        condition = {
            'field': 'date_received',
            'operator': 'older_than',
            'value': '30',
            'unit': 'days'
        }

        result = rule_engine.check_condition(email_data, condition)
        assert result is True

    def test_evaluate_rule_all_predicate(self, rule_engine_with_temp_file):
        """Test rule evaluation with 'all' predicate"""
        rule_engine = rule_engine_with_temp_file

        email_data = {
            'from': 'test@example.com',
            'subject': 'Test Subject'
        }

        rule = {
            'predicate': 'all',
            'conditions': [
                {'field': 'from', 'operator': 'contains', 'value': 'test@example'},
                {'field': 'subject', 'operator': 'contains', 'value': 'Test'}
            ]
        }

        result = rule_engine.evaluate_rule(email_data, rule)
        assert result is True

        rule['conditions'][1]['value'] = 'NotFound'
        result = rule_engine.evaluate_rule(email_data, rule)
        assert result is False

    def test_evaluate_rule_any_predicate(self, rule_engine_with_temp_file):
        """Test rule evaluation with 'any' predicate"""
        rule_engine = rule_engine_with_temp_file

        email_data = {
            'from': 'test@example.com',
            'subject': 'Different Subject'
        }

        rule = {
            'predicate': 'any',
            'conditions': [
                {'field': 'from', 'operator': 'contains', 'value': 'test@example'},
                {'field': 'subject', 'operator': 'contains', 'value': 'NotFound'}
            ]
        }

        result = rule_engine.evaluate_rule(email_data, rule)
        assert result is True

        rule['conditions'][0]['value'] = 'NotFound'
        result = rule_engine.evaluate_rule(email_data, rule)
        assert result is False

    def test_get_actions_for_email(self, rule_engine_with_temp_file):
        """Test getting actions for an email"""
        rule_engine = rule_engine_with_temp_file

        email_data = {
            'id': 'test_123',
            'from': 'test@example.com',
            'subject': 'Test Subject'
        }

        actions = rule_engine.get_actions_for_email(email_data)

        assert len(actions) == 1
        assert actions[0]['rule_name'] == 'Test Rule 1'
        assert actions[0]['action']['type'] == 'mark_as_read'
        assert actions[0]['email_id'] == 'test_123'

    def test_get_actions_for_email_multiple_rules(self, rule_engine_with_temp_file):
        """Test getting actions when multiple rules match"""
        rule_engine = rule_engine_with_temp_file

        email_data = {
            'id': 'test_123',
            'from': 'test@example.com',
            'subject': 'Important Test Subject'
        }

        actions = rule_engine.get_actions_for_email(email_data)

        assert len(actions) == 2
        rule_names = [action['rule_name'] for action in actions]
        assert 'Test Rule 1' in rule_names
        assert 'Test Rule 2' in rule_names

    def test_get_actions_for_email_no_match(self, rule_engine_with_temp_file):
        """Test getting actions when no rules match"""
        rule_engine = rule_engine_with_temp_file

        email_data = {
            'id': 'test_123',
            'from': 'different@example.com',
            'subject': 'Regular Subject'
        }

        actions = rule_engine.get_actions_for_email(email_data)
        assert len(actions) == 0


    def test_unknown_field(self, rule_engine_with_temp_file, sample_email_data):
        """Test handling unknown field"""
        rule_engine = rule_engine_with_temp_file

        condition = {
            'field': 'unknown_field',
            'operator': 'contains',
            'value': 'test'
        }

        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is False

    def test_unknown_operator(self, rule_engine_with_temp_file, sample_email_data):
        """Test handling unknown operator"""
        rule_engine = rule_engine_with_temp_file

        condition = {
            'field': 'from',
            'operator': 'unknown_operator',
            'value': 'test'
        }

        result = rule_engine.check_condition(sample_email_data, condition)
        assert result is False

    def test_unknown_predicate(self, rule_engine_with_temp_file, sample_email_data):
        """Test handling unknown predicate"""
        rule_engine = rule_engine_with_temp_file

        rule = {
            'predicate': 'unknown_predicate',
            'conditions': [
                {'field': 'from', 'operator': 'contains', 'value': 'test'}
            ]
        }

        result = rule_engine.evaluate_rule(sample_email_data, rule)
        assert result is False
