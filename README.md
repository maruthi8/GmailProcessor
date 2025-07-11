# Gmail Email Processor

A standalone Python application that integrates with Gmail API to automatically process emails based on configurable rules and perform actions like marking as read/unread and moving messages.

## Task Overview

This Task implements a rule-based email processing system that:
- Authenticates with Gmail API using OAuth 2.0
- Fetches emails from Gmail inbox
- Stores emails in a SQLite database
- Processes emails against JSON-defined rules
- Executes actions on Gmail using REST API

## Features

### Email Processing
- **OAuth Authentication**: Secure Gmail API access
- **Email Fetching**: Retrieve emails from Gmail (no IMAP)
- **Database Storage**: Store emails in SQLite for processing
- **Rule-based Processing**: Apply configurable rules to emails
- **Action Execution**: Perform actions on Gmail via REST API

### Rule Engine
- **JSON Configuration**: Define rules in JSON format
- **Multiple Conditions**: Support for multiple conditions per rule
- **Flexible Predicates**: "All" or "Any" condition matching
- **String Operations**: Contains, equals, not contains, not equals
- **Date Operations**: Older than, newer than (days/months)
- **Supported Fields**: From, To, Subject, Message body, Date received

### Actions
- **Mark as Read/Unread**: Change email read status
- **Move Messages**: Move emails to inbox, trash, or custom labels
- **Label Management**: Create and apply custom labels

## Requirements

- Python 3.11+
- Gmail account
- Google Cloud Project with Gmail API enabled
- Internet connection
- Get credentials from Google cloud console

## Installation

### 1. Clone the Repository
```bash
git clone [<repository-url>](https://github.com/maruthi8/GmailProcessor.git)
cd gmail-email-processor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

### Rules Configuration (`rules.json`)

The system uses JSON-based rules configuration:

```json
{
  "rules": [
    {
      "name": "Rule Name",
      "description": "Rule description",
      "predicate": "all",
      "conditions": [
        {
          "field": "from",
          "operator": "contains",
          "value": "example.com"
        },
        {
          "field": "subject",
          "operator": "contains",
          "value": "Important"
        }
      ],
      "actions": [
        {
          "type": "mark_as_read"
        },
        {
          "type": "move_message",
          "folder": "Important"
        }
      ]
    }
  ]
}
```

### Supported Fields
- `from`: Email sender
- `to`: Email recipient
- `subject`: Email subject line
- `body`: Email message content
- `date_received`: Email received date

### Supported Operators
- **String fields**: `contains`, `not_contains`, `equals`, `not_equals`
- **Date fields**: `older_than`, `newer_than` (with units: days, months)

### Supported Actions
- `mark_as_read`: Mark email as read
- `mark_as_unread`: Mark email as unread
- `move_message`: Move email to folder/label

### Predicates
- `all`: All conditions must match
- `any`: At least one condition must match

## Usage

### Basic Usage
```bash
python main.py
```

### First Run
1. The application will open your web browser
2. Sign in to your Google account
3. Grant permissions for Gmail access
4. The system will process emails according to your rules

## Security

- **OAuth 2.0**: Secure authentication with Google
- **Local Storage**: Credentials stored locally
- **Minimal Permissions**: Only requests necessary Gmail permissions
- **No Password Storage**: Uses OAuth tokens, not passwords

## Troubleshooting

### Common Issues

#### Authentication Errors
- **Problem**: "403: access_denied"
- **Solution**: Add your email as test user in OAuth consent screen

#### Missing Dependencies
- **Problem**: "ModuleNotFoundError"
- **Solution**: Run `pip install -r requirements.txt`

#### No Emails Found
- **Problem**: "No messages found"
- **Solution**: Check Gmail account has emails, adjust query parameters

#### Rule Not Matching
- **Problem**: "Generated 0 actions"
- **Solution**: Check rule conditions match your email content

## 🔗 References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Python Google API Client](https://github.com/googleapis/google-api-python-client)

---

**Note**: This application requires proper Google Cloud setup and Gmail API access. Follow the installation instructions carefully for proper configuration.
