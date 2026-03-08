# AgentMail API Reference

> **Last updated:** 2026-03-07
> **API Base URL:** `https://api.agentmail.to/v0`
> **Authentication:** Bearer token via `Authorization` header
> **Content-Type:** `application/json` (all requests and responses)

AgentMail is an API-first email platform built for AI agents. It provides a complete REST API for programmatic email management: creating inboxes, sending and receiving messages, managing threads, handling webhooks for real-time events, and configuring custom domains. Unlike traditional email services, AgentMail is designed for two-way autonomous conversations, with features like content extraction, label-based filtering, and WebSocket real-time streaming purpose-built for agent workflows.

**Quick Links:**
- [Official Docs](https://docs.agentmail.to) | [Console](https://console.agentmail.to)
- [Python SDK](https://github.com/agentmail-to/agentmail-python) (`pip install agentmail`) — v0.2.24
- [TypeScript SDK](https://www.npmjs.com/package/agentmail) (`npm install agentmail`) — v0.4.3
- [OpenAPI Spec](https://docs.agentmail.to/openapi.json)

---

## Table of Contents

1. [API Resources Overview](#1-api-resources-overview)
2. [Authentication](#2-authentication)
3. [Organizations](#3-organizations)
4. [Pods](#4-pods)
5. [API Keys](#5-api-keys)
6. [Inboxes](#6-inboxes)
7. [Threads](#7-threads)
8. [Messages](#8-messages)
9. [Drafts](#9-drafts)
10. [Attachments](#10-attachments)
11. [Domains](#11-domains)
12. [Webhooks](#12-webhooks)
13. [WebSockets](#13-websockets)
14. [Metrics](#14-metrics)
15. [Lists (Allow/Block)](#15-lists-allowblock)
16. [Error Handling](#16-error-handling)
17. [Common Patterns](#17-common-patterns)
18. [Validation Rules](#18-validation-rules)
19. [Rate Limiting](#19-rate-limiting)
20. [Webhooks Deep Dive](#20-webhooks-deep-dive)
21. [WebSockets Deep Dive](#21-websockets-deep-dive)
22. [Incoming & Outgoing Email Flow](#22-incoming--outgoing-email-flow)
23. [Common Support Questions & FAQ](#23-common-support-questions--faq)
24. [Resource Relationships](#24-resource-relationships)
25. [Quick Reference](#25-quick-reference)

---

## 1. API Resources Overview

### Resource Table

| Resource | Description | Key Endpoints |
|----------|-------------|---------------|
| **Organization** | Top-level account container | `GET /organizations` |
| **Pod** | Multi-tenant isolation boundary | `POST /pods`, `GET /pods`, `DELETE /pods/{pod_id}` |
| **API Key** | Authentication credential | `POST /api-keys`, `GET /api-keys`, `DELETE /api-keys/{id}` |
| **Inbox** | Email account (e.g., `agent@agentmail.to`) | `POST /inboxes`, `GET /inboxes`, `DELETE /inboxes/{id}` |
| **Thread** | Conversation grouping (auto-created) | `GET /threads`, `GET /inboxes/{id}/threads` |
| **Message** | Individual email in a thread | `POST .../messages/send`, `POST .../messages/{id}/reply` |
| **Draft** | Unsent message for review/scheduling | `POST /inboxes/{id}/drafts`, `POST .../drafts/{id}/send` |
| **Attachment** | File attached to message or draft | `GET .../attachments/{attachment_id}` |
| **Domain** | Custom domain with SPF/DKIM/DMARC | `POST /domains`, `GET /domains/{id}/zone-file` |
| **Webhook** | Event notifications via HTTP POST (Svix) | `POST /webhooks`, `PATCH /webhooks/{id}` |
| **WebSocket** | Real-time bidirectional connection | `$connect`, `subscribe`, `unsubscribe` |
| **Metrics** | Email event analytics | `GET /metrics`, `GET /inboxes/{id}/metrics` |
| **List** | Allow/block lists for send/receive filtering | `POST /lists/{direction}/{type}` |

### Resource Hierarchy

```
Organization (top-level container)
├── Pod (optional multi-tenancy boundary)
│   ├── Inbox (email account)
│   │   ├── Thread (conversation, auto-created)
│   │   │   └── Message (individual email)
│   │   │       └── Attachment (file)
│   │   └── Draft (unsent message)
│   ├── Domain (custom domain)
│   ├── List Entry (allow/block rule)
│   └── API Key (pod-scoped credential)
├── Webhook (event subscription)
├── Domain (org-level domain)
├── API Key (org-level credential)
├── List Entry (org-level allow/block rule)
└── Metrics (event analytics)
```

---

## 2. Authentication

### API Key Format

AgentMail API keys follow the format: `am_<prefix>_<secret>`

- **Prefix:** 8 characters shown in the dashboard for identification
- **Secret:** 32 random bytes (hex-encoded)
- **EU keys:** Keys starting with `am_eu_` automatically route to the EU environment (TypeScript SDK only)

### Using the API Key

All API requests require a Bearer token in the `Authorization` header:

```bash
curl -X GET https://api.agentmail.to/v0/inboxes \
  -H "Authorization: Bearer am_abc12345_your_secret_key_here" \
  -H "Content-Type: application/json"
```

### SDK Initialization

**Python:**

```python
from agentmail import AgentMail

# Option 1: Environment variable (recommended)
# Set AGENTMAIL_API_KEY in your environment or .env file
client = AgentMail()

# Option 2: Explicit API key
client = AgentMail(api_key="am_abc12345_your_secret_key_here")

# Option 3: Lazy provider (for vault/secrets manager)
client = AgentMail(api_key=lambda: get_key_from_vault())
```

**TypeScript:**

```typescript
import { AgentMailClient } from "agentmail";

// Option 1: Environment variable (recommended)
const client = new AgentMailClient();

// Option 2: Explicit API key
const client = new AgentMailClient({ apiKey: "am_abc12345_your_secret_key_here" });

// Option 3: Async provider
const client = new AgentMailClient({ apiKey: async () => getKeyFromVault() });
```

### Environment Variable

| Variable | Description |
|----------|-------------|
| `AGENTMAIL_API_KEY` | API key, auto-read by both SDKs on client initialization |

> **Warning:** Never commit API keys to source control. Use `.env` files or a secrets manager. Add `AGENTMAIL_API_KEY` to your `.gitignore` and `.env`.

### Environments

| Environment | HTTP Base URL | WebSocket URL |
|-------------|--------------|---------------|
| Production (US) | `https://api.agentmail.to` | `wss://ws.agentmail.to` |
| Production (EU) | `https://api.agentmail.eu` | `wss://ws.agentmail.eu` |

---

## 3. Organizations

### Description

An Organization is the top-level container for all AgentMail resources. Every API key belongs to exactly one organization. All resource access is organization-scoped — requests for resources outside your organization return 404 (not 403), by design.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `organization_id` | UUID | Unique identifier |
| `authentication_type` | enum | `agentmail`, `clerk`, `vercel`, `wallet` |
| `is_playground` | boolean | Whether this is a playground/trial org |
| `inbox_limit` | number | Max inboxes allowed |
| `domain_limit` | number | Max custom domains allowed |
| `daily_send_limit` | number | Max emails per day |
| `monthly_send_limit` | number | Max emails per month |
| `inbox_count` | number | Current inbox count |
| `domain_count` | number | Current domain count |
| `suspended_at` | datetime | When the org was suspended (if applicable) |
| `suspended_reason` | enum | `bounce_rate` or `complaint_rate` |
| `updated_at` | datetime | Last update timestamp |
| `created_at` | datetime | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/organizations` | Get current organization info |

---

## 4. Pods

### Description

Pods provide multi-tenant isolation within an organization. They allow you to partition resources (inboxes, domains, lists, API keys) so that different tenants or projects are logically separated. A pod-scoped API key can only access resources within that pod.

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `organization_id` | UUID | Auto | Parent organization |
| `pod_id` | UUID | Auto | Unique identifier |
| `name` | string | No | Human-readable name |
| `client_id` | string | No | Idempotency key |
| `updated_at` | datetime | Auto | Last update timestamp |
| `created_at` | datetime | Auto | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pods` | Create a pod |
| GET | `/pods` | List pods |
| GET | `/pods/{pod_id}` | Get pod details |
| DELETE | `/pods/{pod_id}` | Delete a pod |

> **Note:** Pods cannot be deleted while they contain inboxes, domains, or other resources. Delete all child resources first.

### Code Example

**Python:**

```python
# Create a pod for a tenant
pod = client.pods.create(name="tenant-acme", client_id="acme-pod")
print(f"Pod: {pod.pod_id}")

# Create inbox inside the pod
inbox = client.pods.inboxes.create(
    pod_id=pod.pod_id,
    username="support",
    client_id="acme-support-inbox",
)

# List pod-scoped resources
pod_inboxes = client.pods.inboxes.list(pod_id=pod.pod_id)
```

---

## 5. API Keys

### Description

API keys provide programmatic access to the AgentMail API. Keys can be scoped to the entire organization or to a specific pod. A pod-scoped key cannot access resources outside that pod.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `api_key_id` | UUID | Unique identifier |
| `name` | string | Human-readable name |
| `prefix` | string | First 8 characters of the key (for identification) |
| `pod_id` | UUID | Pod scope (optional; if set, restricts access) |
| `used_at` | datetime | Last usage timestamp |
| `created_at` | datetime | Creation timestamp |

> **Note:** The full API key token is only returned at creation time. It cannot be retrieved later.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api-keys` | Create an org-level API key |
| POST | `/pods/{pod_id}/api-keys` | Create a pod-scoped API key |
| GET | `/api-keys` | List org API keys |
| GET | `/pods/{pod_id}/api-keys` | List pod API keys |
| DELETE | `/api-keys/{api_key_id}` | Delete an API key |
| DELETE | `/pods/{pod_id}/api-keys/{api_key_id}` | Delete a pod API key |

---

## 6. Inboxes

### Description

An Inbox is an email account (e.g., `support@agentmail.to`). It is the primary resource for sending and receiving email. Inboxes belong to an organization and optionally to a pod. Each inbox has a unique email address formed as `{username}@{domain}`.

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `inbox_id` | string | Auto | Email address (e.g., `agent@agentmail.to`) |
| `organization_id` | UUID | Auto | Parent organization |
| `pod_id` | UUID | Auto | Parent pod |
| `display_name` | string | No | Display name (no special chars: `()<>@,;:\\"[]`) |
| `client_id` | string | No | Idempotency key |
| `updated_at` | datetime | Auto | Last update timestamp |
| `created_at` | datetime | Auto | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/inboxes` | Create an inbox |
| POST | `/pods/{pod_id}/inboxes` | Create an inbox in a pod |
| GET | `/inboxes` | List inboxes |
| GET | `/pods/{pod_id}/inboxes` | List inboxes in a pod |
| GET | `/inboxes/{inbox_id}` | Get inbox details |
| PATCH | `/inboxes/{inbox_id}` | Update inbox (display name) |
| DELETE | `/inboxes/{inbox_id}` | Delete inbox (async, returns 202) |

### Create Inbox

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username` | string | No | Username part; randomly generated if omitted |
| `domain` | string | No | Must be a verified domain; defaults to `agentmail.to` |
| `display_name` | string | No | Display name shown in email From header |
| `client_id` | string | No | Idempotency key for safe retries |

### Code Examples

**Python:**

```python
from agentmail import AgentMail

client = AgentMail()

# Create inbox with idempotency
inbox = client.inboxes.create(
    username="support-agent",
    domain="agentmail.to",
    display_name="Support Bot",
    client_id="support-agent-inbox",
)
print(f"Created: {inbox.inbox_id}")  # support-agent@agentmail.to

# Update display name
client.inboxes.update(
    inbox_id=inbox.inbox_id,
    display_name="New Support Bot",
)

# Delete (async — returns 202 Accepted)
client.inboxes.delete(inbox_id=inbox.inbox_id)
```

**TypeScript:**

```typescript
const inbox = await client.inboxes.create({
    username: "support-agent",
    displayName: "Support Bot",
    clientId: "support-agent-inbox",
});
console.log(`Created: ${inbox.inboxId}`);

await client.inboxes.delete(inbox.inboxId);
```

---

## 7. Threads

### Description

A Thread represents a conversation (email chain). Threads are auto-created when messages are sent or received. They group related messages using the `In-Reply-To` and `References` email headers. Threads can be queried per-inbox, per-pod, or org-wide.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `thread_id` | UUID | Unique identifier |
| `inbox_id` | string | Parent inbox email address |
| `labels` | string[] | Thread-level labels |
| `timestamp` | datetime | Latest activity timestamp |
| `received_timestamp` | datetime | Latest received message time |
| `sent_timestamp` | datetime | Latest sent message time |
| `senders` | string[] | All sender addresses in the thread |
| `recipients` | string[] | All recipient addresses in the thread |
| `subject` | string | Thread subject |
| `preview` | string | Preview text of latest message |
| `attachments` | Attachment[] | Attachments across the thread |
| `last_message_id` | string | ID of the most recent message |
| `message_count` | number | Total messages in thread |
| `size` | number | Total size in bytes |
| `messages` | Message[] | Full message list (on `get` only) |
| `updated_at` | datetime | Last update |
| `created_at` | datetime | Thread creation time |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/threads` | List threads org-wide |
| GET | `/inboxes/{inbox_id}/threads` | List threads for an inbox |
| GET | `/pods/{pod_id}/threads` | List threads for a pod |
| GET | `/threads/{thread_id}` | Get thread with messages |
| GET | `/inboxes/{inbox_id}/threads/{thread_id}` | Get thread (inbox-scoped) |
| GET | `/threads/{thread_id}/attachments/{attachment_id}` | Get thread attachment |
| DELETE | `/threads/{thread_id}` | Delete thread (async) |
| DELETE | `/inboxes/{inbox_id}/threads/{thread_id}` | Delete thread (inbox-scoped) |

### List Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 50 | Max results per page |
| `page_token` | string | — | Pagination cursor |
| `ascending` | boolean | false | Sort order by timestamp |
| `labels` | string[] | — | Filter by labels |
| `before` | datetime | — | Threads before this time |
| `after` | datetime | — | Threads after this time |

### Code Example

**Python:**

```python
# List threads with label filter
threads = client.inboxes.threads.list(
    inbox_id="agent@agentmail.to",
    labels=["unread"],
    limit=10,
)
for t in threads.threads:
    print(f"[{t.thread_id}] {t.subject} ({t.message_count} msgs)")

# Get full thread with all messages
thread = client.inboxes.threads.get(
    inbox_id="agent@agentmail.to",
    thread_id=threads.threads[0].thread_id,
)
for msg in thread.messages:
    print(f"  {msg.from_}: {msg.extracted_text}")
```

---

## 8. Messages

### Description

A Message is an individual email within a thread. Messages support sending, replying, reply-all, forwarding, label management, raw RFC 2822 access, and attachment downloads. The `extracted_text` and `extracted_html` fields provide clean reply content with quoted text removed (via the Talon library).

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `message_id` | string | Unique identifier |
| `inbox_id` | string | Parent inbox |
| `thread_id` | UUID | Parent thread |
| `labels` | string[] | Message labels |
| `timestamp` | datetime | Message timestamp |
| `from` | string | Sender address (Python: `from_`) |
| `reply_to` | string[] | Reply-to addresses |
| `to` | string[] | Recipient addresses |
| `cc` | string[] | CC addresses |
| `bcc` | string[] | BCC addresses |
| `subject` | string | Subject line |
| `preview` | string | Preview text snippet |
| `text` | string | Full plain text body (includes quoted text) |
| `html` | string | Full HTML body |
| `extracted_text` | string | Clean reply text (no quoted text) |
| `extracted_html` | string | Clean reply HTML |
| `attachments` | Attachment[] | File attachments |
| `in_reply_to` | string | Message-ID this replies to |
| `references` | string[] | Reference chain |
| `headers` | object | Custom headers (user-provided only) |
| `size` | number | Message size in bytes |
| `updated_at` | datetime | Last update |
| `created_at` | datetime | Creation time |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/inboxes/{inbox_id}/messages` | List messages |
| GET | `/inboxes/{inbox_id}/messages/{message_id}` | Get message |
| POST | `/inboxes/{inbox_id}/messages/send` | Send new message |
| POST | `/inboxes/{inbox_id}/messages/{message_id}/reply` | Reply to message |
| POST | `/inboxes/{inbox_id}/messages/{message_id}/reply-all` | Reply all |
| POST | `/inboxes/{inbox_id}/messages/{message_id}/forward` | Forward message |
| PATCH | `/inboxes/{inbox_id}/messages/{message_id}` | Update labels |
| GET | `/inboxes/{inbox_id}/messages/{message_id}/raw` | Get raw RFC 2822 (302 redirect) |
| GET | `/inboxes/{inbox_id}/messages/{message_id}/attachments/{id}` | Get attachment |

### List Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | number | 50 | Max results per page |
| `page_token` | string | — | Pagination cursor |
| `ascending` | boolean | false | Sort by timestamp |
| `labels` | string[] | — | Filter by labels |
| `before` | datetime | — | Messages before this time |
| `after` | datetime | — | Messages after this time |
| `include_spam` | boolean | false | Include spam-flagged messages |
| `include_blocked` | boolean | false | Include blocked messages |
| `include_trash` | boolean | false | Include trashed messages |

### Send Message Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string[] | Yes | Recipient addresses |
| `cc` | string[] | No | CC recipients |
| `bcc` | string[] | No | BCC recipients |
| `subject` | string | No | Subject line |
| `text` | string | No | Plain text body |
| `html` | string | No | HTML body |
| `reply_to` | string[] | No | Reply-to addresses |
| `labels` | string[] | No | Labels to apply |
| `attachments` | object[] | No | File attachments (see [Attachments](#10-attachments)) |
| `headers` | object | No | Custom email headers |

### Reply Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | No | Plain text body |
| `html` | string | No | HTML body |
| `to` | string[] | No | Override recipient (see FAQ) |
| `labels` | string[] | No | Labels to apply |
| `attachments` | object[] | No | File attachments |

### Update Message Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `add_labels` | string[] | Labels to add |
| `remove_labels` | string[] | Labels to remove |

### Code Examples

**Python — Send and Reply:**

```python
# Send a new email
response = client.inboxes.messages.send(
    inbox_id="support@agentmail.to",
    to=["customer@example.com"],
    subject="Your order has shipped",
    text="Your order #12345 has shipped. Track it at ...",
    html="<p>Your order <b>#12345</b> has shipped.</p>",
    labels=["outbound", "orders"],
)
print(f"Sent message: {response.message_id}")

# Reply to a message
client.inboxes.messages.reply(
    inbox_id="support@agentmail.to",
    message_id="msg_abc123",
    text="Thanks for reaching out! We'll look into this.",
    html="<p>Thanks for reaching out! We'll look into this.</p>",
)

# Reply to a specific recipient (override default)
client.inboxes.messages.reply(
    inbox_id="support@agentmail.to",
    message_id="msg_abc123",
    to=["specific-person@example.com"],
    text="This reply goes to a specific person.",
)
```

**TypeScript — Send and Reply:**

```typescript
const response = await client.inboxes.messages.send("support@agentmail.to", {
    to: ["customer@example.com"],
    subject: "Your order has shipped",
    text: "Your order #12345 has shipped.",
    html: "<p>Your order <b>#12345</b> has shipped.</p>",
    labels: ["outbound", "orders"],
});

await client.inboxes.messages.reply("support@agentmail.to", "msg_abc123", {
    text: "Thanks for reaching out!",
});
```

**Python — List and Filter:**

```python
# Get unread messages from today
messages = client.inboxes.messages.list(
    inbox_id="agent@agentmail.to",
    labels=["unread"],
    after="2026-03-07T00:00:00Z",
    limit=25,
)

for msg in messages.messages:
    # Use extracted_text for clean reply content
    print(f"From: {msg.from_}, Subject: {msg.subject}")
    print(f"Clean content: {msg.extracted_text}")
```

---

## 9. Drafts

### Description

A Draft is an unsent message that can be composed, edited, scheduled, and sent later. Drafts support all the same fields as sent messages (recipients, body, attachments). Drafts can be scheduled for future delivery using the `send_at` parameter.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `draft_id` | UUID | Unique identifier |
| `inbox_id` | string | Parent inbox |
| `thread_id` | UUID | Thread (if replying) |
| `client_id` | string | Idempotency key |
| `labels` | string[] | Labels (auto-includes `draft`; `scheduled` if send_at set) |
| `to` | string[] | Recipients |
| `cc` | string[] | CC recipients |
| `bcc` | string[] | BCC recipients |
| `reply_to` | string[] | Reply-to addresses |
| `subject` | string | Subject line |
| `text` | string | Plain text body |
| `html` | string | HTML body |
| `attachments` | Attachment[] | File attachments |
| `in_reply_to` | string | Message-ID being replied to |
| `send_status` | enum | `scheduled`, `sending`, `failed` |
| `send_at` | datetime | Scheduled send time |
| `updated_at` | datetime | Last update |
| `created_at` | datetime | Creation time |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/inboxes/{inbox_id}/drafts` | Create a draft |
| GET | `/drafts` | List drafts org-wide |
| GET | `/inboxes/{inbox_id}/drafts` | List drafts for an inbox |
| GET | `/pods/{pod_id}/drafts` | List drafts for a pod |
| GET | `/drafts/{draft_id}` | Get draft |
| GET | `/inboxes/{inbox_id}/drafts/{draft_id}` | Get draft (inbox-scoped) |
| PATCH | `/inboxes/{inbox_id}/drafts/{draft_id}` | Update draft |
| POST | `/inboxes/{inbox_id}/drafts/{draft_id}/send` | Send draft now |
| DELETE | `/inboxes/{inbox_id}/drafts/{draft_id}` | Delete draft |
| GET | `/drafts/{draft_id}/attachments/{attachment_id}` | Get draft attachment |

### Code Example

**Python:**

```python
# Create a draft
draft = client.inboxes.drafts.create(
    inbox_id="support@agentmail.to",
    to=["customer@example.com"],
    subject="Follow-up on your request",
    text="Hi, just following up on...",
    html="<p>Hi, just following up on...</p>",
    client_id="draft-followup-123",
)

# Schedule it for later
client.inboxes.drafts.update(
    inbox_id="support@agentmail.to",
    draft_id=draft.draft_id,
    send_at="2026-03-08T09:00:00Z",
)

# Or send immediately
client.inboxes.drafts.send(
    inbox_id="support@agentmail.to",
    draft_id=draft.draft_id,
)
```

---

## 10. Attachments

### Description

Attachments are files associated with messages or drafts. When sending, attachments can be provided as base64-encoded content or as a URL. When receiving, attachments are stored in S3 and accessible via download endpoints.

### Attachment Properties (on received messages)

| Property | Type | Description |
|----------|------|-------------|
| `attachment_id` | UUID | Unique identifier |
| `filename` | string | Original filename |
| `size` | number | Size in bytes |
| `content_type` | string | MIME type (auto-inferred from filename if not set) |
| `content_disposition` | enum | `inline` or `attachment` |
| `content_id` | string | For embedded/inline images |

### Send Attachment Format

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `content` | string | One of content/url | Base64-encoded file content |
| `url` | string | One of content/url | URL to fetch the file from |
| `filename` | string | No | Filename for the attachment |
| `content_type` | string | No | MIME type (auto-inferred if omitted) |
| `content_id` | string | No | For inline images |

> **Note:** You must provide either `content` or `url`, not both.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/inboxes/{inbox_id}/messages/{message_id}/attachments/{attachment_id}` | Download message attachment |
| GET | `/threads/{thread_id}/attachments/{attachment_id}` | Download thread attachment |
| GET | `/drafts/{draft_id}/attachments/{attachment_id}` | Download draft attachment |

### Code Example

**Python — Send with Attachment:**

```python
import base64

with open("report.pdf", "rb") as f:
    content = base64.b64encode(f.read()).decode()

client.inboxes.messages.send(
    inbox_id="agent@agentmail.to",
    to=["user@example.com"],
    subject="Monthly report attached",
    text="Please find the report attached.",
    html="<p>Please find the report attached.</p>",
    attachments=[{
        "content": content,
        "filename": "report.pdf",
        "content_type": "application/pdf",
    }],
)
```

---

## 11. Domains

### Description

Custom domains allow you to send and receive email from your own domain (e.g., `support@yourcompany.com`) instead of the default `agentmail.to`. Domain setup requires DNS configuration for DKIM signing, SPF, DMARC, and MX records.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `domain_id` | string | Domain name (e.g., `yourcompany.com`) |
| `organization_id` | UUID | Parent organization |
| `pod_id` | UUID | Parent pod (optional) |
| `client_id` | string | Idempotency key |
| `feedback_enabled` | boolean | Enable bounce/complaint feedback (default: true) |
| `dkim_signing_type` | enum | `AWS_SES` or `BYODKIM` |
| `dkim_selector` | string | DKIM selector (default: `default`) |
| `status` | string | Verification status |
| `verification_records` | object[] | DNS records to configure |
| `updated_at` | datetime | Last update |
| `created_at` | datetime | Creation time |

### Verification Status Values

| Status | Description |
|--------|-------------|
| `NOT_STARTED` | Domain created, no DNS checks yet |
| `PENDING` | DNS records missing or not yet propagated |
| `VERIFYING` | DNS records detected, AWS verifying |
| `VERIFIED` | Fully verified, ready to use |
| `INVALID` | DNS records are incorrect |
| `FAILED` | AWS verification failed |

### DNS Records Required

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| MX | `@` | `inbound-smtp.{region}.amazonaws.com` (priority 10) | Receive email |
| MX | `mail` | `feedback-smtp.{region}.amazonses.com` (priority 10) | Bounce feedback |
| TXT | `mail` | `v=spf1 include:amazonses.com -all` | SPF authentication |
| TXT | `_dmarc` | `v=DMARC1; p=reject; rua=mailto:dmarc@{domain}` | DMARC policy |
| TXT | `{selector}._domainkey` | `v=DKIM1; k=rsa; p={publicKey}` | DKIM signing |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/domains` | Create/register a domain |
| POST | `/pods/{pod_id}/domains` | Create domain in a pod |
| GET | `/domains` | List domains |
| GET | `/pods/{pod_id}/domains` | List domains in a pod |
| GET | `/domains/{domain_id}` | Get domain details + verification status |
| GET | `/domains/{domain_id}/zone-file` | Download BIND zone file |
| POST | `/domains/{domain_id}/verify` | Trigger verification check |
| PATCH | `/domains/{domain_id}` | Update domain settings |
| DELETE | `/domains/{domain_id}` | Delete domain |

### Code Example

**Python:**

```python
# Register a custom domain
domain = client.domains.create(
    domain="mycompany.com",
    feedback_enabled=True,
)

# Print DNS records to configure
for record in domain.verification_records:
    print(f"Type: {record.type}, Name: {record.name}")
    print(f"Value: {record.value}")
    print(f"Status: {record.status}")
    print()

# After configuring DNS, trigger verification
client.domains.verify(domain_id="mycompany.com")

# Check status
domain = client.domains.get(domain_id="mycompany.com")
print(f"Status: {domain.status}")

# Download zone file for reference
zone_file = client.domains.get_zone_file(domain_id="mycompany.com")

# Create inbox on custom domain
inbox = client.inboxes.create(
    username="support",
    domain="mycompany.com",
    client_id="mycompany-support",
)
# → support@mycompany.com
```

> **Note:** DNS propagation typically takes 5–30 minutes but can take up to 48 hours. If your domain is stuck on "Pending," verify your DNS records are correct, then wait and retry.

---

## 12. Webhooks

### Description

Webhooks deliver real-time HTTP POST notifications when events occur (e.g., new email received). AgentMail uses [Svix](https://svix.com) for webhook delivery, which provides automatic retries, signature verification, and delivery tracking.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `webhook_id` | string | Unique identifier (Svix endpoint ID) |
| `url` | string | HTTPS endpoint URL (must be HTTPS) |
| `event_types` | string[] | Event types to subscribe to |
| `inbox_ids` | string[] | Scope to specific inboxes (optional) |
| `pod_ids` | string[] | Scope to specific pods (optional) |
| `secret` | string | Signing secret (starts with `whsec_`) |
| `enabled` | boolean | Whether the webhook is active |
| `client_id` | string | Idempotency key |
| `updated_at` | datetime | Last update |
| `created_at` | datetime | Creation time |

> **Note:** The `secret` is only returned when creating or getting a webhook. Store it securely for signature verification.

### Event Types

| Event Type | Description |
|------------|-------------|
| `message.received` | New email received by an inbox |
| `message.sent` | Email sent from an inbox |
| `message.delivered` | Email confirmed delivered to recipient's server |
| `message.bounced` | Email delivery failed (hard or soft bounce) |
| `message.complained` | Recipient marked email as spam |
| `message.rejected` | Email rejected before sending |
| `domain.verified` | Custom domain verification completed |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks` | Create a webhook |
| GET | `/webhooks` | List webhooks |
| GET | `/webhooks/{webhook_id}` | Get webhook (includes secret) |
| PATCH | `/webhooks/{webhook_id}` | Update webhook |
| DELETE | `/webhooks/{webhook_id}` | Delete webhook |

### Webhook Create Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | HTTPS callback URL |
| `event_types` | string[] | Yes | Events to subscribe to |
| `inbox_ids` | string[] | No | Scope to specific inboxes |
| `pod_ids` | string[] | No | Scope to specific pods |
| `client_id` | string | No | Idempotency key |

### Webhook Update Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | New callback URL |
| `add_inbox_ids` | string[] | Add inbox scopes |
| `remove_inbox_ids` | string[] | Remove inbox scopes |
| `add_pod_ids` | string[] | Add pod scopes |
| `remove_pod_ids` | string[] | Remove pod scopes |

> **Note:** Max 10 channels (inbox_ids + pod_ids) per webhook. Omit both for organization-level events.

### Code Example

**Python:**

```python
# Create a webhook
webhook = client.webhooks.create(
    url="https://myapp.example.com/webhooks/agentmail",
    event_types=["message.received", "message.bounced"],
    inbox_ids=["support@agentmail.to"],
    client_id="my-webhook",
)
print(f"Webhook ID: {webhook.webhook_id}")
print(f"Secret: {webhook.secret}")  # Store this securely!
```

**TypeScript:**

```typescript
const webhook = await client.webhooks.create({
    url: "https://myapp.example.com/webhooks/agentmail",
    eventTypes: ["message.received", "message.bounced"],
    inboxIds: ["support@agentmail.to"],
    clientId: "my-webhook",
});
console.log(`Secret: ${webhook.secret}`);
```

---

## 13. WebSockets

### Description

WebSockets provide real-time event streaming without needing a public URL. They are ideal for development, local environments, and persistent connections. Events are delivered in the same format as webhook payloads.

### Connection Flow

1. **Connect** with authentication (Bearer token in query or header)
2. **Subscribe** to specific inboxes, pods, or the entire organization
3. **Receive events** as they occur
4. **Unsubscribe** or **disconnect** when done

### Subscribe Message Format

```json
{
    "action": "subscribe",
    "inbox_ids": ["agent@agentmail.to"],
    "pod_ids": ["pod-uuid"],
    "event_types": ["message.received"]
}
```

All fields are optional. Omit both `inbox_ids` and `pod_ids` to subscribe to all organization events. Max 100 subscriptions per connection.

### Code Example

**Python (async):**

```python
import asyncio
from agentmail import AsyncAgentMail, Subscribe, MessageReceivedEvent

client = AsyncAgentMail()

async def main():
    async with client.websockets.connect() as socket:
        await socket.send_subscribe(Subscribe(
            inbox_ids=["agent@agentmail.to"]
        ))
        async for event in socket:
            if isinstance(event, MessageReceivedEvent):
                print(f"New: {event.message.subject} from {event.message.from_}")

asyncio.run(main())
```

**TypeScript:**

```typescript
const socket = await client.websockets.connect();

socket.on("open", () => {
    socket.sendSubscribe({
        type: "subscribe",
        inboxIds: ["agent@agentmail.to"],
    });
});

socket.on("message", (event) => {
    if (event.type === "message_received") {
        console.log(`New: ${event.message.subject}`);
    }
});
```

---

## 14. Metrics

### Description

Metrics provide aggregate analytics on email events (sends, deliveries, bounces, complaints, etc.) over time. Available at organization, pod, and inbox scope.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Org-wide metrics |
| GET | `/pods/{pod_id}/metrics` | Pod-level metrics |
| GET | `/inboxes/{inbox_id}/metrics` | Inbox-level metrics |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_types` | string[] | [] (all) | Filter by event types |
| `start` | datetime | 1 day ago | Start of time range (max 90 days) |
| `end` | datetime | now | End of time range |
| `period` | number | — | Bucket size in seconds (1–86400) |
| `limit` | number | 1000 | Max data points (1–1000) |
| `descending` | boolean | false | Sort order |

### Code Example

**Python:**

```python
metrics = client.inboxes.metrics.get(
    inbox_id="support@agentmail.to",
    event_types=["message.received", "message.sent"],
    start="2026-03-01T00:00:00Z",
    end="2026-03-07T23:59:59Z",
    period=86400,  # Daily buckets
)
```

---

## 15. Lists (Allow/Block)

### Description

Lists control which email addresses and domains your agents can send to or receive from. There are four list types formed by combining direction and type:

| Direction | Type | Purpose |
|-----------|------|---------|
| `receive` | `allow` | Only accept email from these addresses/domains |
| `receive` | `block` | Reject email from these addresses/domains |
| `send` | `allow` | Only send email to these addresses/domains |
| `send` | `block` | Prevent sending to these addresses/domains |

**Priority rules:**
- Pod-scoped entries take priority over org-scoped entries
- Email entries take priority over domain entries
- Allow lists take priority over block lists
- If any allow list has entries, addresses NOT in the allow list are implicitly blocked

### List Entry Properties

| Property | Type | Description |
|----------|------|-------------|
| `entry` | string | Email address or domain (normalized: lowercase, plus-addressing stripped) |
| `entry_type` | enum | `email` or `domain` (auto-detected) |
| `direction` | enum | `send` or `receive` |
| `list_type` | enum | `allow` or `block` |
| `reason` | string | Reason for blocking (block lists only) |
| `organization_id` | UUID | Parent organization |
| `pod_id` | UUID | Parent pod (optional) |
| `inbox_id` | string | Parent inbox (optional) |
| `created_at` | datetime | Creation time |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/lists/{direction}/{type}` | Create list entry |
| POST | `/pods/{pod_id}/lists/{direction}/{type}` | Create pod-scoped entry |
| GET | `/lists/{direction}/{type}` | List entries |
| GET | `/pods/{pod_id}/lists/{direction}/{type}` | List pod entries |
| GET | `/lists/{direction}/{type}/{entry}` | Get specific entry |
| DELETE | `/lists/{direction}/{type}/{entry}` | Delete entry |

### Create Entry Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entry` | string | Yes | Email address or domain |
| `reason` | string | No | Reason (for block lists) |

### Code Examples

**Python:**

```python
# Block a spammy sender
client.lists.create(
    direction="receive",
    type="block",
    entry="spam@example.com",
    reason="Persistent spam",
)

# Block an entire domain
client.lists.create(
    direction="receive",
    type="block",
    entry="spamdomain.com",
    reason="Known spam domain",
)

# Add to send allowlist (only send to approved addresses)
client.lists.create(
    direction="send",
    type="allow",
    entry="partner@trusted.com",
)

# List all receive blocklist entries
blocked = client.lists.list(direction="receive", type="block")
for entry in blocked.entries:
    print(f"Blocked: {entry.entry} — {entry.reason}")

# Remove from blocklist
client.lists.delete(
    direction="receive",
    type="block",
    entry="spam@example.com",
)
```

**TypeScript:**

```typescript
// Block a sender
await client.lists.create("receive", "block", {
    entry: "spam@example.com",
    reason: "Persistent spam",
});

// Add to send allowlist
await client.lists.create("send", "allow", {
    entry: "partner@trusted.com",
});

// List blocked senders
const blocked = await client.lists.list("receive", "block", { limit: 50 });
for (const entry of blocked.entries) {
    console.log(`Blocked: ${entry.entry} — ${entry.reason}`);
}

// Remove from blocklist
await client.lists.delete("receive", "block", "spam@example.com");
```

> **Note:** Entry normalization: `user+tag@domain.com` is normalized to `user@domain.com`. All entries are stored lowercase.

---

## 16. Error Handling

### Error Response Format

All API errors return a JSON body with `name` and `message` fields:

```json
{
    "name": "NotFoundError",
    "message": "Inbox not found"
}
```

Validation errors include a detailed `errors` array:

```json
{
    "name": "ValidationError",
    "errors": [
        {
            "code": "invalid_format",
            "format": "email",
            "path": ["to", 0],
            "message": "Invalid email format"
        }
    ]
}
```

### Error Types Table

| Error Name | HTTP Status | When It Occurs |
|------------|-------------|----------------|
| `UnauthorizedError` | 401 | Missing or invalid API key |
| `ForbiddenError` | 403 | Insufficient permissions |
| `NotFoundError` | 404 | Resource not found (or wrong organization) |
| `ValidationError` | 400 | Invalid request parameters |
| `AlreadyExistsError` | 403 | Resource already exists |
| `IsTakenError` | 403 | Username/email is taken |
| `LimitExceededError` | 403 | Org limit reached (inboxes, sends, etc.) |
| `DomainNotVerifiedError` | 403 | Sending from unverified domain |
| `MessageRejectedError` | 403 | Email rejected (bounced address, policy) |
| `RaceConditionError` | 409 | Concurrent modification conflict |
| `CannotDeleteError` | 409 | Resource has dependencies (e.g., pod with inboxes) |
| `RateLimitError` | 429 | Too many requests (includes `Retry-After` header) |
| `InvalidPageTokenError` | 400 | Malformed pagination token |
| `ServerError` | 500 | Unexpected internal error |

### Common Scenarios Table

| Scenario | Error | Resolution |
|----------|-------|------------|
| Sending to a bounced address | `MessageRejectedError` (403) | Bounced addresses are permanently blocked. Use a different address. |
| Inbox username already taken | `IsTakenError` (403) | Choose a different username |
| Sending from unverified domain | `DomainNotVerifiedError` (403) | Complete domain verification first |
| Too many inboxes | `LimitExceededError` (403) | Upgrade plan or delete unused inboxes |
| Organization suspended | `ForbiddenError` (403) | Check `suspended_reason` — usually high bounce or complaint rate |
| Wrong API key / org | `NotFoundError` (404) | Resources from other orgs return 404, not 403 |
| Malformed page token | `InvalidPageTokenError` (400) | Use only tokens returned by the API |
| Deleting pod with inboxes | `CannotDeleteError` (409) | Delete all inboxes in the pod first |
| DynamoDB throttle | `RateLimitError` (429) | Retry with exponential backoff |

### Code Example — Error Handling

**Python:**

```python
from agentmail import AgentMail
from agentmail.core.api_error import ApiError
from agentmail.errors import NotFoundError, ValidationError, IsTakenError
from agentmail.messages import MessageRejectedError

client = AgentMail()

try:
    inbox = client.inboxes.get(inbox_id="nonexistent@agentmail.to")
except NotFoundError as e:
    print(f"Not found: {e.body.message}")
except ValidationError as e:
    print(f"Validation errors: {e.body.errors}")
except IsTakenError as e:
    print(f"Already taken: {e.body.message}")
except MessageRejectedError as e:
    print(f"Rejected: {e.body.message}")
except ApiError as e:
    print(f"API error {e.status_code}: {e.body}")
```

**TypeScript:**

```typescript
import { AgentMailError, AgentMailTimeoutError } from "agentmail";

try {
    await client.inboxes.get("nonexistent@agentmail.to");
} catch (err) {
    if (err instanceof AgentMailTimeoutError) {
        console.log("Request timed out");
    } else if (err instanceof AgentMailError) {
        console.log(`Status: ${err.statusCode}`);
        console.log(`Error: ${err.message}`);
        console.log(`Body: ${JSON.stringify(err.body)}`);
    }
}
```

---

## 17. Common Patterns

### Pagination

All list endpoints support cursor-based pagination with `limit`, `page_token`, and `ascending` parameters.

**Response format:**

```json
{
    "inboxes": [...],
    "page_token": "eyJjcmVhdGVkX2F0Ijoi...",
    "count": 50
}
```

- `page_token` is a base64url-encoded cursor. If `null` or absent, you've reached the last page.
- `count` is the number of items in the current page.
- `ascending` controls sort order (default: `false` = newest first).

**Python — Iterate all pages:**

```python
page_token = None
all_inboxes = []

while True:
    response = client.inboxes.list(limit=100, page_token=page_token)
    all_inboxes.extend(response.inboxes)

    if response.page_token is None:
        break
    page_token = response.page_token

print(f"Total: {len(all_inboxes)}")
```

**TypeScript:**

```typescript
let pageToken: string | undefined;
const allInboxes: any[] = [];

do {
    const response = await client.inboxes.list({ limit: 100, pageToken });
    allInboxes.push(...response.inboxes);
    pageToken = response.pageToken;
} while (pageToken);

console.log(`Total: ${allInboxes.length}`);
```

### Filtering

Messages and threads support rich filtering:

| Parameter | Type | Description |
|-----------|------|-------------|
| `labels` | string[] | Filter by labels (intersection) |
| `before` | ISO datetime | Items before this time |
| `after` | ISO datetime | Items after this time |
| `include_spam` | boolean | Include spam-labeled items |
| `include_blocked` | boolean | Include blocked items |
| `include_trash` | boolean | Include trashed items |

### Idempotency

Use `client_id` on create operations to prevent duplicates during retries. Supported on:

| Resource | `client_id` Support |
|----------|---------------------|
| Inbox | Yes |
| Pod | Yes |
| Webhook | Yes |
| Domain | Yes |
| Draft | Yes |

```python
# Safe to call multiple times — won't create duplicates
inbox = client.inboxes.create(
    username="my-agent",
    client_id="my-agent-inbox-v1",
)
```

If a resource with the same `client_id` already exists, the existing resource is returned instead of creating a new one.

### Async Deletion

Some resources use asynchronous deletion (returns `202 Accepted`):

| Resource | Delete Behavior |
|----------|----------------|
| Inbox | 202 Accepted, `delete_status: "deleting"`, purges threads/messages |
| Thread | 202 Accepted when `permanent: true` |
| Pod | Fails if child resources exist |

The resource is soft-deleted immediately (hidden from list queries), then child resources are purged asynchronously.

---

## 18. Validation Rules

### Field Formats

| Field | Format | Rule |
|-------|--------|------|
| Email | `user@domain.com` | Standard email format; plus-addressing allowed on receive |
| Domain | `example.com` | Regex: `/^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$/` |
| Username | string | Min 1 character |
| `client_id` | string | Any non-empty string |
| UUIDs | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | Standard UUID v4 |
| Timestamps | ISO 8601 | `2026-03-07T12:00:00Z` |
| Webhook URL | URL | **Must be HTTPS** |
| Display name | string | No special characters: `()<>@,;:\\"[]` |
| Attachment content | string | Base64-encoded |
| `page_token` | string | Base64url-encoded JSON (use only API-returned values) |

### HTML Sanitization

Received email HTML is sanitized: `<script>` tags are stripped. Custom headers are filtered to remove SES/provider system headers; only user-provided headers are stored.

---

## 19. Rate Limiting

### 429 Behavior

When rate-limited, the API returns:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 5
Content-Type: application/json

{
    "name": "RateLimitError",
    "message": "Rate limit exceeded"
}
```

The `Retry-After` header (in seconds) is included when available.

### Rate Limit Sources

| Source | Trigger | Details |
|--------|---------|---------|
| DynamoDB throttle | High throughput | `ProvisionedThroughputExceededException` → 429 |
| Organization daily limit | Exceeds `daily_send_limit` | `LimitExceededError` (403) |
| Organization monthly limit | Exceeds `monthly_send_limit` | `LimitExceededError` (403) |
| WebSocket subscriptions | > 100 per connection | `LimitExceededError` (403) |
| Webhook channels | > 10 per webhook | Validation error |

### Retry Strategy

**Python (built-in):** The SDK retries status 408, 429, and 5xx automatically (2 retries, exponential backoff with jitter).

**TypeScript (built-in):** Same behavior — 2 retries, exponential backoff (1s, 2s, 4s...) with ±20% jitter, capped at 60s. Honors `Retry-After` and `X-RateLimit-Reset` headers.

**Manual retry example:**

```python
import time
from agentmail.core.api_error import ApiError

def send_with_retry(client, inbox_id, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.inboxes.messages.send(inbox_id=inbox_id, **message)
        except ApiError as e:
            if e.status_code == 429 and attempt < max_retries - 1:
                wait = 2 ** attempt  # 1, 2, 4 seconds
                print(f"Rate limited. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
```

---

## 20. Webhooks Deep Dive

### Event Payload Structure

All webhook events include a common base:

```json
{
    "event_type": "message.received",
    "organization_id": "uuid",
    "pod_id": "uuid",
    "inbox_id": "agent@agentmail.to",
    "thread_id": "uuid",
    "message_id": "msg_xxx",
    "timestamp": "2026-03-07T12:00:00Z"
}
```

### Event-Specific Fields

**`message.received`** — Full thread and message data included:

```json
{
    "event_type": "message.received",
    "thread": { "thread_id": "...", "subject": "...", "messages": [...] },
    "message": { "message_id": "...", "from": "sender@example.com", "subject": "Hello", "text": "...", "html": "..." }
}
```

**`message.sent`** — Send confirmation with recipients:

```json
{
    "event_type": "message.sent",
    "recipients": ["user@example.com"]
}
```

**`message.bounced`** — Bounce details:

```json
{
    "event_type": "message.bounced",
    "feedback_id": "...",
    "type": "Permanent",
    "sub_type": "General",
    "report_mta": "...",
    "remote_mta": "...",
    "recipients": [
        { "address": "user@example.com", "action": "failed", "status": "5.1.1", "diagnostic_code": "..." }
    ]
}
```

**`message.complained`** — Spam complaint:

```json
{
    "event_type": "message.complained",
    "feedback_id": "...",
    "type": "abuse",
    "user_agent": "...",
    "recipients": ["user@example.com"]
}
```

**`message.delivered`** — Delivery confirmation:

```json
{
    "event_type": "message.delivered",
    "time_millis": 1234567890,
    "smtp_response": "250 2.0.0 Ok",
    "report_mta": "...",
    "remote_mta": "...",
    "recipients": ["user@example.com"]
}
```

**`message.rejected`** — Rejection reason:

```json
{
    "event_type": "message.rejected",
    "reason": "Bad content"
}
```

**`domain.verified`** — Domain verification complete (no additional fields beyond base).

### Signature Verification

AgentMail uses [Svix](https://svix.com) for webhook delivery and signing. Each webhook has a signing secret (prefix: `whsec_`) returned at creation time.

**Headers sent with each webhook request:**

| Header | Description |
|--------|-------------|
| `svix-id` | Unique message ID (consistent across retries) |
| `svix-timestamp` | Unix timestamp when the message was sent |
| `svix-signature` | Space-delimited signatures in format `v1,<base64>` |

**Python verification example:**

```python
from svix.webhooks import Webhook, WebhookVerificationError
from flask import Flask, request, Response

app = Flask(__name__)

# Store webhook secret from creation response
WEBHOOK_SECRET = "whsec_your_secret_here"

@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    # IMPORTANT: Use raw body, not parsed JSON
    payload = request.get_data(as_text=True)
    headers = dict(request.headers)

    wh = Webhook(WEBHOOK_SECRET)
    try:
        event = wh.verify(payload, headers)
    except WebhookVerificationError:
        return Response("Invalid signature", status=401)

    # Process the verified event
    if event["event_type"] == "message.received":
        message = event["message"]
        print(f"Verified email from {message['from']}: {message['subject']}")

    return Response(status=200)
```

**TypeScript verification example:**

```typescript
import express from "express";
import { Webhook } from "svix";

const app = express();

// IMPORTANT: Use raw body parser, not JSON
app.use("/webhooks", express.raw({ type: "application/json" }));

const WEBHOOK_SECRET = "whsec_your_secret_here";

app.post("/webhooks", (req, res) => {
    const wh = new Webhook(WEBHOOK_SECRET);
    try {
        const event = wh.verify(req.body.toString(), {
            "svix-id": req.headers["svix-id"] as string,
            "svix-timestamp": req.headers["svix-timestamp"] as string,
            "svix-signature": req.headers["svix-signature"] as string,
        });

        if (event.event_type === "message.received") {
            console.log(`Verified: ${event.message.subject}`);
        }

        res.sendStatus(200);
    } catch {
        res.sendStatus(401);
    }
});
```

> **Warning:** Signature verification requires the **exact raw request body**. If your framework parses the body before you verify, the signature check will fail. Use `request.get_data()` in Flask or `express.raw()` in Express.

### Common Webhook Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Signature verification fails | Body was parsed as JSON before verification | Use raw body access (see examples above) |
| Infinite reply loop | Webhook triggers reply on `message.sent` | Only handle `message.received`, ignore `message.sent` |
| Webhook not firing | Endpoint returns non-2xx | Your endpoint must return 200-299. Check logs. |
| Events delayed | Svix retry backoff | Events are retried with exponential backoff on failure |
| Missing events | Webhook scope too narrow | Check `inbox_ids`/`pod_ids` scope matches the source |

---

## 21. WebSockets Deep Dive

### Connection Flow

1. **Connect:** `wss://ws.agentmail.to` with Bearer token authentication
2. **Subscribe:** Send a subscribe message with optional inbox/pod/event filters
3. **Receive events:** Events pushed as JSON messages
4. **Unsubscribe:** Send unsubscribe message to stop receiving events
5. **Disconnect:** Close the WebSocket connection

### Subscribe/Unsubscribe Message Format

**Subscribe:**

```json
{
    "action": "subscribe",
    "inbox_ids": ["agent@agentmail.to"],
    "pod_ids": ["pod-uuid"],
    "event_types": ["message.received", "message.sent"]
}
```

**Unsubscribe:**

```json
{
    "action": "unsubscribe",
    "inbox_ids": ["agent@agentmail.to"],
    "pod_ids": ["pod-uuid"]
}
```

**Subscribe response:**

```json
{
    "type": "subscribed",
    "inbox_ids": ["agent@agentmail.to"],
    "pod_ids": ["pod-uuid"],
    "organization_id": "uuid"
}
```

### Limits

| Limit | Value |
|-------|-------|
| Max subscriptions per connection | 100 |
| Connection TTL | 24 hours |

### WebSocket vs Webhook

| Feature | WebSocket | Webhook |
|---------|-----------|---------|
| Requires public URL | No | Yes (HTTPS) |
| Best for | Development, persistent connections | Production, serverless |
| Delivery guarantee | At-most-once | At-least-once (Svix retries) |
| Signature verification | N/A (authenticated connection) | Svix HMAC |
| Auto-reconnect (Node SDK) | Yes (30 attempts) | N/A |
| Scaling | One connection per client | Unlimited endpoints |

---

## 22. Incoming & Outgoing Email Flow

### Incoming Email (Receive)

```
External Sender
  → Amazon SES (inbound)
    → Security Checks:
        ├── Virus scan (virusVerdict)
        ├── SPF check (spfVerdict)
        ├── DKIM check (dkimVerdict)
        ├── DMARC check (dmarcVerdict, if policy != 'none')
        └── Spam check (spamVerdict → labels as 'spam')
    → If failed: STOP_RULE_SET (message dropped)
    → Email parsed (mailparser)
    → HTML sanitized (scripts removed)
    → Recipient processing:
        ├── Plus-addressing stripped (user+tag@domain → user@domain)
        ├── Inbox lookup per recipient
        └── Block list check (pod then org, email then domain)
    → Thread matching (via In-Reply-To / References)
    → Storage:
        ├── Raw message → S3
        ├── Parsed body → S3
        ├── Attachments → S3
        └── Metadata → DynamoDB
    → Events dispatched (webhook + websocket)
```

### Security Checks Table

| Check | Verdict | Failed Action |
|-------|---------|---------------|
| Virus | `PASS` / `FAIL` | Message dropped |
| SPF | `PASS` / `FAIL` | Message dropped |
| DKIM | `PASS` / `FAIL` | Message dropped |
| DMARC | `PASS` / `FAIL` | Message dropped (only if policy != `none`) |
| Spam | `PASS` / `FAIL` | Message labeled `spam` (not dropped) |

### Outgoing Email (Send)

```
API Request (send/reply/reply-all/forward)
  → Validation:
      ├── Organization not suspended
      ├── Domain verified (DomainNotVerifiedError if not)
      ├── Send block list check
      ├── Daily/monthly send limit check
      └── Playground: recipient must have emailed you first
  → Message composition (nodemailer):
      ├── From: inbox_id (or "Display Name <inbox_id>")
      ├── Headers: user-provided only
      └── Attachments processed
  → SES SendEmailCommand
      ├── Email tags: org_id, pod_id, inbox_id, thread_id
      └── Returns SES MessageId
  → Storage:
      ├── Raw message → S3
      ├── Message body → S3
      ├── Attachments → S3
      └── Metadata → DynamoDB (labels: ['sent', ...])
  → Thread created/updated
  → Contact tracking (bounce/complaint status)
```

### Contact Tracking

| Status | Effect |
|--------|--------|
| `bounced` | Address permanently blocked from sending |
| `complained` | Address permanently blocked from sending |

> **Warning:** Bounced and complained addresses are permanently blocked. Keep bounce rate below 4% or your organization may be suspended.

---

## 23. Common Support Questions & FAQ

### "Why am I getting 404 when sending a message?"

**Possible causes:**

1. **Wrong `inbox_id`:** The inbox_id is the full email address (e.g., `agent@agentmail.to`), not a UUID.
2. **Wrong API key:** The API key belongs to a different organization than the inbox. Resources from other orgs always return 404.
3. **Inbox deleted:** The inbox was deleted (async deletion). Check by listing inboxes.
4. **Domain not verified:** If using a custom domain, the domain must be verified before the inbox can send.
5. **Free tier/playground restriction:** Playground accounts can only send to addresses that have previously emailed that inbox.

### "My reply is going to the wrong person"

By default, `reply` sends to the original sender (the `from` address of the message being replied to). To override this:

```python
# Override the 'to' field in the reply
client.inboxes.messages.reply(
    inbox_id="support@agentmail.to",
    message_id="msg_abc123",
    to=["specific-person@example.com"],  # <-- explicit override
    text="This goes to the specific person, not the original sender.",
)
```

```typescript
await client.inboxes.messages.reply("support@agentmail.to", "msg_abc123", {
    to: ["specific-person@example.com"],
    text: "This goes to the specific person.",
});
```

Use `reply_all` / `replyAll` to reply to all recipients of the original message.

### "How do I verify webhook signatures?"

Use the [Svix](https://docs.svix.com) library. Install `svix` (`pip install svix` or `npm install svix`), then verify using the raw request body and the `svix-id`, `svix-timestamp`, and `svix-signature` headers. See [Section 20](#20-webhooks-deep-dive) for complete code examples.

The signing secret (prefix `whsec_`) is returned when you create or get a webhook:

```python
webhook = client.webhooks.get(webhook_id="wh_xxx")
secret = webhook.secret  # "whsec_..."
```

### "My domain is stuck on Pending"

1. **DNS propagation:** DNS changes take 5–30 minutes, sometimes up to 48 hours. Wait and retry.
2. **Verify DNS records:** Use `dig` or an online tool to check your records are correct:
   ```bash
   dig MX yourcompany.com
   dig TXT mail.yourcompany.com
   dig TXT _dmarc.yourcompany.com
   dig TXT default._domainkey.yourcompany.com
   ```
3. **Download zone file:** Use `GET /domains/{domain_id}/zone-file` to see the expected records.
4. **Trigger re-verification:** `POST /domains/{domain_id}/verify` to force a check.
5. **Common mistake (AWS Route 53):** DKIM TXT records must be split into two quoted strings with NO space between them: `"first-part""second-part"` (not `"first-part" "second-part"`).
6. **Only one SPF record per domain:** Merge multiple services: `v=spf1 include:amazonses.com include:other.com ~all`

### "How do I use allowlists/blocklists?"

Use the Lists resource. There are four list types: `receive/allow`, `receive/block`, `send/allow`, `send/block`. See [Section 15](#15-lists-allowblock) for complete endpoint documentation and code examples.

Key behavior:
- If a `receive/allow` list has any entries, only those addresses/domains can email you (implicit block for everything else).
- Block lists accept an optional `reason` parameter.
- Entries are normalized (lowercase, plus-addressing stripped).

### "What's `client_id` for?"

`client_id` is an idempotency key. If you create a resource with a `client_id` and a resource with that same `client_id` already exists, the existing resource is returned instead of creating a duplicate. This is safe for retries and agent restarts.

```python
# Safe to call on every agent startup — won't create duplicates
inbox = client.inboxes.create(
    username="my-agent",
    client_id="my-agent-inbox-v1",
)
```

### "What are Playground restrictions?"

Playground/trial accounts have the following restrictions:
- **Can only send to addresses that have previously emailed you** (or SES test domains)
- Limited daily and monthly send quotas
- Limited number of inboxes and domains
- The `is_playground` flag is set on the organization

### "How do I get clean reply text without quoted content?"

Use the `extracted_text` and `extracted_html` fields on the Message object. These use the Talon library to strip quoted text, signatures, and forwarded content:

```python
message = client.inboxes.messages.get(
    inbox_id="agent@agentmail.to",
    message_id="msg_abc123",
)

# Full email (includes quoted text, signatures, etc.)
full = message.text

# Clean reply only (no quoted text)
clean = message.extracted_text
```

### "Why was my organization suspended?"

Check `suspended_reason` on the organization:
- `bounce_rate`: Your bounce rate exceeded 4%. Clean your recipient lists.
- `complaint_rate`: Too many spam complaints. Review your sending practices.

```python
org = client.organizations.get()
if org.suspended_at:
    print(f"Suspended: {org.suspended_reason}")
```

---

## 24. Resource Relationships

### Hierarchy Diagram

```
Organization
├── Pod (multi-tenancy)
│   ├── Inbox → Thread → Message → Attachment
│   │            └── Draft → Attachment
│   ├── Domain (custom email domain)
│   ├── List Entry (allow/block rule)
│   └── API Key (pod-scoped)
│
├── Inbox → Thread → Message → Attachment  (org-level, default pod)
│            └── Draft → Attachment
├── Domain (org-level)
├── Webhook → Event Types (Svix-managed)
├── API Key (org-level)
├── List Entry (org-level)
├── WebSocket Connection → Subscriptions
└── Metrics
```

### Key Relationships

| Relationship | Description |
|-------------|-------------|
| Organization → Pod | One-to-many. Pods are optional. |
| Pod → Inbox | One-to-many. Inbox belongs to exactly one pod. |
| Inbox → Thread | One-to-many. Threads auto-created. |
| Thread → Message | One-to-many. Ordered by timestamp ascending. |
| Message → Attachment | One-to-many. |
| Domain → Inbox | Domain must be verified before inboxes can use it. |
| Webhook → Events | Webhook subscribes to event types, scoped by inbox/pod. |
| API Key → Pod | Optional scope. Pod-scoped keys can only access that pod. |

### Authorization Model

- All resources are **organization-scoped**. Accessing a resource from a different organization returns `404` (not `403`).
- **Pod-scoped API keys** can only access resources within their pod.
- **Path-based authorization:** If a pod_id or inbox_id in the URL doesn't match the API key scope, the request is rejected.

---

## 25. Quick Reference

### Most-Used Endpoints

| Action | Method | Path |
|--------|--------|------|
| Create inbox | POST | `/v0/inboxes` |
| List inboxes | GET | `/v0/inboxes` |
| Send message | POST | `/v0/inboxes/{inbox_id}/messages/send` |
| Reply | POST | `/v0/inboxes/{inbox_id}/messages/{msg_id}/reply` |
| Reply All | POST | `/v0/inboxes/{inbox_id}/messages/{msg_id}/reply-all` |
| List messages | GET | `/v0/inboxes/{inbox_id}/messages` |
| Get message | GET | `/v0/inboxes/{inbox_id}/messages/{msg_id}` |
| Update labels | PATCH | `/v0/inboxes/{inbox_id}/messages/{msg_id}` |
| List threads | GET | `/v0/inboxes/{inbox_id}/threads` |
| Create webhook | POST | `/v0/webhooks` |
| Create domain | POST | `/v0/domains` |
| Add to blocklist | POST | `/v0/lists/receive/block` |
| Get org info | GET | `/v0/organizations` |

### Cheat Sheet — 4 Common Operations

**1. Create Inbox:**

```python
inbox = client.inboxes.create(username="my-agent", client_id="my-agent-inbox")
```

```typescript
const inbox = await client.inboxes.create({ username: "my-agent", clientId: "my-agent-inbox" });
```

**2. Send Message:**

```python
client.inboxes.messages.send(
    inbox_id="my-agent@agentmail.to",
    to=["user@example.com"],
    subject="Hello",
    text="Hello from my agent!",
    html="<p>Hello from my agent!</p>",
)
```

```typescript
await client.inboxes.messages.send("my-agent@agentmail.to", {
    to: ["user@example.com"],
    subject: "Hello",
    text: "Hello from my agent!",
    html: "<p>Hello from my agent!</p>",
});
```

**3. Reply to Message:**

```python
client.inboxes.messages.reply(
    inbox_id="my-agent@agentmail.to",
    message_id="msg_abc123",
    text="Thanks for your email!",
)
```

```typescript
await client.inboxes.messages.reply("my-agent@agentmail.to", "msg_abc123", {
    text: "Thanks for your email!",
});
```

**4. Create Webhook:**

```python
webhook = client.webhooks.create(
    url="https://myapp.com/webhooks",
    event_types=["message.received"],
    client_id="my-webhook",
)
```

```typescript
const webhook = await client.webhooks.create({
    url: "https://myapp.com/webhooks",
    eventTypes: ["message.received"],
    clientId: "my-webhook",
});
```

---

*Report compiled from source code analysis of `agentmail-api/`, Python SDK (v0.2.24), TypeScript SDK (v0.4.3), and official documentation at docs.agentmail.to.*
