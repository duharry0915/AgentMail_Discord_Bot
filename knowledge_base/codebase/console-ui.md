# AgentMail Console UI Guide

This document describes the AgentMail Console web interface at console.agentmail.to, based on actual UI screenshots.

---

## Console Overview

The AgentMail Console is a dark-themed web application for managing email infrastructure. It features:

- **Left Sidebar Navigation**: Contains user profile, Resources section, and Platform section
- **Top Header**: Breadcrumb navigation, search (⌘K), and theme toggle
- **Main Content Area**: Context-specific content for each section

### Navigation Structure

```
AgentMail Console
├── [User Profile: shangran]
├── Resources
│   ├── Inboxes
│   ├── Domains
│   ├── Webhooks
│   ├── API Keys
│   ├── Metrics
│   └── Pods
└── Platform
    └── Documentation
```

---

## 1. Inboxes

### Inboxes List View

**Location**: Dashboard > Inboxes

**Purpose**: Manage all email inboxes in your account

**UI Elements**:
- **Header**: "Inboxes" title with subtitle "Manage your email inboxes • X total"
- **Action Buttons** (top right):
  - `+ Create Inbox` - Opens inbox creation modal
  - `Unified View` - View all inboxes in one interface
  - `SMTP/IMAP` - Access SMTP/IMAP connection settings

**Table Columns**:
| Column | Description |
|--------|-------------|
| Inbox ID | Email address (e.g., `crowdeddamage134@agentmail.to`) |
| Display Name | Human-readable name (e.g., "AgentMail", "Testing White Label Feedback") |
| Created | Creation timestamp |
| Updated | Last update timestamp |
| Actions | Three-dot menu for more options |

**Features**:
- Checkbox selection for bulk operations
- Rows per page selector (10, 25, 50)
- Pagination controls
- Column visibility toggle ("Columns" button)

---

### Create New Inbox Modal

**Purpose**: Create a new email inbox

**Form Fields**:
1. **Username** (optional)
   - Placeholder: "e.g. sales"
   - If not specified, auto-generated random username

2. **Domain** (dropdown)
   - Default: `agentmail.to (Default)`
   - Can select custom verified domains

3. **Display Name** (optional)
   - Placeholder: "e.g. Lead Generation Team"
   - Sets the "From" name in emails

**Configuration Rules Panel** (right side):
- Username will be auto-generated if not specified
- Domain defaults to `agentmail.to`
- To use a custom domain, first register it in the Domains section

**Example Panel**:
```
Input:
  Username: marketing
  Domain: apple.com
  Display: Marketing Team

Output:
  Marketing Team <marketing@apple.com>
```

**Action Button**: `⊕ Create Inbox`

---

### Inbox Detail View (Thread View)

**Location**: Dashboard > Inboxes > [inbox@domain] > Thread

**Purpose**: View and manage emails for a specific inbox

**Tab Navigation**:
| Tab | Purpose |
|-----|---------|
| Inbox | View received emails |
| Sent | View sent emails |
| Drafts | View draft emails |
| Custom View | Create filtered views |
| Spam | View spam emails |
| Compose | Write new email |

**Thread List (Left Panel)**:
- Shows email threads with:
  - Sender name
  - Subject line
  - Preview text
  - Date
  - Status tags: `received`, `unread`, `sent`, `send`
- Rows per page selector
- Page navigation

**Thread Detail (Right Panel)**:
- **Header**:
  - Subject line
  - Last activity timestamp
  - Message count
  - Participants list
  - Status badges: `Received`, `Unread`

- **Message Display**:
  - Sender name and email
  - Recipient (To:)
  - Timestamp with relative time ("2 months ago")
  - Reply and forward buttons
  - Message body
  - Attachments section with:
    - File icon
    - File name
    - File size (e.g., "970 KB")

---

## 2. Domains

### Domains List View

**Location**: Dashboard > Domains

**Purpose**: Manage custom domains for sending/receiving emails

**Header**: "Domains" with subtitle "X domain configured"

**Action Button**: `+ Add Domain`

**Table Columns**:
| Column | Description |
|--------|-------------|
| Domain | Domain name (e.g., `harrydu.dev`) |
| Feedback Forwarding | Status badge (`Enabled` / `Disabled`) |
| Created | Creation timestamp |
| Updated | Last update timestamp |
| Actions | Three-dot menu |

---

### Domain DNS Configuration Modal

**Purpose**: Configure DNS records for domain verification

**Header Section**:
- Domain name (e.g., `harrydu.dev`)
- Subtitle: "DNS Records Configuration"
- **Overall Status**: Badge showing `Verifying`, `Verified`, or `Failed`

**DNS Records Table**:
| Type | Name | Value | Status |
|------|------|-------|--------|
| TXT | `agentmail._domainkey` | DKIM public key (`v=DKIM1; k=rsa; p=MIIBIjANB...`) | ● valid |
| MX | `@` | `inbound-smtp.us-east-1.amazonaws.com` Priority: 10 | ● valid |
| MX | `mail` | `feedback-smtp.us-east-1.amazonses.com` Priority: 10 | ● valid |
| TXT | `mail` | `v=spf1 include:amazonses.com -all` | ● valid |
| TXT | `_dmarc` | `v=DMARC1; p=reject; rua=mailto:dmarc@agentmail.to` | ● valid |

