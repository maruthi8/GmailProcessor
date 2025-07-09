import base64
import logging

from processor.database import EmailDatabase

logger = logging.getLogger(__name__)


def parse_email_content(service, message_id):
    """
    Parse full email content from message ID
    
    Args:
        service: Gmail API service object
        message_id: Gmail message ID
    
    Returns:
        Dictionary with parsed email data
    """
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        email_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'labels': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'from': '',
            'to': '',
            'subject': '',
            'date': '',
            'body': '',
            'is_read': 'UNREAD' not in message.get('labelIds', [])
        }

        headers = message['payload'].get('headers', [])
        for header in headers:
            name = header['name'].lower()
            if name == 'from':
                email_data['from'] = header['value']
            elif name == 'to':
                email_data['to'] = header['value']
            elif name == 'subject':
                email_data['subject'] = header['value']
            elif name == 'date':
                email_data['date'] = header['value']

        email_data['body'] = extract_body(message['payload'])

        return email_data

    except Exception as error:
        logger.error(f'Error parsing email {message_id}: {error}')
        return None


def extract_body(payload):
    """Extract email body from payload"""
    body = ""

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        if payload['mimeType'] == 'text/plain':
            if 'data' in payload['body']:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

    return body


def fetch_and_parse_emails(service, query='in:all', max_results=3):
    """Check if we have already fetched the entries from email and had in database
    else fetch and parse the content again
    Args:
        service:
        query:
        max_results:

    Returns:
        List of emails
    """
    db = EmailDatabase()
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return messages

        existing_emails = []
        new_email_ids = []

        for message in messages:
            email_id = message['id']
            if db.email_exists(email_id):
                existing_emails.append(email_id)
            else:
                new_email_ids.append(email_id)

        parsed_emails = []
        if existing_emails:
            logger.info(f"Loading {len(existing_emails)} emails from database")
            db_emails = db.get_emails_by_ids(existing_emails)
            parsed_emails.extend(db_emails)

        new_emails = []

        for i, email_id in enumerate(new_email_ids, 1):
            email_data = parse_email_content(service, email_id)
            if email_data:
                new_emails.append(email_data)

        if new_emails:
            logger.info(f"Storing {len(new_emails)} new emails in database")
            db.insert_emails(new_emails)
            parsed_emails.extend(new_emails)

        logger.info(f"Total emails processed: {len(parsed_emails)} ({len(existing_emails)} from DB, {len(new_email_ids)} from Gmail)")

        parsed_emails.sort(key=lambda x: x.get('date', ''), reverse=True)

        return parsed_emails

    except Exception as error:
        logger.error(f'Error fetching emails: {error}')
        return []
