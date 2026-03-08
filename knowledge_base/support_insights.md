# Support History Insights

This document summarizes key patterns, frequently asked questions, team responses, and known issues extracted from 843+ Discord support messages.

---

## Frequent Questions (Not in Current FAQs)

### 1. Threads vs Messages - When to Use Each
**Frequency:** Very High  
**User Question:** "What is the difference between messages and threads at the root level of the inbox? Should I expose a tool to my agent to list threads or messages?"

**Team Response:**
- Threads show conversations - they collapse every message belonging to a conversation into one object
- Messages are individual emails, each as its own object
- For inbox overview, use **list threads first**
- Use **list messages** when agent needs to act on email line-by-line (e.g., getting verification codes, scraping invoices)
- **Important:** List threads doesn't return full message bodies, so follow up with get message for full content

### 2. Minimum Toolset for AI Agents
**Frequency:** High  
**User Question:** "What's the minimum toolset needed for an agent to work with your APIs?"

**Team Response:**
1. `list_threads` - For inbox overview (doesn't include full message bodies)
2. `get_message` - To get full message content
3. `reply_to_message` - Use last message ID from thread
4. `send_message` - If no thread exists (starts new conversation)

### 3. Delete Emails/Inboxes Functionality
**Frequency:** High  
**User Question:** "Does the API support deleting emails or inboxes?"

**Team Response:**
- Delete functionality has been added (was not available initially)
- Use DELETE endpoints for inboxes, threads, and messages
- For old messages that might confuse agents, workaround was to spin up a new inbox

### 4. Webhook Verification with Svix
**Frequency:** High  
**User Question:** "How do I verify webhook signatures? Where do I find my secret?"

**Team Response:**
- Copy the secret from the dashboard (webhook details) or via GET webhook API endpoint
- Use the Svix library to verify webhook signatures
- Svix auth is optional but recommended for verifying sender identity
- The secret is shown when creating the webhook - save it immediately

### 5. Sandbox/Testing Environment
**Frequency:** Medium-High  
**User Question:** "Do you support a test or sandbox domain for integration tests?"

**Team Response:**
- No universal sandbox/testnet for email
- Workaround: Create dummy inboxes with AgentMail and send test emails between them
- Can request separate API key for development
- Working on dedicated environment that doesn't send actual emails

### 6. Labels for State Tracking
**Frequency:** Medium  
**User Question:** "How do I track if an agent has successfully handled particular emails?"

**Team Response:**
- Use **labels** - already part of the platform
- Set custom labels and filter on them in list endpoint
- Example: Add "processed", "handled", "pending" labels to messages
- Use `update_message` endpoint to add/remove labels
- Key-value metadata coming soon

### 7. Contexts Feature
**Frequency:** Medium  
**User Question:** "What are contexts for?"

**Team Response:**
- Flexible way to store arbitrary data that agents can reference
- Think of it like a crude memory layer
- Currently being tested with select customers
- Will be documented once stabilized
- Future: ability to search/query semantically related threads

### 8. Human-in-the-Loop Workflow
**Frequency:** Medium  
**User Question:** "Is there a good way for human-in-the-loop? Would be great to view emails with Gmail client."

**Team Response:**
- CC your Gmail in any email thread
- This keeps humans in the loop while agent handles automation

### 9. Email Deliverability & Warmup
**Frequency:** Medium  
**User Question:** "How do you handle warmup/spam prevention/deliverability monitoring?"

**Team Response:**
- AgentMail doesn't offer warmup as part of the service
- Compatible with warmup services like Instantly
- No open/click tracking (hurts deliverability with larger volumes)
- Best practices for deliverability:
  - Send 10-20 emails per inbox per day
  - Have 10-20 inboxes per domain
  - Use email warmup services
  - Have CTA to reply (builds reputation)
  - Minimize links
  - Avoid spammy content

### 10. Client ID Purpose
**Frequency:** Medium  
**User Question:** "Can I use client_id to store my user ID and get it in webhook events?"

**Team Response:**
- `client_id` is for **idempotent create requests** (not foreign key storage)
- If you create with same client_id twice, returns existing resource
- For webhook routing: call `get_inbox` with inbox_id to get client_id
- Metadata storage coming soon

### 11. Attachment Size Limits
**Frequency:** Medium  
**User Question:** "What are the attachment size limits?"

**Team Response:**
- 30 MB limit on size of entire email (including attachments)
- Large emails may be blocked entirely
- Lambda timeouts were increased to handle emails up to 30MB

### 12. Playground vs Production
**Frequency:** Medium  
**User Question:** "Why am I getting 403 Forbidden with my API key?"

**Team Response:**
- AgentMail Playground is an isolated environment with its own API key
- Playground keys are base64 encoded in cookies
- Use dashboard.agentmail.to for production environment
- Extract playground key: decode base64, use value inside quotation marks

---

## Code Examples Shared by Team

### Stripping HTML Line Breaks
When sending HTML emails, newline characters render as extra spacing:
```javascript
const str = `Hello
world!
This is a test.`;

const noBreaks = str.replace(/\n/g, '');
console.log(noBreaks); // "Helloworld!This is a test."
```
Note: AgentMail doesn't strip automatically because some customers use `\n` instead of `<p>` tags.

### Importing TypeScript Types from SDK
```typescript
import { AgentMail } from 'agentmail'
type Payload = AgentMail.webhooks.events.MessageReceivedPayload
```

### Running MCP Server
```bash
npx agentmail-mcp
```
Can pass `--tools` arg to select subset of tools.

---

## Known Issues & Workarounds

### 1. Uppercase Email Addresses
**Issue:** Emails sent to addresses with capital letters weren't being received  
**Cause:** Inbox lookup was case-sensitive  
**Fix:** Server now transforms email addresses to lowercase before processing  
**Workaround:** Always use lowercase email addresses

### 2. Large Attachment Processing
**Issue:** Emails with large attachments (near 30MB) weren't being received  
**Cause:** Lambda processing was timing out silently  
**Fix:** Increased Lambda timeouts  
**Current Limit:** 30 MB for entire email including attachments

### 3. West Coast Draft Sending
**Issue:** Sending drafts from west coast returned 500 errors  
**Cause:** Regional processing bug  
**Fix:** Fixed on server side (August 2025)

### 4. CloudFront SQL Injection False Positive
**Issue:** Reply endpoint blocked with "CloudFront blocked" error  
**Cause:** Message IDs looked like SQL injection attacks to WAF  
**Fix:** Rule disabled while investigating

### 5. Webhook 308 Redirect
**Issue:** Webhooks not being received, showing 308 status  
**Cause:** Trailing slash in webhook URL  
**Fix:** Remove trailing slash from webhook endpoint URL

### 6. Reply Validation Error
**Issue:** Reply endpoint required `to`/`cc`/`bcc` even when replying  
**Cause:** Validation rule touched replies unintentionally  
**Fix:** Server-side fix (no SDK update needed)

### 7. Attachments in us-west-1
**Issue:** S3 PermanentRedirect error when getting attachments  
**Cause:** Regional S3 bucket configuration  
**Fix:** Fixed server-side

### 8. Duplicate Emails from Gmail
**Issue:** Same email received multiple times  
**Status:** Under investigation (infrequent)

---

## User Confusion Points

### 1. "To" Field Must Be an Array
**Confusion:** Users pass single string for recipients  
**Reality:** The `to` field must be a list of strings, even for single recipient  
**Docs Issue:** Fern docs showed it accepts single or list - updated to require list only

### 2. Webhook Event Types Format
**Confusion:** What events to specify when creating webhooks  
**Reality:** Must include specific event types like `inbox: [message_received]`  
**Cannot be left empty**

### 3. Domain Verification Status
**Confusion:** Dashboard shows verified but API says missing  
**Reality:** DNS verification isn't automatically re-checked  
**Solution:** Team can manually trigger DNS check; button coming to dashboard

### 4. Getting Attachments
**Confusion:** How to download attachment content  
**Solution:** 
- Endpoint redirects to signed S3 URL
- Use curl with `-OLJ` flag to download as file
- Dashboard UI doesn't show attachments (being added)

### 5. Message ID Location
**Confusion:** Where to find message IDs in dashboard  
**Reality:** Dashboard doesn't show message IDs currently  
**Workaround:** Use API to list messages

---

## Feature Requests from Users

1. **Enable/disable webhooks** without recreating
2. **Test webhook events** - send example payloads
3. **Exclude inboxes from webhooks** (for dev/test inboxes)
4. **Pods for environment separation** (dev/prod like Stripe/Clerk)
5. **Postman collection** for API testing
6. **Delete endpoints** (now available)
7. **Raw EML download** (now available)
8. **Attachment text extraction** for LLMs (PDF, DOCX)
9. **Open/click tracking** (not planned - hurts deliverability)

---

## Team Members & Roles

- **simplehacker1313** - Community support, escalations, partnerships
- **haakam21** - Technical support, API fixes, feature development
- **mikesteroonie** - Support, hackathon assistance

---

## Response Patterns

### Typical Issue Resolution Flow
1. User reports issue
2. Team asks for message_id, inbox_id, or other identifiers
3. Team investigates logs
4. Fix deployed (often within minutes)
5. Confirmation sent to user

### Common Diagnostic Questions
- "What message_id?"
- "What inbox_id?"
- "What region are you in?" (west coast issues)
- "Are you using the production or playground environment?"
- "Can you show the full error message?"

---

## Statistics Summary

- **Total Messages Analyzed:** 843+
- **Time Period:** May 2025 - January 2026
- **Most Active Topics:** Webhooks, Threads/Messages, Domains, Attachments
- **Average Fix Time:** Minutes to hours for bugs, days for features
- **Most Common User Actions:** Creating inboxes, setting up webhooks, sending/receiving emails
