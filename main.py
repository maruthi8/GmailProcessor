import logging

from processor.actions import EmailActions
from processor.authenticate import authenticate_gmail
from processor.database import EmailDatabase
from processor.rules import RuleEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GmailProcessor:
    def __init__(self, rules_file='rules.json'):
        self.service = None
        self.actions = None
        self.db = EmailDatabase()
        self.rule_engine = RuleEngine(rules_file)
        self.authenticate()

    def authenticate(self):
        """Authenticate with Gmail API"""
        try:
            self.service = authenticate_gmail()
            self.actions = EmailActions(self.service)
            logger.info("Authentication successful!")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")

    def process_emails(self, limit=10):
        """Process the email fetch and apply rules for those.

        Args:
            limit (int):

        Returns:
            True or False
        """
        if not self.service:
            exit(1)
        try:
            logger.info(f"Starting email processing (limit: {limit})")

            actions_to_apply = self.rule_engine.fetch_actions(self.service, limit)

            if not actions_to_apply:
                logger.info("No actions needed - all emails are already processed correctly")
                return

            logger.info(f"Executing {len(actions_to_apply)} actions...")
            self.actions.execute_actions(actions_to_apply)

        except Exception as e:
            logger.error(f"Error in process_emails: {e}")


if __name__ == "__main__":
    processor = GmailProcessor()
    processor.process_emails()
