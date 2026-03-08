# AgentMail Console UI — Knowledge Base Research Report

> **Last updated:** 2026-03-07
> **Source directory:** `agentmail-web/apps/console/`
> **Live URL:** [console.agentmail.to](https://console.agentmail.to)
> **Framework:** Next.js 16 (App Router) + React 19 + Tailwind CSS 4

---

## Table of Contents

1. [Overview](#1-overview)
2. [Navigation & Layout](#2-navigation--layout)
   - [Sidebar](#21-sidebar)
   - [Organization Dropdown](#22-organization-dropdown)
   - [Breadcrumb Navigation](#23-breadcrumb-navigation)
   - [Layout Structure](#24-layout-structure)
3. [Overview Dashboard](#3-overview-dashboard)
4. [Inboxes](#4-inboxes)
   - [Inboxes List](#41-inboxes-list)
   - [Create Inbox](#42-create-inbox)
   - [Inbox Detail / Email Client](#43-inbox-detail--email-client)
   - [Inbox Sidebar Navigation](#44-inbox-sidebar-navigation)
   - [Unified Inbox](#45-unified-inbox)
   - [Compose Modal](#46-compose-modal)
   - [Thread Detail View](#47-thread-detail-view)
   - [SMTP/IMAP Credentials](#48-smtpimap-credentials)
5. [Domains](#5-domains)
   - [Domains List](#51-domains-list)
   - [Create Domain](#52-create-domain)
   - [Domain Records & Verification](#53-domain-records--verification)
6. [Webhooks](#6-webhooks)
7. [API Keys](#7-api-keys)
   - [API Keys List](#71-api-keys-list)
   - [Create API Key](#72-create-api-key)
8. [Allow/Block Lists](#8-allowblock-lists)
9. [Metrics](#9-metrics)
   - [Health Score Bar](#91-health-score-bar)
   - [Compact Stat Row](#92-compact-stat-row)
   - [Email Activity Chart](#93-email-activity-chart)
   - [Delivery Funnel](#94-delivery-funnel)
   - [Latency Distribution](#95-latency-distribution)
   - [Inbound/Outbound Chart](#96-inboundoutbound-chart)
   - [Failure Heatmap](#97-failure-heatmap)
10. [Pods](#10-pods)
    - [Pods List](#101-pods-list)
    - [Pod Detail](#102-pod-detail)
11. [Upgrade / Pricing](#11-upgrade--pricing)
12. [UI Patterns](#12-ui-patterns)
    - [DataTable](#121-datatable)
    - [Dialogs & Modals](#122-dialogs--modals)
    - [Delete Confirmation](#123-delete-confirmation)
    - [Status Badges](#124-status-badges)
    - [Empty States](#125-empty-states)
    - [Pagination](#126-pagination)
    - [Premium Feature Banner](#127-premium-feature-banner)
13. [Onboarding System](#13-onboarding-system)
14. [Authentication & Organization Management](#14-authentication--organization-management)
15. [Common User Questions by UI Section](#15-common-user-questions-by-ui-section)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Overview

The **AgentMail Console** is a web-based management dashboard at [console.agentmail.to](https://console.agentmail.to). It provides a full-featured interface for managing inboxes, domains, webhooks, API keys, email metrics, pods (multi-tenancy), and allow/block lists.

**Key characteristics:**
- **Dark mode only** — forced via `<html className="dark">`
- **Authentication** — Clerk (sign-in, sign-up, org management)
- **Data fetching** — SWR (stale-while-revalidate) with server actions for mutations
- **Billing** — Stripe integration (checkout, customer portal)
- **Webhooks** — Svix embedded portal
- **Email client** — Built-in thread viewer with compose, reply, attachments

**Tech stack:**

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 16.0.0 |
| UI | React | 19.1.1 |
| Styling | Tailwind CSS | 4.1.11 |
| Auth | Clerk | 6.12.0 |
| Data fetching | SWR | 2.3.8 |
| Tables | @tanstack/react-table | 8.21.3 |
| Charts | Recharts | 3.7.0 |
| Icons | Lucide React | 0.475.0 |
| Billing | Stripe | 17.5.0 |
| Webhooks | Svix | 1.84.1 |

---

## 2. Navigation & Layout

### 2.1 Sidebar

The sidebar is the primary navigation element. It is collapsible: **208px (w-52)** expanded, **64px (w-16)** collapsed. In collapsed mode, icons are shown with right-side tooltips.

**Navigation items (in order):**

| # | Label | Icon | Route |
|---|-------|------|-------|
| 1 | Overview | `LayoutDashboard` | `/dashboard/overview` |
| 2 | Inboxes | `Inbox` | `/dashboard/inboxes` |
| 3 | Domains | `Globe` | `/dashboard/domains` |
| 4 | Webhooks | `Webhook` | `/dashboard/webhooks` |
| 5 | API Keys | `Key` | `/dashboard/api-keys` |
| 6 | Allow/Block Lists | `Shield` | `/dashboard/lists` |
| 7 | Metrics | `BarChart3` | `/dashboard/metrics` |
| 8 | Pods | `Box` | `/dashboard/pods` |

**Active state:** `bg-accent text-accent-foreground` when pathname matches.

**Bottom section (external links):**

| Label | Icon | URL |
|-------|------|-----|
| Discord | `DiscordIcon` (custom) | `https://discord.gg/EmDHrGsyQ4` |
| Documentation | `BookOpen` | `https://docs.agentmail.to` |
| Feedback | `MessageSquare` | `mailto:support@agentmail.cc` |

**User button** — Clerk `UserButton` at bottom. Shows avatar and name (expanded) or avatar only (collapsed). `afterSignOutUrl="/sign-in"`.

**Navigation tree:**

```
Sidebar (w-52 / w-16)
├── Logo (AgentMail) + Collapse toggle
├── Organization Dropdown
├── ── ── ── ── ── ──
├── Overview              → /dashboard/overview
├── Inboxes               → /dashboard/inboxes
│   ├── [inboxId]         → /dashboard/inboxes/[inboxId]
│   │   ├── (Inbox)       → /dashboard/inboxes/[inboxId]
│   │   ├── Starred       → /dashboard/inboxes/[inboxId]/starred
│   │   ├── Sent          → /dashboard/inboxes/[inboxId]/sent
│   │   ├── Drafts        → /dashboard/inboxes/[inboxId]/drafts
│   │   ├── Important     → /dashboard/inboxes/[inboxId]/important
│   │   ├── Scheduled     → /dashboard/inboxes/[inboxId]/scheduled
│   │   ├── All Mail      → /dashboard/inboxes/[inboxId]/all
│   │   ├── Spam          → /dashboard/inboxes/[inboxId]/spam
│   │   ├── Trash         → /dashboard/inboxes/[inboxId]/trash
│   │   └── Thread        → /dashboard/inboxes/[inboxId]/threads/[threadId]
│   ├── Unified Inbox     → /dashboard/unified
│   │   ├── All Inboxes   → /dashboard/unified
│   │   ├── Starred       → /dashboard/unified/starred
│   │   ├── Sent          → /dashboard/unified/sent
│   │   ├── Drafts        → /dashboard/unified/drafts
│   │   ├── Important     → /dashboard/unified/important
│   │   ├── Scheduled     → /dashboard/unified/scheduled
│   │   ├── All Mail      → /dashboard/unified/all
│   │   └── Spam          → /dashboard/unified/spam
│   └── SMTP/IMAP         → /dashboard/inboxes/smtp-imap
├── Domains               → /dashboard/domains
├── Webhooks              → /dashboard/webhooks
├── API Keys              → /dashboard/api-keys
├── Allow/Block Lists     → /dashboard/lists
├── Metrics               → /dashboard/metrics
├── Pods                  → /dashboard/pods
│   └── [podId]           → /dashboard/pods/[podId]
│       ├── Inboxes tab
│       ├── Domains tab
│       ├── API Keys tab
│       └── Unified Inbox → /dashboard/pods/[podId]/threads
├── Upgrade               → /dashboard/upgrade
├── ── ── ── ── ── ──
├── Discord (external)
├── Documentation (external)
├── Feedback (mailto)
└── User Button (Clerk)
```

### 2.2 Organization Dropdown

Located at the top of the sidebar, below the logo.

**Expanded trigger shows:** Org avatar, org name, `ChevronsUpDown` icon. If agent-created: shows "Agent Created" subtitle.

**Dropdown contents:**

| Section | Action | Icon | Behavior |
|---------|--------|------|----------|
| Header | Org info | — | Avatar, name, tier, member count, "Member since" date |
| Actions | Organization Settings | `Settings` | Opens Clerk org profile dialog |
| Actions | Switch Organization | `ArrowRightLeft` | Navigates to `/select-organization` |
| Billing | Upgrade Plan | `CreditCard` | Shown for free tier → `/dashboard/upgrade` |
| Billing | Manage Subscription | `CreditCard` | Shown for paid tiers → Stripe portal |

**Tier display format:** `"{tierName} · {count} {members/member}"` (e.g., "Developer · 3 members")

### 2.3 Breadcrumb Navigation

Displayed in the 56px header bar above the content area.

**Route-to-label mapping:**

| Segment | Label |
|---------|-------|
| `dashboard` | Dashboard |
| `overview` | Overview |
| `inboxes` | Inboxes |
| `domains` | Domains |
| `webhooks` | Webhooks |
| `api-keys` | API Keys |
| `lists` | Allow/Block Lists |
| `metrics` | Metrics |
| `pods` | Pods |
| `upgrade` | Upgrade |
| `unified` | Unified Inbox |
| `smtp-imap` | SMTP/IMAP |
| `all` | All Mail |
| `spam` | Spam |
| `sent` | Sent |
| `starred` | Starred |
| `important` | Important |
| `drafts` | Drafts |
| `scheduled` | Scheduled |

**Dynamic segments:**
- **Inbox ID** — Shows `inbox.name` with a **copy button** (copies email address). Has `data-onboarding="inbox-breadcrumb"` attribute.
- **Pod ID** — Shows `pod.name`
- **Thread ID** — Shows `thread.subject` (truncated at 50 chars) or "Thread"

### 2.4 Layout Structure

```
┌──────────────────────────────────────────────────┐
│  Sidebar (w-52)  │  Header (h-14, breadcrumbs)   │
│                  │───────────────────────────────│
│  [Logo]          │                               │
│  [Org dropdown]  │  Main Content Area            │
│  ─────────────   │  (scrollable, px-6 py-4)      │
│  Overview        │                               │
│  Inboxes         │                               │
│  Domains         │                               │
│  Webhooks        │                               │
│  API Keys        │                               │
│  Allow/Block     │                               │
│  Metrics         │                               │
│  Pods            │                               │
│  ─────────────   │                               │
│  Discord         │                               │
│  Docs            │                               │
│  Feedback        │                               │
│  ─────────────   │                               │
│  [User avatar]   │                               │
└──────────────────────────────────────────────────┘
```

**Auth guards:** Users without `userId` are redirected to `/sign-in`. Users without `orgId` are redirected to `/select-organization`.

---

## 3. Overview Dashboard

**Route:** `/dashboard/overview`

The overview is the landing page after login. It provides a high-level summary of the organization's email activity and resources.

**Layout (top to bottom):**

1. **Email Activity Chart** — Full-width stacked bar chart with time range selector (24h / 7d / 30d). Title: "Email Activity". Default range: `7d`.

2. **Two-column grid** (70%/30% split):
   - **Left:** Unified Inbox Preview — Recent threads across all inboxes
   - **Right (stacked):**
     - **Resource Cards** — Shows domain and inbox counts with usage limits
     - **Bounce Rate Card** — 7-day bounce/complaint rate with risk thresholds
     - **Onboarding Checklist** — "Getting Started" guide (see [Section 13](#13-onboarding-system))

**Resource Cards detail:**

| Resource | Icon | Display |
|----------|------|---------|
| Domains | `Globe` | Count, or `count/limit` with progress bar, or "Upgrade" button if limit=0 |
| Inboxes | `Mail` | Count, or `count/limit` with progress bar |

**Usage alert thresholds (both inboxes and domains):**

| Condition | Message | Color |
|-----------|---------|-------|
| count >= limit | "You've reached your {resource} limit ({count}/{limit})." | Red |
| count >= 80% of limit | "You're approaching your {resource} limit ({count}/{limit})." | Orange |
| count >= 50% of limit | "You've used 50% of your {resource} limit." | Amber |

Each alert includes an "Upgrade →" link.

**Bounce Rate Card:**

Two toggle tabs: **Bounce Rate** and **Complained Rate**

| Tab | Metric | Bar Color | Risk Threshold | Y-Axis Max |
|-----|--------|-----------|----------------|------------|
| Bounce Rate | bounced/sent × 100 | Blue `hsl(210, 70%, 55%)` | 5% | 10% |
| Complained Rate | complained/sent × 100 | Orange `hsl(25, 75%, 55%)` | 0.1% | 0.5% |

Bars that meet or exceed the threshold turn red. A dashed "RISK" reference line marks the threshold.

**Auto-onboarding:** If the org has no inboxes and onboarding hasn't been completed, the onboarding flow starts automatically.

---

## 4. Inboxes

### 4.1 Inboxes List

**Route:** `/dashboard/inboxes`
**Header:** Title: "Inboxes" | Subtitle: "Manage your email inboxes"

**Header buttons (right side):**
- **Unified Inbox** (ghost) → `/dashboard/unified`
- **SMTP/IMAP** (ghost) → `/dashboard/inboxes/smtp-imap`
- **Create Inbox** (with Plus icon, `data-onboarding="create-inbox-btn"`)

**Table columns:**

| Column | Header | Width | Content |
|--------|--------|-------|---------|
| `inboxId` | Inbox ID | auto | `inbox.name` (truncated, font-medium) |
| `displayName` | Display Name | 200px | Display name or `"-"` |
| `createdAt` | Created | 180px | Formatted date |
| `updatedAt` | Updated | 180px | Formatted date |
| `actions` | (empty) | 50px | Three-dot menu |

**Row actions:**
- **Update Display Name** (`Pencil` icon) — Opens update dialog
- **Delete** (`Trash2` icon, red text) — Opens delete confirmation

**Row click:** Navigates to `/dashboard/inboxes/[inboxId]`

**Empty state:** Icon: `Inbox` | "No inboxes yet" | "Create your first inbox to get started"

### 4.2 Create Inbox

**Dialog title:** "Create Inbox" (or "Create Inbox in {podName}" when in a pod)
**Dialog description:** "Create a new email inbox for your agents" (or "Create a new email inbox for this pod.")

**Form fields:**

| Field | Label | Placeholder | Validation |
|-------|-------|-------------|------------|
| Username | Username (optional) | "e.g. sales" | Letters, numbers, dots, dashes, underscores only |
| Domain | Domain | "Select a domain" | Required (default: `agentmail.to`) |
| Display Name | Display Name (optional) | "e.g. Sales Team" | None |

**Info hint:** "Username will be auto-generated if not specified"

**Error messages:**

| Error Code | Message |
|------------|---------|
| `INBOX_EXISTS` | "This inbox address already exists in your organization." |
| `INBOX_TAKEN` | "This inbox address is already taken. Please try a different username or domain." |
| `LIMIT_EXCEEDED` | "You have reached your inbox limit. Please upgrade your plan or remove an existing inbox." |
| `DOMAIN_NOT_FOUND` | "The domain is not registered or verified. Please verify the domain first." |
| Catch-all | "Failed to create inbox. Please try again." |

**Submit button:** "Create Inbox" (Plus icon) → "Creating..." (spinner)

### 4.3 Inbox Detail / Email Client

**Route:** `/dashboard/inboxes/[inboxId]`

When you click an inbox row, you enter a full-screen email client layout. This uses the `InboxLayoutUI` component from the shared `@workspace/ui` package. The layout is:

```
┌──────────────────────────────────────────────┐
│ Inbox Sidebar │ Thread List │ Thread Detail  │
│ (Compose btn) │ (clickable) │ (messages)     │
│ Inbox         │             │                │
│ Starred       │             │                │
│ Sent          │             │                │
│ Drafts        │             │                │
│ Important     │             │                │
│ Scheduled     │             │                │
│ All Mail      │             │                │
│ Spam          │             │                │
│ Trash         │             │                │
└──────────────────────────────────────────────┘
```

The layout fills the full viewport height minus the 56px header: `h-[calc(100vh-3.5rem)]`.

### 4.4 Inbox Sidebar Navigation

**Single inbox sidebar items:**

| # | Label | Icon | Route suffix |
|---|-------|------|-------------|
| — | **Compose** (button) | `Pencil` | Opens compose modal |
| 1 | Inbox | `Inbox` | `/` |
| 2 | Starred | `Star` | `/starred` |
| 3 | Sent | `Send` | `/sent` |
| 4 | Drafts | `File` | `/drafts` |
| 5 | Important | `Flag` | `/important` |
| 6 | Scheduled | `Clock` | `/scheduled` |
| 7 | All Mail | `Mail` | `/all` |
| 8 | Spam | `AlertOctagon` | `/spam` |
| 9 | Trash | `Trash2` | `/trash` |

Each sub-view filters threads by the corresponding label.

### 4.5 Unified Inbox

**Route:** `/dashboard/unified`

Cross-inbox thread view. Same layout as single inbox but shows threads from **all** inboxes.

**Unified sidebar items (differences from single-inbox):**
- First item is **"All Inboxes"** instead of "Inbox"
- **No "Trash"** item (8 items instead of 9)
- Compose is a no-op in unified mode

### 4.6 Compose Modal

**Window title:** "New Message"

**Form fields:**

| Field | Placeholder | Type | Notes |
|-------|-------------|------|-------|
| To | (empty) | email | Required |
| Cc | (empty) | email | Toggle button, hidden by default |
| Bcc | (empty) | email | Toggle button, hidden by default |
| Subject | "Subject" | text | — |
| Body | (empty) | textarea | — |

**Attachment handling:**
- Max file size: **25 MB** per file
- Oversized error: "File(s) too large: {names}. Max size is 25MB per file."
- Duplicate error: "All selected files are already attached."

**Window controls:** Minimize, Full screen / Exit full screen, Close
**Window sizes:** Normal: 500×450px | Full screen: 800×80vh | Minimized: 250×36px

**Send button states:** "Send" → "Sending..." → "Sent!" (with check icon). Also supports "Scheduling..." → "Scheduled!" for scheduled sends.

### 4.7 Thread Detail View

**Route:** `/dashboard/inboxes/[inboxId]/threads/[threadId]`

Shows the full email thread with all messages. Features:
- Download message as `.eml` file (filename: `message-{messageId}.eml`)
- Preview/download attachments
- Add/remove message labels
- Back navigation to inbox

**Loading state:** "Loading thread..."
**Error state:** "Failed to load thread" with "Back to inbox" link

### 4.8 SMTP/IMAP Credentials

**Route:** `/dashboard/inboxes/smtp-imap`
**Header:** Title: "SMTP/IMAP Credentials" (Key icon) | Subtitle: "Export credentials for cold email platforms like Smartlead or Instantly"

**API Key input:** Required to populate password fields. Placeholder: `"am_live_xxxxx"`. Toggle show/hide.

**Platform selector (3 options):**

| Platform | Value | Notes |
|----------|-------|-------|
| Generic | `generic` | Standard SMTP/IMAP columns |
| Smartlead | `smartlead` | Includes From Name/From Email |
| Instantly | `instantly` | Includes First/Last Name; SMTP username hardcoded as "agentmail" |

**Export:** "Export as CSV" button (Download icon). Disabled when no credentials.

**Connection details (across all platforms):**

| Protocol | Host | Port |
|----------|------|------|
| SMTP | `smtp.agentmail.to` | 465 |
| IMAP | `imap.agentmail.to` | 993 |

**Password:** Uses the API key. Shows "Enter API Key" placeholder if not entered.

**Row action:** Copy button copies entire row to clipboard.

---

## 5. Domains

### 5.1 Domains List

**Route:** `/dashboard/domains`
**Header:** Title: "Domains" | Subtitle: "Manage your custom domains for sending emails"

**Premium gate:** When `org.domainLimit === 0` (free tier), a premium banner is shown: "Upgrade to Developer or Startup plan to use custom domains for sending emails."

**Table columns:**

| Column | Header | Width | Content |
|--------|--------|-------|---------|
| `domainId` | Domain | auto | Domain name (truncated, font-medium) |
| `status` | Status | 120px | Badge (see status values below) |
| `feedbackEnabled` | Feedback | 100px | Badge: "Enabled" or "Disabled" |
| `createdAt` | Created | 180px | Formatted date |
| `updatedAt` | Updated | 180px | Formatted date |
| `actions` | (empty) | 50px | Three-dot menu → Delete |

**Row click:** Opens Domain Details dialog with DNS records.

**Empty state:** Icon: `Globe` | "No domains configured" | "Add your first domain to start sending emails from your own domain"

### 5.2 Create Domain

**Dialog title:** "Add New Domain" (or "Add Domain to {podName}" in pod context)
**Dialog description:** "Configure your domain for sending emails with precision and control"

**Form field:**

| Field | Label | Placeholder | Validation |
|-------|-------|-------------|------------|
| Domain | Domain Name | "your-domain.com" | Required; must have dot; no leading/trailing dots; TLD >= 2 chars |

**Validation errors:**

| Condition | Message |
|-----------|---------|
| Empty | "Domain name is required." |
| No dot | "Domain is malformed. Please try again." |
| Starts/ends with dot | "A domain cannot start or end with a '.'." |
| Multiple consecutive dots | "Invalid domain format. Check for multiple dots together." |
| TLD too short | "The top-level domain (e.g., '.com') must be at least two characters long." |

**Info cards (general mode):**

1. **Domain Requirements:** Must be valid domain, under your control, feedback auto-enabled
2. **Next Steps:** DNS records generated → Add to DNS provider → Auto-verification → Start sending

**Post-creation:** Shows DNS records table. Footer buttons: "Add Another Domain" (ghost) + "Done" (check icon).

### 5.3 Domain Records & Verification

**Dialog title:** "Domain: {domainId}"
**Subtitle:** "DNS Records Configuration"

**Records table columns:**

| Column | Header | Width | Content |
|--------|--------|-------|---------|
| Type | Type | 15% | Badge (outline): `TXT`, `CNAME`, or `MX` |
| Name | Name | 35% | Mono text + Copy button |
| Value | Value | 35% | Mono text, truncated at 50 chars with popover + Copy button |
| Status | Status | 15% | Status indicator badge (only when status info available) |

**MX records** additionally show: "Priority: {priority}" (default 10).

**DNS record status values:**

| Status | Display Text | Badge Variant | Indicator Color | Animation |
|--------|-------------|---------------|-----------------|-----------|
| `VERIFIED` | "verified" | default (green) | `bg-green-500` | — |
| `VALID` | "valid" | default (green) | `bg-green-500` | — |
| `VERIFYING` | "verifying" | secondary | `bg-blue-500` | Pulsing |
| `PENDING` | "pending" | secondary | `bg-yellow-500` | Pulsing |
| `NOT_STARTED` | "Not Started" | secondary | `bg-yellow-500` | Pulsing |
| `FAILED` | "failed" | destructive (red) | `bg-red-500` | — |
| `INVALID` | "invalid" | destructive (red) | `bg-red-500` | — |

**Action buttons:**
- **Verify Domain** — `RefreshCw` icon. Has 5-minute cooldown (persisted in localStorage). Shows countdown during cooldown.
- **Download Zone File** — `FileText` icon. Downloads BIND-format zone file as `{domain}.zone`.

**Verification nudge messages:**
- All DNS records verified but domain NOT_STARTED: "Great! All DNS records are verified. Click 'Verify Domain' below to complete domain verification..."
- Domain FAILED/INVALID: "Domain verification failed. Please ensure all DNS records are correctly configured..."
- Verifying for > 1 hour: "Your domain has been verifying for over an hour. DNS records can sometimes get stuck..."

**Zone file tooltip:** "Some quirky registries like Namecheap doesn't support bulk zone file upload--paste records individually instead." + link to `https://docs.agentmail.to/custom-domains`.

---

## 6. Webhooks

**Route:** `/dashboard/webhooks`
**Header:** Title: "Webhooks" | Subtitle: "Manage webhook endpoints and monitor delivery"

The webhooks section uses an **embedded Svix portal** via iframe. The portal URL is fetched from `POST /api/webhooks/portal-url` with `{ darkMode: true }`.

**Svix portal features (provided by Svix):**
- Create/edit/delete webhook endpoints
- Event catalog and filtering
- Delivery monitoring and logs
- Retry failed deliveries
- Signing secret management

**Iframe:** Height: 800px, width: 100%, `allow="clipboard-write"`, `loading="lazy"`, title: "Svix Webhook Portal"

**Error state:** "Failed to load webhook portal" with "Try Again" button.

> **Support note:** Webhook management UI is entirely provided by Svix. AgentMail does not control the portal's internal UI. If users report webhook portal issues, check Svix status.

---

## 7. API Keys

### 7.1 API Keys List

**Route:** `/dashboard/api-keys`
**Header:** Title: "API Keys" | Subtitle: "Manage API keys for authenticating with the AgentMail API"

**Table columns:**

| Column | Header | Width | Content |
|--------|--------|-------|---------|
| `name` | Name | auto | Key name (truncated, font-medium) |
| `scope` | Scope | 100px | "Pod" if pod-scoped, otherwise "Org" |
| `apiKey` | API Key | 200px | `{prefix}•••••••••••••` (mono, gray background) |
| `usedAt` | Last Used | 180px | Formatted datetime |
| `createdAt` | Created | 180px | Formatted date |
| `actions` | (empty) | 50px | Three-dot menu → Delete |

**Masking format:** `{prefix}` followed by 13 bullet characters (U+2022). The full key is never shown after creation.

**Empty state:** Icon: `Key` | "No API keys configured" | "Create your first API key to start using the AgentMail API"

### 7.2 Create API Key

**Dialog title:** "Create API Key"
**Dialog description:** "Create a new API key to authenticate with the AgentMail API."

**Form fields:**

| Field | Label | Placeholder | Helper Text |
|-------|-------|-------------|-------------|
| Name | Name | "My API Key" | "A friendly name to identify this API key." |
| Scope | Scope (optional) | "Limit to a pod or leave empty for org-wide" | "Limit to a pod or leave empty for org-wide access." |

**Scope options:**
- "No scope" (value: `none`) — org-wide access
- List of pods from API — pod-scoped access

**Validation:** Name is required ("Name is required").

**Success view (shown once after creation):**

Security warning (yellow): "Save your API key now — Make sure to copy or download your API key now. You won't be able to see it again!"

Displayed fields:
- **API Key** — Full key in readonly input + Copy button + Download button
- **Display Name** — Readonly input
- **Key Prefix** — Readonly mono input

**Download filename:** `agentmail_api_key_{keyName}`

Footer: "Create Another" (ghost) + "Done" (check icon)

---

## 8. Allow/Block Lists

**Route:** `/dashboard/lists`
**Header:** Title: "Lists" | Subtitle: "Manage allow and block lists for email"

**Layout:** Two sections ("Receive" and "Send"), each containing a 2-column grid with Allow List and Block List.

**Four lists displayed:**

| Section | Title | Direction | Type | Shows Reason Column |
|---------|-------|-----------|------|-------------------|
| Receive | Allow List | `receive` | `allow` | No |
| Receive | Block List | `receive` | `block` | Yes |
| Send | Allow List | `send` | `allow` | No |
| Send | Block List | `send` | `block` | Yes |

**Table columns per list:**

| Column | Shown In | Content |
|--------|----------|---------|
| Address | All lists | Email address or domain |
| Reason | Block lists only | Reason text or "—" |
| Created At | All lists | Formatted date |
| Actions | All lists | Three-dot menu → Delete |

**Add entry dialog:**
- Title: "Add to {Allow List/Block List}"
- Fields: Address (required, placeholder: "user@example.com or example.com") + Reason (optional, block lists only, placeholder: "Spam sender")
- Help text: "An email address or domain to allow/block."
- Submit: "Add Entry" → "Adding..."

---

## 9. Metrics

**Route:** `/dashboard/metrics`
**Header:** Title: "Metrics" | Dynamic subtitle based on time range ("Last 24 hours" / "Last 7 days" / "Last 30 days")

**Controls (top right):**

| Control | Options | Default |
|---------|---------|---------|
| Time Range | "Last 24 hours" (24h), "Last 7 days" (7d), "Last 30 days" (30d) | 7d |
| Timezone | 12 common timezones + auto-detected user timezone | Browser timezone |

**Available timezones:**

| Value | Label |
|-------|-------|
| `UTC` | UTC (Coordinated Universal Time) |
| `America/Los_Angeles` | Pacific Time (PT) |
| `America/Denver` | Mountain Time (MT) |
| `America/Chicago` | Central Time (CT) |
| `America/New_York` | Eastern Time (ET) |
| `Europe/London` | London (GMT/BST) |
| `Europe/Paris` | Paris (CET/CEST) |
| `Europe/Berlin` | Berlin (CET/CEST) |
| `Asia/Tokyo` | Tokyo (JST) |
| `Asia/Shanghai` | Shanghai (CST) |
| `Asia/Kolkata` | India (IST) |
| `Australia/Sydney` | Sydney (AEST/AEDT) |

If the user's browser timezone isn't in the list, it's added with a "(Your Timezone)" label.

**Layout (5 sections, top to bottom):**

1. Health Score Bar (full width)
2. Compact Stat Row (full width)
3. Email Activity chart (full width, 350px height)
4. Two-column grid: Delivery Funnel + Latency Distribution
5. Two-column grid: Inbound/Outbound Chart + Failure Heatmap

**Empty state:** Icon: `BarChart3` | "No Metrics Data Yet" | "Once you start sending emails through AgentMail, you'll see detailed analytics here."

### 9.1 Health Score Bar

Displays a health score (0-100) with a Shield icon.

**Health levels:**

| Level | Label | Text Color | Background | Score Range |
|-------|-------|------------|------------|-------------|
| Excellent | "Excellent" | Emerald | `bg-emerald-500/10` | High |
| Good | "Good" | Blue | `bg-blue-500/10` | — |
| Average | "Average" | Amber | `bg-amber-500/10` | — |
| Concerning | "Concerning" | Orange | `bg-orange-500/10` | — |
| Critical | "Critical" | Red | `bg-red-500/10` | Low |

**Display:** "Score: {score} — {label}" + sparkline SVG (120×32px) showing daily health scores over the period.

### 9.2 Compact Stat Row

Horizontal row of key metrics with period-over-period comparison arrows.

**Left group (volume stats):**
- `{sent} sent` · `{delivered} delivered` · `{deliveryRate}% delivery` · `{received} received`

**Right group (problem stats, separated by divider):**
- `{bounced} bounced` · `{complained} complained` · `{rejected} rejected`

**Comparison arrows:**
- Volume stats: up = green (good), down = neutral
- Problem stats: up = red (bad), down = green (good)

**Anomaly highlighting:**
- Bounce rate > 2%: Text turns red
- Any complaints > 0: Text turns orange
- Reject rate > 2%: Text turns red

### 9.3 Email Activity Chart

Stacked bar chart (Recharts) showing email volume by status over time.

- **Series:** Sent, Delivered, Bounced, Failed
- **Title:** "Email Activity"
- **Height:** 350px
- Timezone-aware timestamps

### 9.4 Delivery Funnel

**Title:** "Delivery Funnel"
**Subtitle:** "{sent} sent — where did they end up?"

Horizontal bar chart showing the breakdown of sent emails:

| Segment | Color |
|---------|-------|
| Delivered | Green `hsl(145, 65%, 50%)` |
| Bounced | Red `hsl(0, 70%, 55%)` |
| Rejected | Purple `hsl(270, 60%, 55%)` |
| Delayed | Yellow `hsl(45, 85%, 55%)` |

Format: "{count} ({pct}%)" per bar. Segments with count=0 are hidden.

**Special states:**
- No sent emails: "No sent emails in this period."
- 100% delivered: Green checkmark + "All emails delivered successfully"

### 9.5 Latency Distribution

**Title:** "Delivery Latency"

**Latency quality tiers:**

| Threshold | Label | Color |
|-----------|-------|-------|
| < 1000ms | Fast | Emerald |
| < 5000ms | Normal | Foreground |
| < 30000ms | Slow | Amber |
| >= 30000ms | Very Slow | Red |

**Display modes:**
- **No data (0 deliveries):** "Not enough data to compute latency."
- **Few data points (< 4):** Individual latency entries + average line
- **Sufficient data (>= 4):** Percentile stats (p50, p95, p99) + histogram bar chart (120px height)

### 9.6 Inbound/Outbound Chart

**Title:** "Email Flow — Inbound vs Outbound"
**Subtitle:** "Volume comparison over time"

Dual area chart:
- **Outbound (Sent):** Blue `hsl(220, 70%, 55%)`
- **Inbound (Received):** Green `hsl(150, 60%, 45%)`

Natural curve interpolation with 40% fill opacity.

**Empty state:** "No email activity in this period."

### 9.7 Failure Heatmap

**Title:** "Failure Patterns"
**Subtitle:** "{totalFailures} failure(s) — when do they happen?"

7×24 grid (days × hours). Hour labels shown every 3 hours (`12a`, `3a`, `6a`, ... `9p`).

**Cell color intensity (5 levels):**

| Intensity | Background |
|-----------|------------|
| 0 failures | `bg-muted/30` |
| <= 25% of max | `bg-amber-500/20` |
| <= 50% of max | `bg-orange-500/30` |
| <= 75% of max | `bg-red-500/40` |
| > 75% of max | `bg-red-500/60` |

**Cell tooltip:** "{day} {hour}: {count} failure(s)"

**Legend:** "Less" [5 swatches] "More"

**Zero failures:** Green checkmark + "No failures in this period"

---

## 10. Pods

### 10.1 Pods List

**Route:** `/dashboard/pods`
**Header:** Title: "Pods" | Subtitle: "Manage your isolated workspaces for multi-tenant applications"

**Table columns:**

| Column | Header | Width | Content |
|--------|--------|-------|---------|
| `name` | Name | auto | Pod name (bold) + client ID in mono below |
| `createdAt` | Created | 180px | Formatted date |
| `actions` | (empty) | 50px | Three-dot menu |

**Row actions:**
- Default pod: "Cannot Delete Default" (disabled, muted)
- Other pods: "Delete Pod" (destructive, `Trash2` icon)

**Row click:** Navigates to `/dashboard/pods/[podId]`

**Empty state:** Icon: `Box` | "No pods yet" | "Create your first pod to start organizing your multi-tenant workloads."

### 10.2 Pod Detail

**Route:** `/dashboard/pods/[podId]`

**Header:** Back button ("Back to Pods"), pod icon + name, client ID (mono), created date. Options menu (delete, except default pod).

**Three tabs:**

| Tab | Label | Icon | Content |
|-----|-------|------|---------|
| `inboxes` | Inboxes | `Inbox` | Pod's inboxes (same DataTable as org inboxes) + "Unified Inbox" + "SMTP/IMAP" + "Create Inbox" buttons |
| `domains` | Domains | `Globe` | Pod's domains (same DataTable as org domains) + "Create Domain" button |
| `api-keys` | API Keys | `Key` | Pod-scoped API keys (same DataTable as org API keys) + "Create API Key" button |

Default tab: `inboxes`

**Pod-scoped create dialogs:** Create Inbox, Create Domain, and Create API Key dialogs all work in pod context, scoping resources to the pod.

**Pod unified inbox:** Available at `/dashboard/pods/[podId]/threads` — shows threads across all inboxes in the pod.

---

## 11. Upgrade / Pricing

**Route:** `/dashboard/upgrade`
**Header:** Title: "Upgrade Your Plan" | Subtitle varies by current tier

**Pricing tiers (4 columns):**

| Tier | Name | Price | Key Features |
|------|------|-------|-------------|
| `free` | Free | $0/month | No credit card required, 3 inboxes, 3,000 emails/month, 3 GB storage |
| `developer` | Developer | $20/month | 10 inboxes, 10,000 emails/month, 10 GB storage, 10 custom domains, Email support |
| `startup` | Startup | $200/month | 150 inboxes, 150,000 emails/month, 150 GB storage, 150 custom domains, Dedicated IPs, SOC 2 report, Slack channel support |
| `enterprise` | Enterprise | Custom | Everything in Startup, Custom volume pricing, White-label platform, EU region cloud, BYO cloud deployment, OIDC/SAML SSO |

**Card badges:**
- Current plan: "Current" badge
- Startup (when not current): "Popular" badge (inverted styling)

**Button states:**
- Current plan: "Current Plan" (disabled, with check icon)
- Lower tier: "Included in Your Plan" (disabled)
- Higher tier: "Upgrade to {tier}" (Crown icon) → "Creating checkout..." (spinner)
- Enterprise: "Contact Sales" → `mailto:founders@agentmail.cc`

**Checkout:** Stripe checkout session via `POST /api/billing/checkout-session`. Users with an existing Stripe subscription are redirected to `/dashboard`.

**Cancelled checkout:** Yellow banner: "Your upgrade was cancelled. You can try again anytime."

---

## 12. UI Patterns

### 12.1 DataTable

Built on `@tanstack/react-table`. Used consistently across all list views.

**Features:**
- Fixed column widths via `width` property
- Row click callbacks (navigation)
- Hover state: `cursor-pointer hover:bg-muted/50`
- Loading state with skeleton animation
- Empty state message
- Server-side pagination (see [Pagination](#126-pagination))

### 12.2 Dialogs & Modals

Built on Radix UI Dialog. Two modes:
- **Trigger mode:** Pass children as the trigger button
- **Controlled mode:** `isOpen` and `onClose` props

Standard structure: `DialogContent` > `DialogHeader` > `DialogTitle` + `DialogDescription` > form > footer buttons.

### 12.3 Delete Confirmation

Generic `DeleteConfirmDialog<T>` used for all delete operations.

**Standard flow:**
1. Dialog title: "Delete {ResourceName}"
2. Description: "This action cannot be undone. This will permanently delete the {resourcename}."
3. Warning box (red border): "Warning" heading + custom warning message
4. Type-to-confirm: "To confirm, please type **delete** in the box below." → placeholder: "Type 'delete' to confirm"
5. Buttons: "Cancel" + "Delete {ResourceName}" (destructive, disabled until "delete" typed)
6. Deleting state: "Deleting..." with spinner

**Resource-specific warning messages:**

| Resource | Warning |
|----------|---------|
| Inbox | Default |
| Domain | "You will lose the ability to send and receive emails from this domain, but you will still have access to existing inbox information." |
| API Key | "You are about to delete {keyName}. Any applications using this API key will no longer be able to authenticate." + shows masked key |
| Pod | Default (cannot delete default pod) |
| List Entry | "You are about to remove {entry} from the {allow/block list}." |

### 12.4 Status Badges

**Domain/DNS status badges:**

| Status | Variant | Color |
|--------|---------|-------|
| VERIFIED / VALID | default | Green |
| VERIFYING / PENDING / NOT_STARTED | secondary | Yellow/Blue indicator |
| FAILED / INVALID | destructive | Red |

**Feedback badges:** "Enabled" (default) / "Disabled" (secondary)

**API key scope:** Plain text "Org" or "Pod" (not a badge)

### 12.5 Empty States

Two variants:

**PageEmptyState** — Centered icon (size-12, muted) + title + description. Used in tables.

**CardEmptyState** — Same content inside a Card component (max-w-md). Used on dedicated pages like Metrics.

### 12.6 Pagination

`PaginationBar` component at the bottom of all DataTables.

**Features:**
- **Rows per page:** Dropdown with options `[5, 10, 20, 30, 50]` (default: 30)
- **Navigation:** First (⏮), Previous (◀), range display ("{start} to {end}"), Next (▶), Last (⏭)
- Server-side pagination using `pageToken`
- Does **not** display total count or total pages

### 12.7 Premium Feature Banner

Shown when a feature's limit is 0 (free tier restriction).

**Styling:** Amber/orange gradient card with Crown icon.
- Heading: "Premium Feature"
- Message: Custom or default "{feature} limit reached. Upgrade to add more."
- Button: "Upgrade Plan" (amber background) → `/dashboard/upgrade`
- Optional dismiss (X button)

---

## 13. Onboarding System

Triggered automatically when a new org has no inboxes. Also accessible from the Overview page.

**Card title:** "Getting Started"
**Progress:** "{completed}/{total} completed"

**Checklist steps (2×2 grid):**

| # | Label | Icon | Link | Completion Condition |
|---|-------|------|------|---------------------|
| 1 | Create an inbox | `Mail` | `/dashboard/inboxes` | `org.inboxCount > 0` |
| 2 | Receive an email | `Inbox` | `/dashboard/inboxes` | Any threads exist |
| 3 | Create an API key | `Key` | `/dashboard/api-keys` | `apiKeyCount > 0` |
| 4 | Read the docs | `BookOpen` | `https://docs.agentmail.to` | Docs link visited (localStorage) |

**Step visual states:**
- Completed: `CheckCircle2` icon (primary), text has line-through + 50% opacity
- Incomplete: `Circle` icon (muted), normal text

**CTA button:** Shows the label of the first uncompleted step with arrow icon. When all done: "Dismiss" button.

**Dismiss:** Persisted to `localStorage` key `agentmail-checklist-dismissed-{orgId}`.

---

## 14. Authentication & Organization Management

**Auth provider:** Clerk

**Routes:**
- `/sign-in/[[...sign-in]]` — Sign in page
- `/sign-up/[[...sign-up]]` — Sign up page
- `/select-organization` — Org picker
- `/create-organization` — Create new org
- `/auto-create-organization` — Auto-create on first login

**Auth guards (dashboard layout):**
- No `userId` → redirect to `/sign-in`
- No `orgId` → redirect to `/select-organization`

**Org profile dialog:** Full-screen Clerk `OrganizationProfile` overlay. Closes on Escape or backdrop click.

**SSO:** Vercel SSO callback at `/sso/vercel/callback`.

---

## 15. Common User Questions by UI Section

### Overview

| Question | Answer |
|----------|--------|
| "What does the Overview page show?" | A summary dashboard with an email activity chart (24h/7d/30d), recent threads preview, resource usage (inboxes and domains with limits), bounce/complaint rates, and an onboarding checklist for new users. |
| "Why do I see 'Upgrade' on the Domains card?" | Your plan has a domain limit of 0 (free tier). Upgrade to Developer or Startup to use custom domains. |
| "What do the colored arrows mean in the stats?" | Green up arrows mean a metric improved. Red up arrows on bounce/complaint/reject mean those got worse. The comparison is against the previous equivalent period. |

### Inboxes

| Question | Answer |
|----------|--------|
| "How do I create an inbox?" | Click "Create Inbox" on the Inboxes page. Username is optional (auto-generated if blank). Choose a domain (agentmail.to by default, or a verified custom domain). |
| "What's the Unified Inbox?" | It shows threads from all your inboxes in one view. Access it via the "Unified Inbox" button on the Inboxes list page. |
| "Can I change an inbox email address?" | No. You can only update the Display Name. To change the address, delete the inbox and create a new one. |
| "Where is SMTP/IMAP setup?" | Click "SMTP/IMAP" on the Inboxes page. Enter your API key to populate credentials. Supports Generic, Smartlead, and Instantly export formats. You can also export as CSV. |
| "What email folders are available?" | Inbox, Starred, Sent, Drafts, Important, Scheduled, All Mail, Spam, and Trash (Trash is not available in Unified Inbox). |
| "How do I compose an email?" | Open an inbox, then click the "Compose" button in the inbox sidebar. Fill in To, Subject, and Body. Cc/Bcc are available as toggle buttons. |
| "What's the max attachment size?" | 25 MB per file. |

### Domains

| Question | Answer |
|----------|--------|
| "How do I add a custom domain?" | Click "Create Domain" on the Domains page. Enter your domain name. After creation, DNS records (MX, CNAME, TXT) are generated. Add them to your DNS provider. |
| "What DNS records do I need?" | The console shows the exact records. Typically: MX record for receiving, CNAME for DKIM, TXT for SPF and verification. You can download a BIND zone file. |
| "My domain is stuck on 'verifying'." | If it's been more than an hour, click "Verify Domain" to trigger a re-check. Check that all DNS records are correctly configured. Some DNS providers take up to 48 hours to propagate. |
| "Why can't I add domains on the free plan?" | Custom domains are a premium feature. Upgrade to Developer ($20/mo) or Startup ($200/mo). |
| "What does 'Feedback Enabled' mean?" | When enabled, bounce and complaint feedback is processed for deliverability monitoring. It's automatically enabled for new domains. |

### Webhooks

| Question | Answer |
|----------|--------|
| "How do I set up webhooks?" | Go to the Webhooks page. The UI is powered by Svix. Click to add an endpoint, select event types, and provide your URL. |
| "The webhook portal won't load." | Try clicking "Try Again". If it persists, check your network connection. The portal is hosted by Svix and loaded in an iframe. |

### API Keys

| Question | Answer |
|----------|--------|
| "I lost my API key. Can I see it again?" | No. API keys are shown only once at creation. You must create a new one and delete the old one. |
| "What's the difference between Org and Pod scope?" | Org-scoped keys can access all resources. Pod-scoped keys can only access resources within that specific pod. |
| "What does the masked key format mean?" | The display shows the key prefix followed by bullets (e.g., `am_us_abc•••••••••••••`). The prefix helps identify the key without revealing it. |

### Allow/Block Lists

| Question | Answer |
|----------|--------|
| "What are Allow/Block Lists?" | Four lists that control email filtering: Receive Allow, Receive Block, Send Allow, and Send Block. Enter email addresses or full domains. |
| "What's the Reason column?" | Block lists optionally show a reason (e.g., "Spam sender"). Allow lists don't have reasons. |
| "Can I add a whole domain?" | Yes. Enter just the domain (e.g., `example.com`) instead of a full email address. |

### Metrics

| Question | Answer |
|----------|--------|
| "What time ranges are available?" | Last 24 hours, Last 7 days, and Last 30 days. |
| "Can I change the timezone?" | Yes. Click the timezone selector in the top-right of the Metrics page. 12 common timezones are available, plus your browser's timezone if it's different. |
| "What's the Health Score?" | A 0-100 score reflecting your overall email sending health. Levels: Excellent, Good, Average, Concerning, Critical. |
| "What does the Failure Heatmap show?" | A 7-day × 24-hour grid showing when email failures occur. Darker cells = more failures. Useful for identifying patterns. |
| "No metrics are showing." | Metrics appear after you start sending emails. If you've sent emails and still see nothing, try changing the time range or check your API key permissions. |

### Pods

| Question | Answer |
|----------|--------|
| "What are Pods?" | Pods are isolated workspaces for multi-tenant applications. Each pod has its own inboxes, domains, and API keys. |
| "Can I delete the default pod?" | No. The default pod cannot be deleted. Other pods can be deleted if empty. |
| "How do I scope an API key to a pod?" | When creating an API key, select the pod from the Scope dropdown. Or create the key from within the pod's API Keys tab. |

### Upgrade / Billing

| Question | Answer |
|----------|--------|
| "How do I upgrade?" | Go to the Upgrade page (sidebar org dropdown → "Upgrade Plan", or `/dashboard/upgrade`). Select a plan and complete checkout via Stripe. |
| "How do I manage my subscription?" | Org dropdown → "Manage Subscription" (opens Stripe customer portal). |
| "My checkout was cancelled." | A yellow banner will confirm cancellation. You can try again anytime from the Upgrade page. |

---

## 16. Troubleshooting

### Page/Loading Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Blank page after login | Missing org selection | Navigate to `/select-organization` and pick or create an org |
| "Loading..." spinner that never resolves | API connectivity issue | Check network tab for failed requests. Verify API key is valid. |
| Webhook portal not loading | Svix portal URL fetch failure | Click "Try Again". Check network/firewall for iframe restrictions. |
| Breadcrumbs show raw IDs instead of names | Data still loading or not found | Wait for data to load. If persistent, the resource may have been deleted. |

### Domain Verification

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Domain stuck on "Not Started" | DNS records not yet configured | Add all DNS records shown in the records table to your DNS provider. |
| Domain stuck on "verifying" > 1 hour | DNS propagation delay or misconfigured records | Click "Verify Domain" to force re-check. Double-check records match exactly. DNS can take up to 48 hours. |
| "FAILED" status | DNS records incorrect or missing | Compare each record in the table against your DNS config. Common issues: wrong CNAME target, missing TXT value, split DKIM string. |
| Zone file won't import | Some registrars (e.g., Namecheap) don't support bulk import | Paste records individually. See tooltip in the records dialog. |
| Verify button disabled with countdown | 5-minute cooldown between verification attempts | Wait for the countdown. The cooldown is stored in localStorage. |

### Create Operations

| Symptom | Cause | Resolution |
|---------|-------|------------|
| "This inbox address already exists" | Inbox email already in your org | Choose a different username or domain. |
| "This inbox address is already taken" | Another org owns that address | Choose a different username. |
| "You have reached your inbox limit" | Plan limit exceeded | Delete unused inboxes or upgrade your plan. |
| "Domain is malformed" | Invalid domain format | Check for missing dots, multiple consecutive dots, or short TLD. |
| "Name is required" (API key) | Empty name field | Enter a descriptive name for the key. |

### Billing

| Symptom | Cause | Resolution |
|---------|-------|------------|
| "Creating checkout..." hangs | Stripe API timeout | Retry. Check network connectivity. |
| Redirected to dashboard after clicking upgrade | Already has a Stripe subscription | Use "Manage Subscription" in org dropdown to access Stripe portal. |
| Premium banner won't dismiss | Not dismissible by design (for limit=0 features) | Upgrade plan to remove the banner. |

### Known Limitations

- **Dark mode only** — No light mode toggle. The console forces dark mode.
- **No global search** — There is no global search across resources. Use per-section tables.
- **No keyboard shortcuts** — No documented keyboard shortcuts for navigation.
- **Webhook UI is external** — The webhook management portal is an embedded Svix iframe; AgentMail cannot customize its internal behavior.
- **Pagination shows no total count** — The pagination bar shows "X to Y" but does not display total items or total pages.
- **Compose not available in Unified Inbox** — The Compose button is a no-op in unified view; you must open a specific inbox to compose.
- **Trash not available in Unified Inbox** — The Unified sidebar has 8 items; the Trash folder is only available in single-inbox views.

---

*Report generated from source code analysis of `agentmail-web/apps/console/` (Next.js 16 App Router, React 19, component files, route structure). Cross-referenced with official documentation at docs.agentmail.to. Last validated: 2026-03-07.*