**Features**:
- Copy buttons for both Name and Value columns
- Green "valid" badges when records are verified
- Blue "Verifying" status during DNS propagation

**Action Buttons**:
- `↻ Verify Domain` - Trigger manual verification check
- `📄 Download Zone File` - Download complete DNS zone file for import

**Common Questions**:
- "Why is my domain still pending?" → Check DNS propagation (can take up to 48 hours)
- "How do I set up DNS records?" → Add records shown in this modal to your DNS provider
- "What does each record do?":
  - **DKIM (TXT)**: Email authentication and signing
  - **MX (@)**: Receive emails to your domain
  - **MX (mail)**: Handle bounce/feedback emails
  - **SPF (TXT)**: Authorize AgentMail to send on your behalf
  - **DMARC (TXT)**: Policy for handling unauthenticated emails

---

## 3. Webhooks

### Webhooks List View

**Location**: Dashboard > Webhooks

**Purpose**: Manage webhook endpoints for event notifications

**Header**: "Webhooks" with subtitle "Manage webhooks and monitor delivery logs"

**Tab Navigation**:
| Tab | Purpose |
|-----|---------|
| Endpoints | List of webhook URLs |
| Event Catalog | Available event types |
| Logs | Webhook delivery logs |
| Activity | Recent webhook activity |

**Endpoints Table**:
| Column | Description |
|--------|-------------|
| Endpoint | Webhook URL |
| (Disabled badge) | Shows if endpoint is disabled |
| Error Rate | Percentage of failed deliveries |

**Action Button**: `+ Add Endpoint`

---

### Webhook Endpoint Detail View

**Location**: Dashboard > Webhooks > [endpoint-name]

**Purpose**: View and configure a specific webhook endpoint

**Header Section**:
- Endpoint URL displayed prominently
- `Edit` button to modify URL

**Tab Navigation**:
| Tab | Purpose |
|-----|---------|
| Overview | General info and stats |
| Testing | Send test events |
| Advanced | Advanced configuration |

**Overview Tab Content**:

1. **Description Section**:
   - Editable description field
   - "No description" placeholder if empty

2. **Delivery Stats**:
   - Visual chart of successful/failed deliveries
   - Message: "NO MESSAGES RECEIVED IN THE LAST 28 DAYS" if inactive

3. **Message Attempts Table**:
   - Filter buttons: `All`, `Succeeded`, `Failed`
   - Refresh button
   - Filters button

   | Column | Description |
   |--------|-------------|
   | Event Type | e.g., `message.received` |
   | Tags | Custom tags |
   | Message ID | UUID of the message |
   | Timestamp | Delivery timestamp |
   | Status | `✓ Succeeded` or `✗ Failed` |

**Right Sidebar Info**:
- **Creation Date**: When endpoint was created
- **Last Updated**: Last modification date
- **Subscribed events**: List of events (e.g., `message.received`) with Edit link
- **Signing Secret**: Masked secret for webhook verification (with reveal toggle)

---

## 4. API Keys

### API Keys List View

**Location**: Dashboard > API Keys

**Purpose**: Manage API keys for programmatic access

**Header**: "API Keys" with subtitle "X API keys configured"

**Action Button**: `+ Create API Key`

**Table Columns**:
| Column | Description |
|--------|-------------|
| Name | Human-readable key name (e.g., "myNewKey", "mySecondKEY") |
| API Key | Masked key (e.g., `am_2ae75••••••••••••`) |
| Last Used | Last API call timestamp |
| Created | Creation timestamp |
| Actions | Three-dot menu (delete, regenerate) |

**Key Format**: API keys start with `am_` prefix

**Security Notes**:
- API keys are partially masked in the UI
- Full key only shown once at creation
- Store keys securely (e.g., in .env files)

---

## 5. Metrics

### Metrics Dashboard

**Location**: Dashboard > Metrics

**Purpose**: Monitor email sending performance and deliverability

**Header Section**:
- Title: "Metrics Dashboard"
- Subtitle: "Comprehensive analysis of your email metrics • Last 7 days"
- **Time Range** dropdown: Last 7 days, Last 30 days, etc.
- **Display Timezone** dropdown: e.g., "Pacific Time (PT)"

**Tab Navigation**:
| Tab | Purpose |
|-----|---------|
| Overview | Summary statistics |
| Detailed Graphs | In-depth charts |

**Summary Cards (Top Section)**:

| Metric | Icon | Description |
|--------|------|-------------|
| Total Sent | ✈️ (plane) | Emails delivered to recipients |
| Total Delivered | ✓ (check) | Successfully delivered emails |

**Rate Cards (Below Summary)**:

