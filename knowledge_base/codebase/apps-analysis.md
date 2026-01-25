# AgentMail Console Application Documentation

This document provides a comprehensive overview of the AgentMail Console application, its features, navigation structure, and user workflows. This documentation is intended to help users navigate and understand the product.

---

## Table of Contents

1. [Overview](#overview)
2. [Navigation Structure](#navigation-structure)
3. [Console Features](#console-features)
   - [Inboxes](#inboxes)
   - [Domains](#domains)
   - [Webhooks](#webhooks)
   - [API Keys](#api-keys)
   - [Metrics](#metrics)
   - [Pods](#pods)
4. [Key Workflows](#key-workflows)
   - [Creating an Inbox](#creating-an-inbox)
   - [Setting Up a Custom Domain](#setting-up-a-custom-domain)
   - [Configuring Webhooks](#configuring-webhooks)
   - [Managing API Keys](#managing-api-keys)
   - [Viewing Metrics](#viewing-metrics)
   - [Using Pods for Multi-Tenancy](#using-pods-for-multi-tenancy)
   - [Sending and Receiving Emails](#sending-and-receiving-emails)
5. [Shared Components](#shared-components)
6. [Data Loaders](#data-loaders)
7. [Key Data Types](#key-data-types)
8. [UI Patterns](#ui-patterns)
9. [User Journeys](#user-journeys)
10. [Additional Features](#additional-features)
    - [Onboarding Flow](#onboarding-flow)
    - [SMTP/IMAP Credentials Export](#smtpimap-credentials-export)
    - [Billing & Pricing](#billing--pricing)
    - [Authentication & Organizations](#authentication--organizations)
    - [Organization Limits](#organization-limits)
    - [Theme Support](#theme-support)
11. [Technical Details](#technical-details)
12. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Overview

The AgentMail Console is a web-based dashboard for managing email infrastructure. It allows users to:

- Create and manage email inboxes
- Register and verify custom domains
- Configure webhooks for real-time event notifications
- Generate and manage API keys for programmatic access
- View email metrics and analytics
- Organize resources using Pods (isolated workspaces)
- Send and receive emails through a web interface

The console is built as a Remix application using React and TypeScript, with a modern UI powered by Tailwind CSS and shadcn/ui components.

---

## Navigation Structure

### Main Sidebar

The console features a collapsible sidebar with the following main sections:

**Resources Section:**
- **Inboxes** - Manage email inboxes and view email threads
- **Domains** - Register and verify custom domains
- **Webhooks** - Configure webhook endpoints for event notifications
- **API Keys** - Manage API keys for programmatic access
- **Metrics** - View email analytics and statistics
- **Pods** - Organize resources into isolated workspaces

**Platform Section:**
- **Documentation** - Link to external documentation at docs.agentmail.to

**Support Section:**
- **Feedback** - Email link for sending feedback to support

**User Section:**
- Organization switcher in the header
- User profile dropdown in the footer

### URL Structure

The console uses the following URL pattern:
- `/dashboard` - Main dashboard home
- `/dashboard/inboxes` - Inbox list view
- `/dashboard/inboxes/{inboxId}` - Specific inbox with threads
- `/dashboard/inboxes/{inboxId}/inbox` - Inbox received emails view
- `/dashboard/inboxes/{inboxId}/sent` - Sent emails view
- `/dashboard/inboxes/{inboxId}/drafts` - Drafts view
- `/dashboard/inboxes/{inboxId}/compose` - Compose new email
- `/dashboard/domains` - Domain list view
- `/dashboard/domains/{domainId}` - Domain details and DNS records
- `/dashboard/webhooks` - Webhook management
- `/dashboard/api-keys` - API key management
- `/dashboard/metrics` - Metrics dashboard
- `/dashboard/pods` - Pod list view
- `/dashboard/pods/{podId}` - Pod details with associated inboxes

---

## Console Features

### Inboxes

The Inboxes section allows users to create and manage email addresses (inboxes).

**Key Features:**
- View a table of all inboxes with ID, display name, creation date, and last updated date
- Create new inboxes with a username, domain selection, and display name
- Delete inboxes individually or in bulk
- Update inbox display names
- Navigate to inbox details to view email threads

**Inbox Detail View:**
- View received emails (inbox view)
- View sent emails
- View drafts
- Compose new emails
- View spam folder
- Custom view for filtered threads

**Table Features:**
- Sortable columns
- Pagination with configurable page size (5, 10, 20, 30, 50 rows)
- Column visibility toggle
- Row selection for bulk operations
- Clickable rows to navigate to inbox details

### Domains

The Domains section allows users to register and verify custom domains for sending emails.

**Key Features:**
- View all registered domains with verification status
- Add new custom domains
- View DNS records required for verification
- Verify domain ownership
- Delete domains individually or in bulk
- Feedback forwarding toggle (enabled by default)

**Domain Status Indicators:**
- **Verified/Valid** - Domain is fully verified and ready to use (green)
- **Verifying** - Verification in progress (blue)
- **Pending/Not Started** - Awaiting DNS configuration (yellow)
- **Failed/Invalid** - Verification failed, DNS records incorrect (red)

**DNS Record Types:**
- TXT records (for SPF/DKIM verification)
- CNAME records
- MX records (with priority)

**Features:**
- Copy individual DNS record values
- Download BIND zone file for bulk import
- Manual verification trigger with rate limiting (5-minute cooldown)
- Status indicators for individual records

### Webhooks

The Webhooks section allows users to configure HTTP endpoints to receive real-time event notifications.

**Key Features:**
- View all configured webhooks with URL, events, and status
- Create new webhooks with endpoint URL and event selection
- Copy webhook ID, URL, and secret
- Delete webhooks individually or in bulk

**Available Event Types:**
- `message.received` - Triggered when a new message is received in an inbox
- `message.sent` - Triggered when a message is sent
- `message.delivered` - Triggered when a message is successfully delivered
- `message.bounced` - Triggered when a message bounces back
- `message.complained` - Triggered when a recipient marks message as spam
- `message.rejected` - Triggered when a message is rejected

**Webhook Configuration:**
- Endpoint URL (required, must be HTTPS)
- Event types to subscribe to (at least one required)
- Inbox IDs filter (optional, defaults to all inboxes)
- Client ID for idempotency (optional)
- Auto-generated secret for signature verification

### API Keys

The API Keys section allows users to generate and manage API keys for programmatic access.

**Key Features:**
- View all API keys with name, prefix, last used date, and creation date
- Create new API keys with a display name
- Delete API keys individually or in bulk
- API key prefix shown (full key only displayed once at creation)

**Table Columns:**
- Name/Display Name
- API Key (prefix with masked remainder)
- Last Used timestamp
- Created timestamp
- Actions menu

### Metrics

The Metrics Dashboard provides comprehensive email analytics and statistics.

**Overview Tab:**
- Title cards showing key metrics (total sent, delivered, bounced, etc.)
- Interactive area chart showing email volume over time
- Pie chart showing email status distribution

**Detailed Graphs Tab:**
- Line chart for failure events over time
- Bounce rate chart
- Complaint rate chart
- Reject rate chart
- Weekly/hourly delivery stacked chart
- Weekly/hourly sends chart
- Weekly/hourly delivery rate chart

**Controls:**
- Time range selector (24 hours or 7 days)
- Timezone selector (auto-detects user timezone)

### Pods

Pods provide isolated workspaces for organizing email infrastructure, particularly useful for multi-tenant applications.

**Key Features:**
- View pods in a grid layout with name, client ID, and creation date
- Create new pods with a name and optional client ID
- View pod-specific inboxes
- Unified view of all threads across pod inboxes
- Delete pods (with guard for pods containing inboxes)

**Pod Card Actions:**
- View Details - Navigate to pod detail page
- View Inboxes - See inboxes associated with the pod
- Unified View - View all threads across pod inboxes
- Delete Pod - Remove the pod (blocked if it contains inboxes)

**Pagination:**
- Configurable items per page (6, 9, or 12)
- Load more pods on demand
- First/previous/next/last page navigation

---

## Key Workflows

### Creating an Inbox

1. Navigate to **Inboxes** from the sidebar
2. Click the **Create Inbox** button
3. Fill in the create inbox form:
   - **Username** (optional) - The local part of the email address. If left blank, a random username will be auto-generated
   - **Domain** - Select from `agentmail.to` (default) or any verified custom domains
   - **Display Name** (optional) - A friendly name for the inbox (e.g., "Marketing Team")
4. Click **Create Inbox**
5. Upon success, you'll be redirected to the new inbox view

**Notes:**
- To use a custom domain, you must first register and verify it in the Domains section
- The resulting email address will be `username@domain`

### Setting Up a Custom Domain

1. Navigate to **Domains** from the sidebar
2. Click the **Add Domain** button
3. Enter your domain name (e.g., `yourdomain.com`)
4. Click **Create Domain**
5. You'll see a table of DNS records that need to be added to your DNS provider
6. For each record, copy the **Name** and **Value** and add them to your DNS provider:
   - TXT records for SPF/DKIM verification
   - CNAME records for email routing
   - MX records for mail delivery
7. After adding all records, click **Verify Domain**
8. Wait for verification (may take a few minutes to several hours depending on DNS propagation)
9. Once all records show "Verified" status and the overall domain status is "Verified", you can use the domain for inboxes

**Tips:**
- Download the zone file for bulk import (if your DNS provider supports it)
- Some providers like Namecheap require manual record entry
- Verification can be re-triggered after a 5-minute cooldown
- Refer to the DNS configuration guide in the documentation for provider-specific instructions

### Configuring Webhooks

1. Navigate to **Webhooks** from the sidebar
2. Click the **Create Webhook** button
3. Configure the webhook:
   - **Endpoint URL** (required) - Your publicly accessible HTTPS endpoint that will receive webhook events
   - **Events** (required) - Select at least one event type to subscribe to:
     - Message Received
     - Message Sent
     - Message Delivered
     - Message Bounced
     - Message Complained
     - Message Rejected
   - **Inbox IDs** (optional) - Comma-separated list of inbox IDs to filter events. Leave empty for all inboxes
   - **Client ID** (optional) - Your own identifier for idempotency
4. Click **Create Webhook**
5. **Important:** Copy and securely store the webhook secret shown after creation - it won't be shown again
6. Use the secret to verify webhook signatures in your endpoint

**Webhook Security:**
- All webhooks include a signature for verification
- Your endpoint must respond with a 2xx status code
- The endpoint must be publicly accessible

### Managing API Keys

1. Navigate to **API Keys** from the sidebar
2. To create a new key:
   - Click **Create API Key**
   - Enter a display name for the key
   - Click **Create**
   - **Important:** Copy the full API key immediately - it will only be shown once
3. To delete a key:
   - Click the actions menu (three dots) on the key row
   - Select **Delete**
   - Confirm the deletion

**Warning:** Deleting an API key will immediately revoke access for any applications using that key.

### Viewing Metrics

1. Navigate to **Metrics** from the sidebar
2. The **Overview** tab shows:
   - Summary cards with total counts
   - Email volume trends over time
   - Email status distribution
3. Switch to **Detailed Graphs** for:
   - Failure event analysis
   - Bounce, complaint, and reject rates
   - Sending patterns and delivery rates
4. Use the **Time Range** selector to view 24-hour or 7-day data
5. Adjust the **Timezone** to match your preferred time zone

### Using Pods for Multi-Tenancy

Pods are ideal for SaaS applications that need to separate email infrastructure per customer.

1. Navigate to **Pods** from the sidebar
2. Click **Create Pod**
3. Enter:
   - **Name** - A descriptive name for the pod (e.g., "Customer ABC")
   - **Client ID** (optional) - Your internal identifier for the customer
4. Click **Create**
5. Within a pod, you can:
   - Create inboxes that are isolated to that pod
   - View all pod inboxes in one place
   - Use the **Unified View** to see all threads across the pod's inboxes

**Use Cases:**
- Separate email infrastructure per customer in a multi-tenant SaaS
- Organize inboxes by department or project
- Maintain isolation between different environments or clients

### Sending and Receiving Emails

**Viewing Received Emails:**
1. Navigate to an inbox (via Inboxes → click on an inbox)
2. The **Inbox** view shows all received threads
3. Click on a thread to view all messages in the conversation
4. Each message shows sender, recipients (To, Cc, Bcc), timestamp, and content

**Viewing Sent Emails:**
1. Navigate to an inbox
2. Click on the **Sent** tab
3. View all sent email threads

**Composing a New Email:**
1. Navigate to an inbox
2. Click the **Compose** button
3. Fill in:
   - **To** (required) - Recipient email address
   - **Cc** (optional) - Carbon copy recipients
   - **Bcc** (optional) - Blind carbon copy recipients
   - **Subject** - Email subject line
   - **Body** - Email content (rich text editor)
4. Click **Send**

**Replying to an Email:**
1. Open a thread
2. Click the **Reply** button on any message
3. The compose form will pre-fill the recipient and subject
4. Add your reply content
5. Click **Send**

**Drafts:**
1. Navigate to an inbox
2. Click the **Drafts** tab to view saved drafts
3. Click on a draft to continue editing

---

## Shared Components

The console uses a library of shared components located in the `shared/` directory. These components are designed to be reusable across the console and potentially other AgentMail applications.

### Email Components
- **Compose** - Email composition form with rich text editor, To/Cc/Bcc fields, subject, and send button
- **Thread** - Display of a complete email thread with all messages, labels, and metadata
- **ThreadList** - Scrollable list of email threads with infinite scroll loading
- **ThreadItem** - Individual thread preview in the list (subject, preview, sender, timestamp)
- **Message** - Single email message display with sender info, recipients, timestamp, and body
- **CollapsibleQuote** - Expandable/collapsible quoted text in emails

### Form Components
- **ComposeBase** - Base form layout for email composition
- **InlineCompose** - Compact inline compose form
- **LabeledInput** - Input field with associated label

### UI Components (shadcn/ui based)
- **Button** - Primary button component with variants (default, outline, ghost, destructive)
- **Card** - Container component with header, content, and footer sections
- **Dialog** - Modal dialog for forms and confirmations
- **AlertDialog** - Confirmation dialogs for destructive actions
- **Table** - Data table with sortable columns and selection
- **Select** - Dropdown select menus
- **Input** - Text input fields
- **Textarea** - Multi-line text input
- **Checkbox** - Checkbox inputs for selection
- **Badge** - Status and category badges
- **Tabs** - Tabbed navigation
- **ScrollArea** - Custom scrollable containers
- **Tooltip** - Hover tooltips for additional information
- **DropdownMenu** - Context menus and action menus
- **Skeleton** - Loading placeholder components
- **Label** - Form field labels

### Navigation Components
- **MenuBar** - Top action bar with navigation and actions
- **NavBar** - Main navigation sidebar
- **NavArrows** - Previous/Next navigation for threads

### Utility Components
- **ErrorBoundary** - Error handling wrapper
- **Dropdown** - Generic dropdown container
- **DropdownDelete** - Delete confirmation dropdown

---

## Data Loaders

The console uses Remix loaders to fetch data from the AgentMail API. These loaders are implemented as factory functions that create environment-configured loaders.

### Available Loaders

**Inbox Loaders:**
- `createListInboxesLoader` - Fetches paginated list of inboxes
- `createListReceivedThreadsLoader` - Fetches received email threads for an inbox
- `createListSentThreadsLoader` - Fetches sent email threads
- `createListSpamThreadsLoader` - Fetches spam threads
- `createListDraftsLoader` - Fetches draft messages
- `createGetThreadLoader` - Fetches a single thread with all messages

**Domain Loaders:**
- `createListDomainsLoader` - Fetches list of registered domains
- `createGetDomainLoader` - Fetches domain details with DNS records

**Other Loaders:**
- `createListWebhooksLoader` - Fetches list of webhooks
- `createListMetricsLoader` - Fetches email metrics data
- `createGetComposeDataLoader` - Fetches data needed for email composition
- `createGetAuthStatusLoader` - Checks authentication status
- `createGetAttachmentLoader` - Fetches email attachments
- `createGetClientApiKeyLoader` - Fetches API key for client-side use
- `createListCustomViewDataLoader` - Fetches custom filtered thread views

### Loader Features
- Pagination support with `limit` and `pageToken` parameters
- Client-side loaders for faster navigation
- Automatic revalidation on data changes
- Error handling with proper HTTP status codes

---

## Key Data Types

### Inbox
- `inboxId` - Unique identifier (email address format)
- `displayName` - Friendly display name
- `createdAt` - Creation timestamp
- `updatedAt` - Last update timestamp
- `organizationId` - Parent organization
- `podId` - Associated pod (if any)
- `isPlayground` - Whether it's a playground inbox

### Thread (ThreadItem)
- `threadId` - Unique thread identifier
- `inboxId` - Parent inbox
- `subject` - Email subject
- `preview` - Short preview text
- `senders` - List of sender addresses
- `recipients` - List of recipient addresses
- `labels` - Applied labels (e.g., "positive", "negative")
- `messageCount` - Number of messages in thread
- `timestamp` - Last activity timestamp
- `attachments` - List of attachments

### Message
- `messageId` - Unique message identifier
- `inboxId` - Parent inbox
- `threadId` - Parent thread
- `from` - Sender address
- `to` - Recipients
- `cc` - CC recipients
- `bcc` - BCC recipients
- `subject` - Subject line
- `text` - Plain text body
- `html` - HTML body
- `timestamp` - Send/receive timestamp
- `attachments` - Message attachments

### Domain
- `domainId` - Domain name (e.g., "example.com")
- `feedbackEnabled` - Whether feedback forwarding is enabled
- `records` - List of DNS records to configure
- `status` - Verification status (VERIFIED, PENDING, FAILED, etc.)
- `createdAt` - Creation timestamp
- `updatedAt` - Last update timestamp

### Webhook
- `webhookId` - Unique identifier
- `url` - Endpoint URL
- `eventTypes` - List of subscribed events
- `inboxIds` - Filtered inbox IDs (optional)
- `secret` - Signing secret
- `createdAt` - Creation timestamp
- `updatedAt` - Last update timestamp

### API Key
- `api_key_id` - Unique identifier
- `name` - Internal name
- `display_name` - User-friendly name
- `prefix` - Key prefix for identification
- `hash` - Hashed key value
- `is_playground` - Playground mode flag
- `created_at` - Creation timestamp
- `used_at` - Last usage timestamp

### Pod
- `podId` - Unique identifier
- `name` - Pod name
- `clientId` - Optional client-side identifier
- `createdAt` - Creation timestamp

---

## UI Patterns

### Table Pattern
All resource tables (Inboxes, Domains, Webhooks, API Keys) follow a consistent pattern:
- Header with resource count and create button
- Column visibility toggle
- Sortable columns
- Row selection for bulk operations
- Bulk delete controls appearing when items selected
- Pagination controls (first, previous, next, last, page size)
- Loading skeletons during data fetch
- Empty state with call-to-action

### Dialog Pattern
Create and edit dialogs follow a two-column layout:
- Left column: Form inputs
- Right column: Info cards with requirements and examples
- Error display below form
- Success state with next steps or confirmation

### Status Indicators
Consistent status visualization:
- Green: Verified, Valid, Success
- Blue: Verifying, In Progress
- Yellow: Pending, Not Started
- Red: Failed, Invalid, Error
- Pulsing animation for in-progress states

### Copy to Clipboard
One-click copy buttons for:
- Email addresses
- Inbox IDs
- Domain names
- DNS record values
- Webhook IDs, URLs, and secrets
- API key prefixes

### Loading States
- Skeleton loaders matching content structure
- Loading spinners on buttons during submission
- "Loading more..." indicators for pagination

### Error Handling
- Inline error messages below form fields
- Error cards with heading and description
- Retry buttons for failed operations
- Error boundaries for graceful degradation

---

## User Journeys

### New User Onboarding

1. **Sign up** - Create account and organization
2. **First Inbox** - Create your first inbox using the default agentmail.to domain
3. **Test Email** - Send a test email to verify the inbox works
4. **API Integration** - Create an API key to integrate with your application
5. **Custom Domain** (optional) - Register and verify your own domain
6. **Webhook Setup** (optional) - Configure webhooks for real-time notifications

### Developer Integration Journey

1. **Create API Key** - Generate credentials for your application
2. **Create Inbox** - Set up an inbox for your agent
3. **Configure Webhook** - Set up event notifications for incoming emails
4. **Test Integration** - Send and receive test emails via API
5. **Monitor Metrics** - Track email delivery and engagement

### Multi-Tenant SaaS Journey

1. **Create Pod** - Set up isolated workspace for each customer
2. **Create Customer Inbox** - Create inboxes within the pod
3. **Configure Webhooks** - Set up webhooks filtered to pod inboxes
4. **Monitor by Pod** - Use unified view to monitor all customer emails
5. **Scale** - Add more pods and inboxes as needed

### Email Campaign Monitoring Journey

1. **Review Metrics** - Check overview dashboard for delivery rates
2. **Analyze Issues** - Use detailed graphs to identify bounce/complaint patterns
3. **Check Domain Health** - Verify domain DNS records are properly configured
4. **Optimize Sending** - Use time-based analysis to optimize send times

---

## Additional Features

### Onboarding Flow

New users are guided through an interactive onboarding experience powered by Intro.js:

**Phase 1: Welcome & Create Inbox**
1. Welcome modal introducing AgentMail
2. Highlight on "Create Inbox" button with instructions

**Phase 2: Try It Out**
1. After creating first inbox, user is guided to send a test email
2. The inbox address is displayed for easy copying
3. User is prompted to send an email from any email client

**Phase 3: First Email Received**
1. System polls for incoming email
2. When first email arrives, a highlight appears on the thread
3. User is guided to click and view their first email
4. Onboarding completes

**Skip Confirmation:**
- Users can skip the onboarding at any time
- A confirmation modal ensures intentional skipping
- Onboarding state is stored per-organization in localStorage

### SMTP/IMAP Credentials Export

For users who want to integrate AgentMail with cold email platforms (Smartlead, Instantly), the console provides SMTP/IMAP credential export functionality.

**How to Access:**
1. Navigate to Inboxes
2. Click the SMTP/IMAP export option

**Export Process:**
1. Enter your API key (used as the password for SMTP/IMAP auth)
2. View credentials table with all inboxes
3. Select export platform (Smartlead, Instantly, or Generic)
4. Download as CSV for bulk import

**Credential Fields:**
- Email address
- SMTP Host and Port
- IMAP Host and Port
- Password (your API key)

**Note:** API keys are not stored in plaintext - you must enter yours each time for security.

### Billing & Pricing

**Available Plans:**

1. **Free Tier** ($0/month)
   - 3 inboxes
   - 3,000 emails/month
   - 3GB storage
   - Discord support

2. **Developer Tier** (Paid)
   - Increased inbox limits
   - Higher email volume
   - Priority support

3. **Startup Tier** (Paid)
   - Even higher limits
   - Additional features
   - Highlighted as recommended plan

4. **Custom Tier** (Contact sales)
   - Custom volume pricing
   - Dedicated IPs
   - Self-hosted solutions
   - White-label solutions
   - Training & onboarding
   - 24/7 dedicated support

**Checkout Process:**
1. Navigate to Pricing from the dashboard
2. Select a plan (except Free, which is the default)
3. Complete Stripe checkout
4. Return to dashboard with success confirmation (confetti animation!)

**Plan Management:**
- Upgrade or downgrade anytime
- No hidden fees
- Full API access on all plans
- Organization-level billing

### Authentication & Organizations

The console uses Clerk for authentication with organization-based access control:

**Sign Up/Sign In:**
- Email and password authentication
- OAuth providers (Google, GitHub, etc.)
- Email verification

**Organizations:**
- Multi-organization support
- Organization switcher in sidebar header
- Create new organizations
- Switch between organizations seamlessly
- Invite team members

**User Profile:**
- Profile management
- Change password
- Manage connected accounts

### Organization Limits

Organizations have configurable limits based on their plan:
- **Inbox Limit** - Maximum number of inboxes
- **Domain Limit** - Maximum number of custom domains

Current usage is tracked and displayed:
- Inbox count vs limit
- Domain count vs limit

Limits are enforced when creating new resources.

### Theme Support

The console supports light and dark themes:
- Automatic detection of system preference
- Manual theme toggle in user dropdown
- Consistent styling across all components
- Proper contrast ratios for accessibility

---

## Technical Details

### Technology Stack
- **Framework:** Remix (React-based full-stack framework)
- **UI Library:** shadcn/ui components with Tailwind CSS
- **State Management:** Remix loaders and fetchers
- **Authentication:** Clerk
- **Payments:** Stripe
- **API Client:** AgentMail SDK
- **Animations:** GSAP, Framer Motion

### Browser Support
The console is optimized for modern browsers with support for:
- Shadow DOM for isolated email rendering (HTML emails)
- CSS animations for visual feedback
- Intersection Observer for infinite scroll pagination
- Web Storage API for local preferences

### Accessibility
- Keyboard navigation support
- Screen reader compatible
- Proper focus management in dialogs
- High contrast theme support

---

## Troubleshooting Common Issues

### Domain Verification Not Working
1. Ensure all DNS records are added correctly
2. Check for typos in record values
3. Wait for DNS propagation (up to 48 hours in some cases)
4. Verify with external DNS lookup tools
5. Click "Verify Domain" button after records propagate

### Emails Not Arriving
1. Check the inbox view for new threads
2. Verify the sender address is correct
3. Check spam folder
4. Ensure the inbox exists and is active
5. Check webhook logs for delivery issues

### API Key Issues
1. Ensure the API key is copied correctly (full key only shown once)
2. Check if the key has been deleted
3. Verify the key belongs to the correct organization
4. Check "Last Used" timestamp for recent activity

### Webhook Not Triggering
1. Verify webhook URL is accessible (HTTPS required)
2. Check that endpoint returns 2xx status
3. Confirm correct event types are selected
4. Check if inbox filter is restricting events
5. Verify webhook secret for signature validation

---

*This documentation is intended for use by AI support bots and help systems to assist users in navigating the AgentMail Console.*
