# AgentMail API Documentation

This document provides a comprehensive overview of the AgentMail API, a TypeScript AWS serverless email API backend. It covers all resources, endpoints, error handling, authentication, webhooks, relationships, and common patterns.

---

## Table of Contents

1. [API Resources Overview](#api-resources-overview)
2. [Authentication](#authentication)
3. [Organizations](#organizations)
4. [Pods](#pods)
5. [API Keys](#api-keys)
6. [Inboxes](#inboxes)
7. [Threads](#threads)
8. [Messages](#messages)
9. [Drafts](#drafts)
10. [Attachments](#attachments)
11. [Domains](#domains)
12. [Webhooks](#webhooks)
13. [WebSockets](#websockets)
14. [Metrics](#metrics)
15. [Error Handling](#error-handling)
16. [Common Patterns](#common-patterns)
17. [Rate Limiting](#rate-limiting)
18. [Validation Rules](#validation-rules)
19. [Resource Relationships](#resource-relationships)

---

## API Resources Overview

The AgentMail API provides the following core resources:

| Resource | Description |
|----------|-------------|
| **Organizations** | Top-level tenant/account that owns all other resources |
| **Pods** | Logical groupings of inboxes within an organization (for multi-tenant scenarios) |
| **API Keys** | Authentication tokens for programmatic API access |
| **Inboxes** | Email addresses that can send and receive emails |
| **Threads** | Conversation threads grouping related messages |
| **Messages** | Individual email messages within threads |
| **Drafts** | Unsent email drafts that can be scheduled or sent later |
| **Attachments** | Files attached to messages or drafts |
| **Domains** | Custom email domains for sending (requires DNS verification) |
| **Webhooks** | HTTP endpoints that receive real-time event notifications |
| **Connections** | WebSocket connections for real-time streaming events |
| **Metrics** | Analytics data for email events (sent, delivered, bounced, etc.) |

---

## Authentication

### Overview

The API supports two authentication methods:

1. **API Keys** - For programmatic/automated access
2. **JWT Tokens** - For dashboard/user sessions

### API Key Authentication

- API keys are prefixed with `am_` followed by 64 hexadecimal characters
- Keys are stored as SHA-256 hashes (the plaintext is never stored)
- Only the first 8 characters (prefix) are stored for identification
- The `used_at` timestamp is updated on each API call
- API keys are scoped to a single organization

### JWT Authentication

- Supports both AgentMail-issued JWTs and Clerk-issued JWTs
- JWTs contain the `organizationId` in the payload
- Verified using public keys stored in environment configuration

### Authorization Flow

1. Request includes `Authorization` header with bearer token
2. System determines if token is JWT (contains 3 dot-separated parts) or API key
3. For API keys: hash the token, look up in database, return organization_id
4. For JWTs: verify signature, extract organization_id from payload
5. Organization is fetched to get additional context (is_playground, is_paid status)
6. Protected routes receive organization context in the authorizer response

### Authorizer Context

All protected endpoints receive:
- `organization_id` - The authenticated organization's UUID
- `is_playground` - Boolean indicating if this is a playground/sandbox organization
- `is_paid` - Boolean indicating if the organization has a paid subscription (based on domain_limit)

---

## Organizations

### Description

An organization is the top-level tenant that owns all resources. Organizations track resource counts and limits, and may have Stripe billing integration.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Unique identifier |
| external_id | String (optional) | External reference ID (e.g., Clerk organization ID) |
| stripe_customer_id | String (optional) | Stripe customer ID for billing |
| stripe_subscription_id | String (optional) | Stripe subscription ID |
| is_playground | Boolean (optional) | Whether this is a sandbox/test organization |
| inbox_limit | Number (optional) | Maximum number of inboxes allowed |
| domain_limit | Number (optional) | Maximum number of custom domains allowed |
| inbox_count | Number | Current number of inboxes |
| domain_count | Number | Current number of domains |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/organizations` | Create a new organization (public endpoint) |
| POST | `/organizations/claim` | Claim/link an organization to an external ID |
| GET | `/organizations` | Get the authenticated organization's details |

### Create Organization

Creates a new organization. This is a public endpoint (no authentication required).

**Optional Parameters:**
- `is_playground` - Set to true for sandbox environments

**Behavior:**
- Generates a new UUID for the organization
- Sets default limits: inbox_limit=3, domain_limit=0
- Creates a default pod with the same ID as the organization

### Get Organization

Returns the authenticated organization's details including resource counts and limits.

---

## Pods

### Description

Pods are logical groupings of inboxes within an organization. They enable multi-tenant scenarios where different projects or customers need isolated inbox groups. Every organization has a default pod with the same ID as the organization.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| pod_id | UUID | Unique identifier |
| name | String | Display name for the pod |
| client_id | String (optional) | Client-provided idempotency key |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/pods` | Create a new pod |
| GET | `/pods` | List all pods in the organization |
| GET | `/pods/{pod_id}` | Get a specific pod |
| DELETE | `/pods/{pod_id}` | Delete a pod |

### Create Pod

Creates a new pod within the organization.

**Optional Parameters:**
- `name` - Display name (defaults to "My Pod")
- `client_id` - Idempotency key for deduplication

**Idempotency:** If a `client_id` is provided and a pod with that client_id already exists, the existing pod is returned instead of creating a new one.

### Delete Pod

Deletes a pod from the organization.

**Restrictions:**
- Cannot delete the default pod (where pod_id equals organization_id)
- Cannot delete pods that contain inboxes (must delete all inboxes first)

---

## API Keys

### Description

API keys provide programmatic access to the API. They are organization-scoped and can be created and revoked as needed.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| api_key_id | UUID | Unique identifier |
| hash | String | SHA-256 hash of the API key (internal) |
| prefix | String | First 8 characters for identification |
| name | String | Display name |
| used_at | ISO DateTime (optional) | Last usage timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api-keys` | Create a new API key |
| GET | `/api-keys` | List all API keys |
| DELETE | `/api-keys/{api_key_id}` | Delete an API key |

### Create API Key

Creates a new API key for the organization.

**Optional Parameters:**
- `name` - Display name (defaults to "My API Key")

**Response:** Returns the full API key token ONLY at creation time. The token is never stored or retrievable again. The response includes:
- `api_key` - The full token (am_xxx...)
- `api_key_id` - UUID for management
- `prefix` - First 8 characters
- `name` - Display name
- `created_at` - Creation timestamp

### List API Keys

Returns all API keys for the organization. Note that the actual key values are not returned, only the prefix and metadata.

---

## Inboxes

### Description

Inboxes are email addresses that can send and receive emails. Each inbox belongs to a pod (and transitively to an organization). Inboxes can use either the default AgentMail domain or a custom verified domain.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| pod_id | UUID | Parent pod |
| inbox_id | Email | The email address (serves as unique ID) |
| client_id | String (optional) | Client-provided idempotency key |
| display_name | String (optional) | Sender display name |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/inboxes` | Create inbox in default pod |
| POST | `/pods/{pod_id}/inboxes` | Create inbox in specific pod |
| GET | `/inboxes` | List all inboxes in organization |
| GET | `/pods/{pod_id}/inboxes` | List inboxes in a pod |
| GET | `/inboxes/{inbox_id}` | Get a specific inbox |
| GET | `/pods/{pod_id}/inboxes/{inbox_id}` | Get inbox within pod context |
| PATCH | `/inboxes/{inbox_id}` | Update inbox |
| PATCH | `/pods/{pod_id}/inboxes/{inbox_id}` | Update inbox within pod context |
| DELETE | `/inboxes/{inbox_id}` | Delete inbox |
| DELETE | `/pods/{pod_id}/inboxes/{inbox_id}` | Delete inbox within pod context |

### Create Inbox

Creates a new inbox email address.

**Optional Parameters:**
- `username` - Local part of email (auto-generated if not provided)
- `domain` - Domain to use (defaults to AgentMail's shared domain)
- `display_name` - Sender name (defaults to "AgentMail")
- `client_id` - Idempotency key

**Username Generation:** If not specified, generates a random username in the format `{adjective}{noun}{number}` (e.g., "happycat123").

**Domain Requirements:**
- If using a custom domain, it must be verified and belong to the same organization
- If the domain belongs to a specific pod, the inbox must be created in that pod

**Limits:** Creating an inbox increments the organization's inbox_count. If inbox_count would exceed inbox_limit, the request fails with LimitExceededError.

**Idempotency:** If client_id is provided and an inbox with that client_id exists, returns the existing inbox.

### Update Inbox

Updates inbox properties.

**Updateable Fields:**
- `display_name` - The sender display name

### Delete Inbox

Initiates async deletion of an inbox and all associated data.

**Behavior:**
1. Marks the inbox with `delete_status: 'deleting'`
2. Decrements organization's inbox_count
3. Enqueues a purge job to delete all child resources (threads, messages, drafts)
4. Returns 202 Accepted immediately

**Note:** Deletion is asynchronous. The inbox and its data may remain queryable briefly while background deletion processes.

---

## Threads

### Description

Threads group related email messages into conversations. A thread is created when a message is received or sent, and subsequent replies are automatically grouped into the same thread based on In-Reply-To and References headers.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| pod_id | UUID | Parent pod |
| inbox_id | Email | Parent inbox |
| thread_id | UUID | Unique identifier |
| labels | String[] | Thread labels (e.g., "received", "sent", "unread") |
| timestamp | ISO DateTime | Timestamp of most recent message |
| received_timestamp | ISO DateTime (optional) | Timestamp of most recent received message |
| sent_timestamp | ISO DateTime (optional) | Timestamp of most recent sent message |
| senders | String[] | All unique sender addresses |
| recipients | String[] | All unique recipient addresses |
| subject | String (optional) | Thread subject line |
| preview | String (optional) | Preview text from latest message |
| attachments | Attachment[] (optional) | Aggregated attachments from all messages |
| last_message_id | String | ID of the most recent message |
| message_count | Number | Total messages in thread |
| size | Number | Total size in bytes |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/threads` | List all threads in organization |
| GET | `/inboxes/{inbox_id}/threads` | List threads in an inbox |
| GET | `/pods/{pod_id}/threads` | List threads in a pod |
| GET | `/threads/{thread_id}` | Get thread with all messages |
| GET | `/inboxes/{inbox_id}/threads/{thread_id}` | Get thread within inbox context |
| GET | `/pods/{pod_id}/threads/{thread_id}` | Get thread within pod context |
| DELETE | `/threads/{thread_id}` | Delete a thread |
| DELETE | `/inboxes/{inbox_id}/threads/{thread_id}` | Delete thread within inbox context |

### List Threads

Returns paginated threads with filtering and sorting options.

**Query Parameters:**
- `limit` - Maximum results to return
- `page_token` - Pagination token from previous response
- `labels` - Filter by labels (comma-separated)
- `before` - Filter messages before this timestamp
- `after` - Filter messages after this timestamp
- `ascending` - Sort order (default: descending/newest first)
- `include_spam` - Include spam-labeled threads (default: false)

**Label Filtering:**
- If labels include "received", uses received_timestamp index
- If labels include "sent" (but not "received"), uses sent_timestamp index
- Spam threads are excluded by default

### Get Thread

Returns full thread details including all messages with their body content.

**Response includes:**
- Thread metadata (subject, participants, timestamps)
- Array of messages with full text/html content
- Extracted content (quoted text removed) when available

### Delete Thread

Initiates async deletion of a thread and all its messages.

**Behavior:**
1. Marks thread with `delete_status: 'deleting'`
2. Enqueues purge job for child message deletion
3. Returns 202 Accepted

---

## Messages

### Description

Messages are individual emails within a thread. They can be received (incoming) or sent (outgoing). Messages contain headers, body content, and optional attachments.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| pod_id | UUID | Parent pod |
| inbox_id | Email | Parent inbox |
| thread_id | UUID | Parent thread |
| message_id | String | Unique identifier (derived from SMTP Message-ID) |
| labels | String[] | Message labels |
| timestamp | ISO DateTime | Message timestamp |
| from | String | Sender address (with optional display name) |
| reply_to | String[] (optional) | Reply-To addresses |
| to | String[] (optional) | To recipients |
| cc | String[] (optional) | CC recipients |
| bcc | String[] (optional) | BCC recipients |
| subject | String (optional) | Subject line |
| preview | String (optional) | Plain text preview |
| text | String (optional) | Plain text body |
| html | String (optional) | HTML body |
| extracted_text | String (optional) | Text with quoted content removed |
| extracted_html | String (optional) | HTML with quoted content removed |
| attachments | Attachment[] (optional) | File attachments |
| in_reply_to | String (optional) | Message-ID being replied to |
| references | String[] (optional) | Chain of referenced Message-IDs |
| headers | Object (optional) | Custom headers (non-standard only) |
| smtp_id | String | Internal SMTP identifier |
| size | Number | Message size in bytes |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Standard Labels

| Label | Description |
|-------|-------------|
| `received` | Incoming message |
| `sent` | Outgoing message |
| `unread` | Not yet read |
| `spam` | Detected as spam |
| `bounced` | Delivery bounced |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/inboxes/{inbox_id}/messages` | List messages in an inbox |
| GET | `/inboxes/{inbox_id}/messages/{message_id}` | Get a specific message |
| GET | `/inboxes/{inbox_id}/messages/{message_id}/raw` | Get raw .eml file |
| POST | `/inboxes/{inbox_id}/messages/send` | Send a new message |
| POST | `/inboxes/{inbox_id}/messages/{message_id}/reply` | Reply to a message |
| POST | `/inboxes/{inbox_id}/messages/{message_id}/reply-all` | Reply-all to a message |
| PATCH | `/inboxes/{inbox_id}/messages/{message_id}` | Update message labels |

### List Messages

Returns paginated messages for an inbox.

**Query Parameters:**
- `limit` - Maximum results
- `page_token` - Pagination token
- `labels` - Filter by labels
- `before` / `after` - Timestamp filters
- `ascending` - Sort order
- `include_spam` - Include spam messages

### Get Message

Returns full message content including text and HTML bodies.

**Content Extraction:**
The API attempts to extract the "new" content from replies by removing quoted text. Results are returned in `extracted_text` and `extracted_html` fields.

### Get Raw Message

Returns a redirect (302) to a signed S3 URL for downloading the original .eml file.

**URL Expiration:** Signed URLs expire after 1 hour.

### Send Message

Sends a new email message from the inbox.

**Required Parameters:**
- At least one of: `to`, `cc`, or `bcc` recipients

**Optional Parameters:**
- `subject` - Subject line
- `text` - Plain text body
- `html` - HTML body (automatically sanitized)
- `reply_to` - Reply-To addresses
- `labels` - Custom labels to apply
- `attachments` - File attachments (base64-encoded content)
- `headers` - Custom email headers
- `in_reply_to` - Message-ID for threading

**Playground Restrictions:**
Playground organizations can only send to addresses they have previously received emails from (or to other AgentMail addresses).

**Bounce/Complaint Protection:**
Messages cannot be sent to addresses that have previously bounced or filed complaints.

**Response:**
- `message_id` - The new message's ID
- `thread_id` - The thread ID (new or existing)

### Reply to Message

Sends a reply to an existing message.

**Automatic Behavior:**
- Sets In-Reply-To header to original message ID
- Appends to References chain
- Uses original subject with "Re:" prefix if not specified
- Quotes original message in body

**Parameters:**
- `to` - Override recipients (defaults to original sender/reply-to)
- `cc` - CC recipients
- `bcc` - BCC recipients
- `reply_all` - Set true to reply to all original recipients
- `subject` - Override subject
- `text` / `html` - Reply body
- `attachments` - New attachments

**Note:** Cannot specify `to`, `cc`, or `bcc` when `reply_all` is true.

### Reply All

Convenience endpoint for reply-all. Automatically includes all original recipients (To and CC) except the sending inbox.

### Update Message

Modifies message labels.

**Parameters:**
- `add_labels` - Labels to add
- `remove_labels` - Labels to remove

**Behavior:** Also updates the parent thread's aggregated labels.

---

## Drafts

### Description

Drafts are unsent email messages that can be saved, edited, and sent later. They support scheduling for future sending.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| pod_id | UUID (optional) | Parent pod |
| inbox_id | Email | Parent inbox |
| draft_id | UUID | Unique identifier |
| client_id | String (optional) | Idempotency key |
| labels | String[] | Draft labels |
| reply_to | String[] (optional) | Reply-To addresses |
| to | String[] (optional) | To recipients |
| cc | String[] (optional) | CC recipients |
| bcc | String[] (optional) | BCC recipients |
| subject | String (optional) | Subject line |
| preview | String (optional) | Preview text |
| text | String (optional) | Plain text body |
| html | String (optional) | HTML body |
| attachments | Attachment[] (optional) | Attachments |
| in_reply_to | String (optional) | Message being replied to |
| references | String[] (optional) | Reference chain |
| send_status | Enum (optional) | "scheduled", "sending", or "failed" |
| send_at | ISO DateTime (optional) | Scheduled send time |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/inboxes/{inbox_id}/drafts` | Create a draft |
| GET | `/drafts` | List all drafts in organization |
| GET | `/drafts/{draft_id}` | Get a specific draft |
| GET | `/inboxes/{inbox_id}/drafts` | List drafts in an inbox |
| GET | `/inboxes/{inbox_id}/drafts/{draft_id}` | Get draft within inbox context |
| GET | `/pods/{pod_id}/drafts` | List drafts in a pod |
| GET | `/pods/{pod_id}/drafts/{draft_id}` | Get draft within pod context |
| PATCH | `/inboxes/{inbox_id}/drafts/{draft_id}` | Update a draft |
| DELETE | `/inboxes/{inbox_id}/drafts/{draft_id}` | Delete a draft |
| POST | `/inboxes/{inbox_id}/drafts/{draft_id}/send` | Send a draft |

### Create Draft

Creates a new draft email.

**Parameters:**
- `to`, `cc`, `bcc` - Recipients
- `subject` - Subject line
- `text` / `html` - Body content
- `reply_to` - Reply-To addresses
- `in_reply_to` - For reply drafts
- `labels` - Custom labels
- `send_at` - Schedule for future sending
- `client_id` - Idempotency key

**Automatic Labels:**
- Always includes "draft"
- Adds "scheduled" if send_at is provided

### Update Draft

Modifies draft content.

**Updateable Fields:**
- `to`, `cc`, `bcc`, `reply_to`
- `subject`
- `text`, `html`
- `send_at`

### Send Draft

Sends a draft immediately.

**Behavior:**
1. Validates draft content meets sending requirements
2. If draft is a reply (has in_reply_to), builds reply with quoted content
3. Sends the message
4. Deletes the draft
5. Returns the new message_id and thread_id

**Optional Parameters:**
- `add_labels` - Additional labels for sent message
- `remove_labels` - Labels to exclude from sent message

---

## Attachments

### Description

Attachments are files associated with messages. They are stored in S3 and accessed via signed URLs.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| attachment_id | UUID | Unique identifier |
| filename | String (optional) | Original filename |
| size | Number | Size in bytes |
| content_type | String (optional) | MIME type |
| content_disposition | Enum (optional) | "inline" or "attachment" |
| content_id | String (optional) | Content-ID for inline attachments |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/inboxes/{inbox_id}/messages/{message_id}/attachments/{attachment_id}` | Get attachment from message |
| GET | `/threads/{thread_id}/attachments/{attachment_id}` | Get attachment from thread |
| GET | `/inboxes/{inbox_id}/threads/{thread_id}/attachments/{attachment_id}` | Get attachment within inbox context |
| GET | `/pods/{pod_id}/threads/{thread_id}/attachments/{attachment_id}` | Get attachment within pod context |

### Get Attachment

Returns attachment metadata and a signed download URL.

**Response:**
- Attachment metadata (filename, size, content_type, etc.)
- `download_url` - Signed S3 URL for downloading
- `expires_at` - URL expiration timestamp

**URL Expiration:** Download URLs expire after 1 hour.

**Legacy Behavior:** Some older organizations receive a 302 redirect directly to the download URL instead of JSON metadata.

### Sending Attachments

When sending messages or creating drafts, attachments are provided as:

- `filename` - Desired filename
- `content` - Base64-encoded file content
- `content_type` - MIME type (auto-detected from filename if not provided)
- `content_disposition` - "inline" or "attachment" (defaults based on content_id)
- `content_id` - For inline/embedded images (automatically wrapped in angle brackets)

---

## Domains

### Description

Custom domains allow sending emails from your own domain instead of the shared AgentMail domain. Domains require DNS verification including DKIM, SPF, DMARC, and MX records.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| pod_id | UUID (optional) | Restricts domain to specific pod |
| domain_id | String | Domain name (serves as unique ID) |
| client_id | String (optional) | Idempotency key |
| feedback_enabled | Boolean | Whether to forward bounce/complaint emails |
| dkim_signing_type | Enum | "AWS_SES" (Easy DKIM) or "BYODKIM" (custom keys) |
| dkim_selector | String (optional) | DKIM selector for BYODKIM |
| status | String (optional) | Verification status |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Verification Statuses

| Status | Description |
|--------|-------------|
| NOT_STARTED | DNS records not yet configured |
| PENDING | DNS records detected, verification in progress |
| VERIFIED | All records verified, ready for sending |
| FAILED | Verification failed |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/domains` | Add a domain to organization |
| POST | `/pods/{pod_id}/domains` | Add domain restricted to pod |
| GET | `/domains` | List all domains |
| GET | `/pods/{pod_id}/domains` | List domains in a pod |
| GET | `/domains/{domain_id}` | Get domain details and status |
| GET | `/domains/{domain_id}/zone-file` | Get DNS records as zone file |
| PATCH | `/domains/{domain_id}` | Update domain settings |
| POST | `/domains/{domain_id}/verify` | Trigger verification check |
| DELETE | `/domains/{domain_id}` | Remove a domain |
| DELETE | `/pods/{pod_id}/domains/{domain_id}` | Remove domain from pod |

### Create Domain

Registers a new custom domain.

**Parameters:**
- `domain` - The domain name (e.g., "example.com")
- `client_id` - Idempotency key (optional)
- `feedback_enabled` - Forward bounce/complaint emails (default: true)

**Limits:** Creating a domain checks against domain_limit. Free organizations have domain_limit=0 (no custom domains).

**Response includes:**
- Domain metadata
- `records` - Array of required DNS records

### Required DNS Records

The API returns required DNS records that must be configured:

1. **DKIM Record** (TXT) - Email authentication signature
   - Name: `{selector}._domainkey.{domain}`
   - Value: Public key in DKIM format

2. **MX Record (Inbound)** - For receiving emails
   - Name: `{domain}`
   - Value: `inbound-smtp.{region}.amazonaws.com`
   - Priority: 10

3. **MX Record (Mail From)** - For sending emails
   - Name: `mail.{domain}`
   - Value: `feedback-smtp.{region}.amazonaws.com`
   - Priority: 10

4. **SPF Record** (TXT) - Sender authorization
   - Name: `mail.{domain}`
   - Value: `v=spf1 include:amazonses.com -all`

5. **DMARC Record** (TXT) - Policy for failed authentication
   - Name: `_dmarc.{domain}`
   - Value: `v=DMARC1; p=reject; rua=mailto:dmarc@{ses_domain}`

### Get Domain

Returns domain details with current verification status for each DNS record.

**Response includes:**
- Domain metadata
- Current status
- Array of records with individual status (VALID, MISSING, or INVALID)

### Verify Domain

Triggers a verification check and attempts to complete DKIM signing setup.

**Behavior:**
1. For BYODKIM: Uploads private key to SES
2. Configures MAIL FROM domain
3. Returns 204 on success

### Update Domain

Updates domain settings.

**Updateable Fields:**
- `feedback_enabled` - Toggle bounce/complaint forwarding

### Delete Domain

Removes a domain and associated SES identity.

**Behavior:**
1. Deletes SES email identity
2. For BYODKIM: Deletes private key from Secrets Manager
3. Decrements organization's domain_count
4. Returns 204 on success

---

## Webhooks

### Description

Webhooks deliver real-time HTTP notifications when events occur. They are powered by Svix and support filtering by event type, inbox, or pod.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| organization_id | UUID | Parent organization |
| webhook_id | String | Unique identifier |
| client_id | String (optional) | Idempotency key |
| url | URL | HTTPS endpoint to receive events |
| event_types | String[] | Types of events to receive |
| inbox_ids | String[] (optional) | Filter to specific inboxes |
| pod_ids | String[] (optional) | Filter to specific pods |
| secret | String | Signing secret for verification |
| enabled | Boolean | Whether webhook is active |
| updated_at | ISO DateTime | Last update timestamp |
| created_at | ISO DateTime | Creation timestamp |

### Event Types

| Event Type | Description |
|------------|-------------|
| `message.received` | New email received |
| `message.sent` | Email sent (accepted by SES) |
| `message.delivered` | Email delivered to recipient's server |
| `message.bounced` | Email bounced (hard or soft) |
| `message.complained` | Recipient marked email as spam |
| `message.rejected` | Email rejected by SES |
| `domain.verified` | Domain verification completed |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks` | Create a webhook |
| GET | `/webhooks` | List all webhooks |
| GET | `/webhooks/{webhook_id}` | Get webhook details |
| DELETE | `/webhooks/{webhook_id}` | Delete a webhook |

### Create Webhook

Creates a new webhook endpoint.

**Required Parameters:**
- `url` - HTTPS URL to receive events
- `event_types` - Array of event types to subscribe to

**Optional Parameters:**
- `client_id` - Idempotency key
- `inbox_ids` - Limit to events from specific inboxes
- `pod_ids` - Limit to events from specific pods

**Response includes:**
- Webhook metadata
- `secret` - Use this to verify webhook signatures

### Webhook Payload Structure

All webhook payloads include:

- `type` - Always "event"
- `event_type` - The specific event type
- `event_id` - Unique event identifier

**message.received payload:**
- `receipt.organization_id`, `pod_id`, `inbox_id`, `thread_id`, `message_id`
- `receipt.timestamp`
- `receipt.contact_id` - Sender email address

**message.sent payload:**
- `send.organization_id`, `pod_id`, `inbox_id`, `thread_id`, `message_id`
- `send.timestamp`
- `send.recipients` - Array of recipient addresses

**message.delivered payload:**
- `delivery.organization_id`, `pod_id`, `inbox_id`, `thread_id`, `message_id`
- `delivery.timestamp`
- `delivery.recipients` - Array of delivered addresses

**message.bounced payload:**
- `bounce.organization_id`, `pod_id`, `inbox_id`, `thread_id`, `message_id`
- `bounce.timestamp`
- `bounce.type` - "Permanent" or "Transient"
- `bounce.sub_type` - Specific bounce reason
- `bounce.recipients` - Array with address and status

**message.complained payload:**
- `complaint.organization_id`, `pod_id`, `inbox_id`, `thread_id`, `message_id`
- `complaint.timestamp`
- `complaint.recipients` - Addresses that complained

### Webhook Verification

Webhooks are signed using the secret. Recipients should verify signatures to ensure authenticity. The signing follows Svix's standard webhook signature format.

---

## WebSockets

### Description

WebSocket connections enable real-time streaming of events without polling. Clients connect, authenticate, subscribe to specific resources, and receive events as they occur.

### Connection Flow

1. **Connect** - Establish WebSocket connection with authentication
2. **Subscribe** - Subscribe to organization, pods, or inboxes
3. **Receive** - Receive real-time events
4. **Unsubscribe** - Remove subscriptions
5. **Disconnect** - Close connection

### Endpoints

| Action | Route Key | Description |
|--------|-----------|-------------|
| Connect | `$connect` | Establish authenticated connection |
| Disconnect | `$disconnect` | Handle disconnection |
| Subscribe | `subscribe` | Subscribe to resources |
| Unsubscribe | `unsubscribe` | Remove subscriptions |

### Subscribe Message

Send after connecting to start receiving events:

**Parameters:**
- `inbox_ids` - Array of inbox IDs to subscribe to (optional)
- `pod_ids` - Array of pod IDs to subscribe to (optional)
- `event_types` - Filter to specific event types (optional)

**Behavior:**
- If neither inbox_ids nor pod_ids specified, subscribes to entire organization
- Can subscribe to multiple inboxes/pods
- Event types filter which events are delivered

### Event Messages

Events delivered via WebSocket have the same structure as webhook payloads:

- `type` - "event"
- `event_type` - The specific event
- `event_id` - Unique identifier
- Event-specific data

### Connection Management

- Connections have a TTL for automatic cleanup
- Connection state stored in DynamoDB
- Messages sent via API Gateway Management API
- Multiple regions supported with regional endpoints

---

## Metrics

### Description

Metrics provide analytics data about email events within a time range. They track when messages were sent, delivered, bounced, etc.

### Available Metrics

| Metric | Description |
|--------|-------------|
| message.sent | Emails sent |
| message.delivered | Emails delivered |
| message.delayed | Emails delayed |
| message.bounced | Emails bounced |
| message.complained | Spam complaints |
| message.rejected | Emails rejected |
| message.received | Emails received |

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Get organization-wide metrics |
| GET | `/inboxes/{inbox_id}/metrics` | Get inbox-specific metrics |

### Query Parameters

- `event_types` - Comma-separated list of metrics to retrieve (default: all)
- `start_timestamp` - Start of time range (required)
- `end_timestamp` - End of time range (required)

### Response Format

Metrics are grouped by object type and event type:

```
{
  "message": {
    "sent": ["2024-01-15T10:00:00Z", "2024-01-15T11:00:00Z", ...],
    "delivered": ["2024-01-15T10:00:05Z", ...],
    "bounced": []
  }
}
```

Each array contains timestamps of when events occurred.

---

## Error Handling

### Error Response Format

All errors return JSON with:
- `name` - Error type identifier
- `message` - Human-readable description

Validation errors include:
- `name` - "ValidationError"
- `errors` - Array of Zod validation issues with paths

### Error Types and HTTP Status Codes

| Error Type | Status Code | Description |
|------------|-------------|-------------|
| ValidationError | 400 | Request validation failed |
| SyntaxError | 400 | Malformed JSON body |
| AlreadyExistsError | 403 | Resource already exists |
| IsTakenError | 403 | Resource name/ID is taken by another org |
| LimitExceededError | 403 | Resource limit reached |
| DomainNotVerifiedError | 403 | Domain not verified for sending |
| MessageRejectedError | 403 | Email rejected (various reasons) |
| NotFoundError | 404 | Resource not found |
| RaceConditionError | 409 | Concurrent modification conflict |
| CannotDeleteError | 409 | Delete not allowed (has dependencies) |
| RateLimitError | 429 | Too many requests |
| ServerError | 500 | Unexpected server error |

### Common Error Scenarios

**ValidationError (400)**
- Invalid email format
- Missing required fields
- Invalid UUID format
- Invalid page_token

**AlreadyExistsError (403)**
- Creating inbox with email that already exists in same org
- Creating domain that already exists in same org

**IsTakenError (403)**
- Creating inbox with email that exists in different org
- Creating domain that exists in different org

**LimitExceededError (403)**
- Creating inbox when inbox_count >= inbox_limit
- Creating domain when domain_count >= domain_limit

**DomainNotVerifiedError (403)**
- Sending from inbox on unverified domain
- Creating inbox on unverified domain

**MessageRejectedError (403)**
- Sending to previously bounced address
- Sending to address that filed complaint
- Playground sending to non-received address
- SES rejection for policy violations

**NotFoundError (404)**
- Resource doesn't exist
- Resource exists but belongs to different organization

**RaceConditionError (409)**
- Concurrent updates to same resource
- Client ID collision

**CannotDeleteError (409)**
- Deleting default pod
- Deleting pod with existing inboxes

**RateLimitError (429)**
- DynamoDB provisioned throughput exceeded
- Too many API requests

---

## Common Patterns

### Pagination

List endpoints support cursor-based pagination.

**Request Parameters:**
- `limit` - Maximum items to return (positive integer)
- `page_token` - Opaque token from previous response

**Response Fields:**
- `count` - Number of items in current page
- `limit` - Limit used for this request
- `next_page_token` - Token for next page (null if no more pages)
- Resource array (e.g., `threads`, `messages`, `inboxes`)

**Token Format:** Base64url-encoded JSON of DynamoDB LastEvaluatedKey

### Filtering

List endpoints support various filters:

**Time Range:**
- `before` - ISO datetime, exclusive upper bound
- `after` - ISO datetime, inclusive lower bound
- Both can be combined: `after <= timestamp < before`

**Labels:**
- `labels` - Comma-separated list
- All specified labels must be present (AND logic)

**Sorting:**
- `ascending` - Boolean, defaults to false (newest first)

**Spam:**
- `include_spam` - Boolean, defaults to false

### Client ID (Idempotency)

Many create operations support `client_id` for idempotency:

**Behavior:**
1. If client_id provided, check if resource with that client_id exists
2. If exists, return existing resource (no new creation)
3. If not exists, create new resource and store client_id mapping

**Supported Resources:**
- Pods
- Inboxes
- Domains
- Drafts
- Webhooks

**Format Requirements:**
- Must match: `[A-Za-z0-9._~-]+`
- No spaces or special characters except `.`, `_`, `~`, `-`

### Async Deletion

Resource deletion is asynchronous for complex resources:

**Flow:**
1. Request returns 202 Accepted immediately
2. Resource marked with `delete_status: 'deleting'`
3. Background job deletes child resources
4. Parent resource deleted after children cleared

**Affected Resources:**
- Inboxes (deletes threads, messages, drafts)
- Threads (deletes messages)
- Messages

---

## Rate Limiting

### DynamoDB Throughput

The API uses DynamoDB with provisioned capacity (auto-scaling between 16-256 units). When throughput is exceeded, requests receive 429 errors.

**Behavior:**
- `ProvisionedThroughputExceededException` is caught
- Returns `RateLimitError` with 429 status
- Client should implement exponential backoff

### API Gateway

API Gateway has default rate limits. Excessive requests may be throttled at the gateway level before reaching Lambda handlers.

### Lambda Warming

Production environments use scheduled warming to keep Lambdas warm and reduce cold start latency.

---

## Validation Rules

### Email Addresses

- Must be valid email format per RFC 5322
- Automatically lowercased
- Can include display name: `"Name" <email@example.com>`

### Domain Names

- Must match pattern: `^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$`
- Cannot be empty
- Labels cannot start or end with hyphens
- Automatically lowercased

### Usernames (Inbox Local Part)

- Must be valid as the local part of an email
- Cannot be empty if provided
- Automatically lowercased

### Client IDs

- Must match: `^[A-Za-z0-9._~-]+$`
- URL-safe characters only

### UUIDs

- Standard UUID format (8-4-4-4-12 hexadecimal)

### Timestamps

- ISO 8601 datetime format
- Example: `2024-01-15T10:30:00Z`

### URLs (Webhooks)

- Must be HTTPS protocol
- Normalized before storage

### Labels

- Automatically lowercased
- No restrictions on characters

### HTML Content

- Automatically sanitized when received
- Dangerous elements/attributes removed

### Display Names

- Leading/trailing whitespace trimmed
- Special characters sanitized

### Attachments

- `content` must be valid Base64
- `content_type` auto-detected from filename if not provided
- `content_id` automatically wrapped in angle brackets if missing

---

## Resource Relationships

### Hierarchy

```
Organization
├── API Keys
├── Webhooks
├── Domains (optional pod restriction)
└── Pods
    ├── Domains (pod-specific)
    └── Inboxes
        ├── Drafts
        └── Threads
            └── Messages
                └── Attachments
```

### Key Relationships

**Organization → Pods:**
- Every organization has a default pod (pod_id = organization_id)
- Additional pods can be created for multi-tenant isolation

**Pod → Inboxes:**
- Inboxes are always created within a pod
- Default pod is used if not specified

**Inbox → Threads:**
- Threads are created when first message received/sent
- Thread belongs to single inbox

**Thread → Messages:**
- Messages grouped by In-Reply-To and References headers
- Thread aggregates data from all messages

**Message → Attachments:**
- Attachments stored separately in S3
- Referenced by attachment_id

**Domain → Inbox:**
- Custom domains can be used for inbox creation
- Domain must be verified before use
- Pod-restricted domains can only be used in that pod

**Webhook/Connection → Events:**
- Can filter by inbox_ids or pod_ids
- Can filter by event_types
- If no filter, receives all organization events

### Authorization Model

All resources are scoped to an organization:
- API requests authenticated to an organization
- Can only access resources owned by that organization
- Attempting to access other org's resources returns 404 (not 403, for security)

---

## Contact Tracking

### Description

The system tracks contacts (external email addresses) for analytics and protection:

### Tracked Events

| Event | Counter | Timestamp |
|-------|---------|-----------|
| Email received from | received_count | received_at |
| Email delivered to | delivered_count | delivered_at |
| Bounce from address | bounced_count | bounced_at |
| Complaint from address | complained_count | complained_at |

### Sending Restrictions

Before sending, the system checks recipient contacts:
- If `bounced_at` is set → MessageRejectedError
- If `complained_at` is set → MessageRejectedError

### Playground Restrictions

Playground organizations have additional restrictions:
- Can only send to addresses that have previously emailed them
- Exception: Can always send to other @agentmail.me addresses

---

## Incoming Email Processing

### Receipt Flow

1. Email arrives via SES
2. Security checks performed (virus, SPF, DKIM, DMARC)
3. Failed checks → message dropped
4. Spam check → adds "spam" label if failed
5. Look up recipient inboxes
6. Parse email content and headers
7. Store raw message in S3
8. Upload body and attachments
9. Create/update thread
10. Create message record
11. Trigger webhook and WebSocket events

### Security Checks

| Check | Action on FAIL |
|-------|----------------|
| Virus | Drop message entirely |
| SPF | Drop message entirely |
| DKIM | Drop message entirely |
| DMARC | Drop if policy is not "none" |
| Spam | Add "spam" label, continue processing |

### Header Handling

Custom headers from senders are extracted and stored. Standard email provider headers (SES, Gmail, Outlook, ProtonMail) are filtered out to reduce noise.

---

## Outgoing Email Processing

### Send Flow

1. Validate recipients against contact restrictions
2. Check domain verification status
3. Build email message with Nodemailer
4. Send via SES
5. Store raw message in S3
6. Upload body and attachments
7. Create message record
8. Create/update thread
9. SES triggers SNS notifications for tracking events

### Event Tracking

SES sends notifications to SNS topics for:
- **Send** - Email accepted by SES
- **Delivery** - Email delivered to recipient MTA
- **Bounce** - Delivery failed
- **Complaint** - Recipient marked as spam
- **Delay** - Delivery temporarily delayed
- **Reject** - Email rejected by SES

Each event:
1. Updates contact counters
2. Stores event in tracking table
3. Sends webhook notification
4. Sends WebSocket event