| Metric | Description | Good Value |
|--------|-------------|------------|
| Delivery Rate | Percentage of sent emails delivered | 100% |
| Bounce Rate | Percentage bounced | 0% |
| Complaint Rate | Spam complaints | 0% |
| Rejection Rate | Rejected by recipient servers | 0% |

**Email Metrics - Interactive Chart**:
- Line graph showing sent/delivered over time
- Hourly buckets
- Metric selector dropdown (e.g., "2 selected")

**Email Issues Breakdown Panel**:
- Status badge: `EXCELLENT`, `GOOD`, `WARNING`, `CRITICAL`
- Success message: "100% delivery success!"
- Count: "X emails delivered successfully"
- Celebratory emoji when excellent (🎉)

---

## 6. Pods

### Pods List View

**Location**: Dashboard > Pods

**Purpose**: Organize email infrastructure by isolated workspaces

**Header**: "Pods" with subtitle "Organize your email infrastructure by isolated workspaces"

**Action Button**: `+ Create Pod`

**Pod Cards**:
Each pod displayed as a card with:
- **Pod Name** (bold title): e.g., "Default Pod"
- **Pod ID**: UUID (e.g., `86afd95b-0e4c-55d5-937b-4f7bc9466e43`)
- **Created**: Creation date
- **Action Buttons**:
  - `📧 View Inboxes` - See inboxes in this pod
  - `👁 Unified View` - View all pod messages together
- Three-dot menu for additional options

**Use Cases**:
- Separate development/staging/production environments
- Isolate different projects or clients
- Organize inboxes by team or function

---

## 7. Common UI Patterns

### Tables

All list views share common table features:
- **Checkbox column**: For bulk selection
- **Column visibility**: Toggle columns with "Columns" button
- **Sorting**: Click column headers to sort
- **Pagination**: 
  - "X of Y row(s) selected" counter
  - Rows per page selector (10, 25, 50, 100)
  - Page navigation: First, Previous, Next, Last

### Action Menus

Three-dot menus (⋮) provide contextual actions:
- Edit / View details
- Delete / Remove
- Copy ID
- Additional context-specific options

### Status Badges

Color-coded badges indicate status:
- **Green**: Success, Valid, Enabled, Succeeded
- **Blue**: Verifying, Processing
- **Yellow/Orange**: Warning, Pending
- **Red**: Failed, Error, Disabled
- **Gray**: Default, Inactive

### Search

Global search available via:
- Search icon in header
- Keyboard shortcut: `⌘K` (Mac) / `Ctrl+K` (Windows)

### Feedback

- "Feedback" button in sidebar for reporting issues
- User account section shows email and profile

---

## 8. Common User Questions by UI Section

### Inboxes
- **"How do I create an inbox?"** → Click `+ Create Inbox`, optionally set username/domain/display name
- **"Why can't I see my custom domain?"** → Register it in Domains section first
- **"How do I read emails?"** → Click on inbox row, then click on a thread
- **"What do the tags mean?"** → `received` = incoming, `sent` = outgoing, `unread` = not read yet

### Domains
- **"How long does verification take?"** → Usually minutes, but DNS can take up to 48 hours
- **"Which records do I need?"** → All 5 records (DKIM, 2 MX, SPF, DMARC) for full functionality
- **"What if a record shows invalid?"** → Double-check the value copied correctly, wait for DNS propagation

### Webhooks
- **"How do I test my webhook?"** → Use the "Testing" tab in endpoint detail view
- **"What's the signing secret for?"** → Verify webhook requests are from AgentMail (prevent spoofing)
- **"Why are deliveries failing?"** → Check your endpoint returns 2xx status code within timeout

### API Keys
- **"Where do I find my API key?"** → Dashboard > API Keys
- **"I lost my API key"** → Create a new one; old keys cannot be retrieved
- **"How do I use the API key?"** → Set as Bearer token: `Authorization: Bearer am_xxxxx`

### Metrics
- **"Why is my delivery rate low?"** → Check bounce reasons, email content, sender reputation
- **"What's a good bounce rate?"** → Under 2% is acceptable, under 0.5% is excellent
- **"How often do metrics update?"** → Near real-time, with hourly aggregation

### Pods
- **"What are pods for?"** → Isolate different environments or projects
- **"Can I move inboxes between pods?"** → Currently inboxes are created within a pod
- **"Do I need multiple pods?"** → Only if you need workspace isolation; Default Pod works for most users

---

## 9. UI Tips and Shortcuts

### Keyboard Shortcuts
- `⌘K` / `Ctrl+K`: Open global search
- Standard browser shortcuts for navigation

### Best Practices
1. **Name your resources descriptively** - Makes management easier
2. **Use display names for inboxes** - Improves email appearance
3. **Set up webhooks early** - Real-time notifications are powerful
4. **Monitor metrics regularly** - Catch deliverability issues early
5. **Organize with pods** - Especially for multi-project setups

### Troubleshooting
- **Page not loading?** → Refresh, check network, clear cache
- **Action not working?** → Check permissions, try logging out/in
- **Data not updating?** → Refresh the page, some data has slight delays
