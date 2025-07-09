import email.utils
import json
import logging
from datetime import datetime, timedelta

from processor.parse import fetch_and_parse_emails

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, rules_file='rules.json'):
        self.rules_file = rules_file
        self.rules = self.load_rules()

    def load_rules(self):
        """Load rules from JSON file"""
        try:
            with open(self.rules_file, 'r') as file:
                data = json.load(file)
                rules = data.get('rules', [])
                logger.info(f"Loaded {len(rules)} rules from {self.rules_file}")
                return rules
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return []

    def check_condition(self, email_data, condition):
        """Check if a single condition matches the email"""
        field = condition['field']
        operator = condition['operator']
        value = condition['value']

        if field == 'from':
            email_value = email_data.get('from', '').lower()
        elif field == 'to':
            email_value = email_data.get('to', '').lower()
        elif field == 'subject':
            email_value = email_data.get('subject', '').lower()
        elif field == 'body':
            email_value = email_data.get('body', '').lower()
        elif field == 'date_received':
            email_value = email_data.get('date', '')
        else:
            logger.warning(f"Unknown field: {field}")
            return False

        if operator in ['contains', 'not_contains', 'equals', 'not_equals']:
            value = value.lower()

        if operator == 'contains':
            return value in email_value
        elif operator == 'not_contains':
            return value not in email_value
        elif operator == 'equals':
            return email_value == value
        elif operator == 'not_equals':
            return email_value != value
        elif operator == 'older_than':
            return self.check_date_condition(email_value, value, condition.get('unit', 'days'), older=True)
        elif operator == 'newer_than':
            return self.check_date_condition(email_value, value, condition.get('unit', 'days'), older=False)
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    def check_date_condition(self, email_date_str, value, unit, older=True):
        """Check date-based conditions
        Args:
            email_date_str:
            value:
            unit:
            older:

        Returns:

        """
        try:
            email_date = email.utils.parsedate_to_datetime(email_date_str)

            days = int(value)
            if unit == 'days':
                threshold_date = datetime.now(email_date.tzinfo) - timedelta(days=days)
            elif unit == 'months':
                threshold_date = datetime.now(email_date.tzinfo) - timedelta(days=days * 30)
            else:
                logger.warning(f"Unknown date unit: {unit}")
                return False

            if older:
                return email_date < threshold_date
            else:
                return email_date > threshold_date

        except Exception as e:
            logger.error(f"Error parsing date {email_date_str}: {e}")
            return False

    def evaluate_rule(self, email_data, rule):
        """Based on the rule apply the condition and predicate to an email data that we got after parsing.
        Args:
            email_data:
            rule:

        Returns:

        """
        conditions = rule.get('conditions', [])
        predicate = rule.get('predicate', 'all')

        if not conditions:
            return False

        condition_results = []
        for condition in conditions:
            result = self.check_condition(email_data, condition)
            condition_results.append(result)

        if predicate == 'all':
            match = all(condition_results)
        elif predicate == 'any':
            match = any(condition_results)
        else:
            logger.warning(f"Unknown predicate: {predicate}")
            match = False

        return match

    def get_actions_for_email(self, email_data):
        """Get all actions that should be applied to an email

        Args:
            email_data:

        Returns:

        """
        actions_to_apply = []

        for rule in self.rules:
            if self.evaluate_rule(email_data, rule):
                rule_name = rule.get('name', 'Unknown Rule')
                actions = rule.get('actions', [])

                logger.info(f"Rule matched: '{rule_name}' for email: {email_data.get('subject', 'No Subject')}")

                for action in actions:
                    actions_to_apply.append({
                        'rule_name': rule_name,
                        'action': action,
                        'email_id': email_data['id']
                    })

        return actions_to_apply

    def fetch_actions(self, email_service, limit=10):
        """Parse the emails and get the actions to be done based on rules
        Args:
            email_service:
            limit:

        Returns:

        """
        all_actions = []
        parsed_emails = fetch_and_parse_emails(email_service, max_results=limit)

        logger.info(f"Processing {len(parsed_emails)} emails against {len(self.rules)} rules")

        for parsed_email in parsed_emails:
            email_actions = self.get_actions_for_email(parsed_email)
            all_actions.extend(email_actions)

        logger.info(f"Generated {len(all_actions)} actions to apply")
        return all_actions
