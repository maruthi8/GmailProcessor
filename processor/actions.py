import logging
from googleapiclient.errors import HttpError
from processor.database import EmailDatabase

logger = logging.getLogger(__name__)


class EmailActions:
    def __init__(self, gmail_service):
        self.service = gmail_service
        self.db = EmailDatabase()

    def action_already_performed(self, email_id, rule_name, action_type):
        """Check if action was already performed (database check first)"""
        return self.db.action_exists(email_id, rule_name, action_type)

    def get_email_labels(self, email_id):
        """Get current labels for an email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='minimal'
            ).execute()

            return message.get('labelIds', [])

        except HttpError as error:
            logger.error(f"Error getting labels for email {email_id}: {error}")
            return []

    def is_email_read(self, email_id):
        """Check if email is already read"""
        labels = self.get_email_labels(email_id)
        return 'UNREAD' not in labels

    def is_email_unread(self, email_id):
        """Check if email is already unread"""
        labels = self.get_email_labels(email_id)
        return 'UNREAD' in labels

    def has_label(self, email_id, label_name):
        """Check if email already has a specific label"""
        try:
            labels_result = self.service.users().labels().list(userId='me').execute()
            all_labels = labels_result.get('labels', [])

            target_label_id = None
            for label in all_labels:
                if label['name'] == label_name:
                    target_label_id = label['id']
                    break

            if not target_label_id:
                return False

            email_labels = self.get_email_labels(email_id)
            return target_label_id in email_labels

        except HttpError as error:
            logger.error(f"Error checking label for email {email_id}: {error}")
            return False

    def mark_as_read(self, email_id, rule_name):
        """Mark an email as read (check database first, then Gmail state)"""
        action_type = 'mark_as_read'

        if self.action_already_performed(email_id, rule_name, action_type):
            logger.info(f"Action '{action_type}' already recorded in database for email {email_id} - skipping")
            return True

        if self.is_email_read(email_id):
            logger.info(f"Email {email_id} is already read - recording and skipping")
            self.db.record_action(email_id, rule_name, action_type, 'Already read')
            return True

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            self.db.record_action(email_id, rule_name, action_type, 'Marked as read')
            logger.info(f"Marked email {email_id} as read and recorded in database")
            return True

        except HttpError as error:
            logger.error(f"Error marking email {email_id} as read: {error}")
            self.db.record_action(email_id, rule_name, action_type, f'Error: {error}', 'failed')
            return False

    def mark_as_unread(self, email_id, rule_name):
        """Mark an email as unread (check database first, then Gmail state)"""
        action_type = 'mark_as_unread'

        if self.action_already_performed(email_id, rule_name, action_type):
            logger.info(f"📚 Action '{action_type}' already recorded in database for email {email_id} - skipping")
            return True

        if self.is_email_unread(email_id):
            logger.info(f"Email {email_id} is already unread - recording and skipping")
            self.db.record_action(email_id, rule_name, action_type, 'Already unread')
            return True

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()

            self.db.record_action(email_id, rule_name, action_type, 'Marked as unread')
            logger.info(f"Marked email {email_id} as unread and recorded in database")
            return True

        except HttpError as error:
            logger.error(f"Error marking email {email_id} as unread: {error}")
            self.db.record_action(email_id, rule_name, action_type, f'Error: {error}', 'failed')
            return False

    def move_to_inbox(self, email_id, rule_name):
        """Move email to inbox (check database first, then Gmail state)"""
        action_type = 'move_to_inbox'

        if self.action_already_performed(email_id, rule_name, action_type):
            logger.info(f"Action '{action_type}' already recorded in database for email {email_id} - skipping")
            return True

        email_labels = self.get_email_labels(email_id)
        if 'INBOX' in email_labels:
            logger.info(f"Email {email_id} is already in inbox - recording and skipping")
            self.db.record_action(email_id, rule_name, action_type, 'Already in inbox')
            return True

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['INBOX']}
            ).execute()

            self.db.record_action(email_id, rule_name, action_type, 'Moved to inbox')
            logger.info(f"Moved email {email_id} to inbox and recorded in database")
            return True

        except HttpError as error:
            logger.error(f"Error moving email {email_id} to inbox: {error}")
            self.db.record_action(email_id, rule_name, action_type, f'Error: {error}', 'failed')
            return False

    def move_to_label(self, email_id, rule_name, label_name):
        """Move email to a specific label (check database first, then Gmail state)"""
        action_type = f'move_to_{label_name}'

        if self.action_already_performed(email_id, rule_name, action_type):
            logger.info(f"Action '{action_type}' already recorded in database for email {email_id} - skipping")
            return True

        if self.has_label(email_id, label_name):
            logger.info(f"Email {email_id} already has label '{label_name}' - recording and skipping")
            self.db.record_action(email_id, rule_name, action_type, f'Already has label {label_name}')
            return True

        try:
            label_id = self.get_or_create_label(label_name)
            if not label_id:
                self.db.record_action(email_id, rule_name, action_type, f'Failed to create label {label_name}', 'failed')
                return False

            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [label_id]}
            ).execute()

            self.db.record_action(email_id, rule_name, action_type, f'Added label {label_name}')
            logger.info(f"Added label '{label_name}' to email {email_id} and recorded in database")
            return True

        except HttpError as error:
            logger.error(f"Error adding label {label_name} to email {email_id}: {error}")
            self.db.record_action(email_id, rule_name, action_type, f'Error: {error}', 'failed')
            return False

    def get_or_create_label(self, label_name):
        """Get label ID by name, or create if it doesn't exist"""
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            for label in labels:
                if label['name'] == label_name:
                    return label['id']

            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }

            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()

            logger.info(f"Created new label: {label_name}")
            return created_label['id']

        except HttpError as error:
            logger.error(f"Error with label {label_name}: {error}")
            return None

    def execute_action(self, action_item):
        """Execute a single action on an email"""
        email_id = action_item['email_id']
        rule_name = action_item['rule_name']
        action = action_item['action']
        action_type = action['type']

        logger.info(f"Executing action '{action_type}' on email {email_id}")

        if action_type == 'mark_as_read':
            return self.mark_as_read(email_id, rule_name)

        elif action_type == 'mark_as_unread':
            return self.mark_as_unread(email_id, rule_name)

        elif action_type == 'move_message':
            folder = action.get('folder', 'INBOX')
            if folder.upper() == 'INBOX':
                return self.move_to_inbox(email_id, rule_name)
            elif folder.upper() == 'TRASH':
                return self.move_to_trash(email_id, rule_name)
            else:
                return self.move_to_label(email_id, rule_name, folder)

        else:
            logger.warning(f"Unknown action type: {action_type}")
            self.db.record_action(email_id, rule_name, action_type, f'Unknown action type', 'failed')
            return False

    def execute_actions(self, actions_list):
        """Execute multiple actions with database tracking"""
        if not actions_list:
            logger.info("No actions to execute")
            return

        logger.info(f"Executing {len(actions_list)} actions")

        success_count = 0
        failed_count = 0

        for action_item in actions_list:
            try:
                result = self.execute_action(action_item)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Unexpected error executing action: {e}")
                failed_count += 1

        logger.info(f"Actions completed: {success_count} successful, {failed_count} failed")

        return success_count, failed_count

    def move_to_trash(self, email_id, rule_name):
        """Move email to trash"""
        action_type = 'move_to_trash'

        if self.action_already_performed(email_id, rule_name, action_type):
            logger.info(f"Action '{action_type}' already recorded in database for email {email_id} - skipping")
            return True

        try:
            self.service.users().messages().trash(
                userId='me',
                id=email_id
            ).execute()

            self.db.record_action(email_id, rule_name, action_type, 'Moved to trash')
            logger.info(f"Moved email {email_id} to trash and recorded in database")
            return True

        except HttpError as error:
            logger.error(f"Error moving email {email_id} to trash: {error}")
            self.db.record_action(email_id, rule_name, action_type, f'Error: {error}', 'failed')
            return False
