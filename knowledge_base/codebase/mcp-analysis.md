# AgentMail MCP Server Documentation

This document provides a comprehensive overview of the AgentMail MCP Server, its tools, configuration, and usage patterns.

---

## Overview

The AgentMail MCP Server is a Model Context Protocol (MCP) server that provides tools for interacting with the AgentMail API. It enables AI agents (like Claude) to send, receive, and manage emails programmatically through a standardized MCP interface.

**Package Information:**
- Package Name: `agentmail-mcp`
- Version: 0.2.1
- License: MIT
- Homepage: https://agentmail.to
- Repository: https://github.com/agentmail-to/agentmail-mcp

**Core Dependencies:**
- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `agentmail` - AgentMail API client library
- `agentmail-toolkit` - Tool definitions and adapters

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENTMAIL_API_KEY` | Yes | Your AgentMail API key from https://agentmail.to |
| `AGENTMAIL_BASE_URL` | No | Custom base URL for self-hosted or staging environments |

### Running the Server

Basic usage:
```bash
npx -y agentmail-mcp
```

### Tool Selection

By default, all tools are loaded. Selectively enable specific tools using `--tools`:
```bash
npx -y agentmail-mcp --tools get_message,send_message,reply_to_message
```

---

## Available MCP Tools (10 Total)

### Inbox Management

#### 1. list_inboxes
Lists all inboxes in your organization with pagination support.

**Parameters:**
- `limit` (number, optional, default: 10) - Maximum inboxes per request
- `pageToken` (string, optional) - Pagination token for next page

**Use Cases:**
- Discovering available inboxes
- Iterating through all inboxes
- Finding a specific inbox

#### 2. get_inbox
Retrieves detailed information about a specific inbox.

**Parameters:**
- `inboxId` (string, required) - The inbox email address

**Use Cases:**
- Verifying inbox exists
- Retrieving inbox metadata
- Checking inbox configuration

#### 3. create_inbox
Creates a new inbox (email account).

**Parameters:**
- `username` (string, optional) - Local part of email (random if not provided)
- `domain` (string, optional) - Domain (defaults to agentmail.to)
- `displayName` (string, optional) - Friendly name in email headers

**Use Cases:**
- Setting up new email identity for an agent
- Creating dedicated inboxes for different purposes
- Provisioning inboxes for multi-tenant applications

#### 4. delete_inbox
Permanently deletes an inbox and all associated data.

**Parameters:**
- `inboxId` (string, required) - The inbox to delete

**Warning:** This action is irreversible.

---

### Thread & Attachment Operations

#### 5. list_threads
Lists all email threads (conversations) in an inbox.

**Parameters:**
- `inboxId` (string, required) - The inbox to list threads from
- `limit` (number, optional, default: 10) - Maximum threads to return
- `pageToken` (string, optional) - Pagination token
- `labels` (string[], optional) - Filter by labels (e.g., ["unread"])
- `before` (string, optional) - Filter before datetime (ISO 8601)
- `after` (string, optional) - Filter after datetime (ISO 8601)

**Use Cases:**
- Checking for new incoming emails (filter by "unread")
- Finding conversations with specific users
- Monitoring inbox activity

#### 6. get_thread
Retrieves a complete email thread including all messages.

**Parameters:**
- `inboxId` (string, required) - The inbox containing the thread
- `threadId` (string, required) - The thread identifier

**Response Notes:**
- Returns full message content (text and HTML)
- Includes `extracted_text`/`extracted_html` fields with quoted text removed

**Use Cases:**
- Reading full conversation context before replying
- Extracting information from email exchanges
- Processing incoming messages for agent decision-making

#### 7. get_attachment
Downloads and extracts content from an email attachment.

**Parameters:**
- `inboxId` (string, required) - The inbox containing the thread
- `threadId` (string, required) - The thread containing the attachment
- `attachmentId` (string, required) - The attachment identifier

**Supported File Types:**
- PDF documents - Returns extracted text
- DOCX documents - Returns extracted text
- Other formats return an error

**Use Cases:**
- Reading resume/CV attachments in hiring workflows
- Processing document attachments in automated workflows
- Extracting information from reports or contracts

---

### Message Operations

#### 8. send_message
Sends a new email message, starting a new conversation thread.

**Parameters:**
- `inboxId` (string, required) - The inbox to send from
- `to` (string[], required) - Array of recipient email addresses
- `subject` (string, optional) - Email subject line
- `text` (string, optional) - Plain text body
- `html` (string, optional) - HTML body
- `cc` (string[], optional) - CC recipients
- `bcc` (string[], optional) - BCC recipients
- `labels` (string[], optional) - Labels to apply

**Use Cases:**
- Initiating outreach campaigns
- Sending notifications
- Proactive communication from agents

**Best Practice:** Always include both `text` and `html` content.

#### 9. reply_to_message
Sends a reply to an existing message within a thread.

**Parameters:**
- `inboxId` (string, required) - The inbox containing the message
- `messageId` (string, required) - The message being replied to
- `text` (string, optional) - Plain text body
- `html` (string, optional) - HTML body
- `replyAll` (boolean, optional) - Reply to all recipients
- `labels` (string[], optional) - Labels to apply

**Automatic Behavior:**
- Sets proper email headers (In-Reply-To, References)
- Maintains thread grouping in recipients' email clients

**Use Cases:**
- Responding to customer inquiries
- Continuing automated conversations
- Multi-turn email interactions

#### 10. update_message
Updates metadata on an existing message (labels).

**Parameters:**
- `inboxId` (string, required) - The inbox containing the message
- `messageId` (string, required) - The message to update
- `addLabels` (string[], optional) - Labels to add
- `removeLabels` (string[], optional) - Labels to remove

**Use Cases:**
- Marking messages as read (remove "unread")
- Flagging for follow-up
- Implementing custom workflow states

---

## Error Handling

### Error Types

| Error | Cause | Resolution |
|-------|-------|------------|
| 401 Unauthorized | Invalid or missing API key | Verify AGENTMAIL_API_KEY |
| 404 Not Found | Resource doesn't exist | Verify resource ID |
| 400 Bad Request | Invalid parameters | Check parameter types |
| 429 Rate Limited | Too many requests | Implement backoff |
| Timeout | Network/slow response | Retry the request |
| Unsupported file type | Attachment extraction failed | Only PDF/DOCX supported |

---

## Integration Patterns

### Pattern 1: Email Monitoring Agent
1. `list_threads` with label filter for "unread"
2. `get_thread` to read full conversation
3. Process content and generate response
4. `reply_to_message` to send response
5. `update_message` to mark as "processed"

### Pattern 2: Proactive Outreach Agent
1. `list_inboxes` to find appropriate sending inbox
2. `send_message` to initiate contact
3. `list_threads` to monitor for responses
4. `get_thread` and `reply_to_message` for follow-up

### Pattern 3: Document Processing Agent
1. `list_threads` to find emails with attachments
2. `get_thread` to access attachment metadata
3. `get_attachment` to extract document content
4. Process extracted text
5. `reply_to_message` with results

### Selective Tool Loading for Security

- **Read-only agents:** `list_inboxes,get_inbox,list_threads,get_thread,get_attachment`
- **Reply-only agents:** `list_threads,get_thread,reply_to_message,update_message`
- **Full access:** All tools (default)

---

## Resource Hierarchy

```
Organization (your account)
└── Inbox (email account, e.g., agent@agentmail.to)
    └── Thread (conversation, auto-created from messages)
        └── Message (individual email)
            └── Attachment (files attached to messages)
```

---

## Best Practices

1. **Use labels for workflow management** - Labels are the primary mechanism for tracking message state

2. **Always provide both text and HTML** - Include both formats for email client compatibility

3. **Use extracted content for replies** - `extracted_text` and `extracted_html` provide clean reply content without quoted text

4. **Handle pagination** - Check for `pageToken` in responses for complete data retrieval

5. **Validate inbox existence** - Call `get_inbox` before sending messages

6. **Implement error handling** - Always handle potential API errors

7. **Use selective tool loading** - Limit available tools for security when appropriate
