import logging
import sqlite3

logger = logging.getLogger(__name__)


class EmailDatabase:
    def __init__(self, db_path='emails.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create tables in db if not exists to store emails and actions for those
        Returns:

        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                thread_id TEXT,
                from_email TEXT,
                to_email TEXT,
                subject TEXT,
                body TEXT,
                date_received TEXT,
                is_read BOOLEAN,
                labels TEXT,
                snippet TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                rule_name TEXT,
                action_type TEXT,
                action_details TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',
                FOREIGN KEY (email_id) REFERENCES emails (id),
                UNIQUE(email_id, rule_name, action_type)
            )
        ''')

        conn.commit()
        conn.close()
        logging.info("Database initialized successfully")

    def email_exists(self, email_id):
        """Check if email exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM emails WHERE id = ?', (email_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count > 0

    def action_exists(self, email_id, rule_name, action_type):
        """Check if action has already been performed on an email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM email_actions 
            WHERE email_id = ? AND rule_name = ? AND action_type = ? AND status = 'success'
        ''', (email_id, rule_name, action_type))

        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def record_action(self, email_id, rule_name, action_type, action_details='', status='success'):
        """Record an action performed on an email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO email_actions 
                (email_id, rule_name, action_type, action_details, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (email_id, rule_name, action_type, action_details, status))

            conn.commit()
            logger.debug(f"Recorded action: {action_type} on email {email_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording action: {e}")
            return False
        finally:
            conn.close()

    def get_emails_by_ids(self, email_ids):
        """Get multiple emails by IDs from database"""
        if not email_ids:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        placeholders = ','.join(['?' for _ in email_ids])

        cursor.execute(f'''
            SELECT id, thread_id, from_email, to_email, subject, body, 
                   date_received, is_read, labels, snippet
            FROM emails 
            WHERE id IN ({placeholders})
        ''', email_ids)

        results = cursor.fetchall()
        conn.close()

        emails = []
        for result in results:
            emails.append({
                'id': result[0],
                'thread_id': result[1],
                'from': result[2],
                'to': result[3],
                'subject': result[4],
                'body': result[5],
                'date': result[6],
                'is_read': result[7],
                'labels': result[8].split(',') if result[8] else [],
                'snippet': result[9]
            })

        return emails

    def insert_email(self, email_data):
        """Insert a single email into the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO emails 
                (id, thread_id, from_email, to_email, subject, body, 
                 date_received, is_read, labels, snippet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_data['id'],
                email_data['thread_id'],
                email_data['from'],
                email_data['to'],
                email_data['subject'],
                email_data['body'],
                email_data['date'],
                email_data['is_read'],
                ','.join(email_data['labels']),
                email_data['snippet']
            ))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error inserting email: {e}")
            return False
        finally:
            conn.close()

    def insert_emails(self, emails):
        """Insert multiple emails into the database"""
        successful = 0
        failed = 0

        for email_l in emails:
            if self.insert_email(email_l):
                successful += 1
            else:
                failed += 1

        logger.info(f"Inserted {successful} emails successfully")
        if failed > 0:
            logger.error(f"Failed to insert {failed} emails")

        return successful, failed

