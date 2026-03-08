# AgentMail MCP Server — Knowledge Base Research Report

> **Last updated:** 2026-03-07
> **Source directory:** `agentmail-smithery-mcp/`
> **Companion CLI package:** `agentmail-mcp` (npm: `agentmail-mcp`)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Package Details](#2-package-details)
3. [Architecture](#3-architecture)
4. [Configuration & Running](#4-configuration--running)
   - [Environment Variables](#41-environment-variables)
   - [Smithery Installation](#42-smithery-installation)
   - [Selective Tool Enablement](#43-selective-tool-enablement---tools-flag)
   - [Client Configuration Examples](#44-client-configuration-examples)
5. [Available MCP Tools](#5-available-mcp-tools)
   - [Tool Summary Table](#51-tool-summary-table)
   - [Tool Reference](#52-tool-reference)
6. [Attachment Handling](#6-attachment-handling)
7. [Error Handling](#7-error-handling)
8. [Common Support Issues](#8-common-support-issues)
9. [Appendix: Project Structure](#9-appendix-project-structure)

---

## 1. Overview

The **AgentMail MCP Server** exposes AgentMail's email API as a set of [Model Context Protocol](https://modelcontextprotocol.io) (MCP) tools, allowing any MCP-compatible AI client to manage inboxes, threads, messages, and attachments through natural language.

There are **two distribution channels**:

| Distribution | Package | Transport | Filtering |
|---|---|---|---|
| **CLI (npx)** | `agentmail-mcp` (v0.2.1) | stdio | `--tools` flag |
| **Smithery (hosted)** | `agentmail-mcp-server` (v1.0.0) | HTTP (Streamable) | Smithery UI |

**Supported MCP clients:** Claude Desktop, Claude Code, Cursor, Windsurf, Cline, and any client implementing the MCP specification.

**Relationship to AgentMail API:** The MCP server wraps the [`agentmail`](https://www.npmjs.com/package/agentmail) Node.js SDK (v0.2.1) via `agentmail-toolkit` (v0.2.0), which provides pre-built MCP tool definitions. The server itself is a thin registration layer — all business logic lives in `agentmail-toolkit/mcp`.

---

## 2. Package Details

### Smithery MCP (`agentmail-smithery-mcp/`)

```
Name:    agentmail-mcp-server
Version: 1.0.0
Runtime: TypeScript (via Smithery)
Entry:   src/index.ts
```

**Key dependencies:**

| Package | Version | Purpose |
|---|---|---|
| `@modelcontextprotocol/sdk` | ^1.24.1 | Core MCP protocol implementation |
| `@smithery/sdk` | ^4.0.1 | Smithery platform SDK |
| `agentmail` | ^0.2.1 | AgentMail API client |
| `agentmail-toolkit` | ^0.2.0 | Pre-built MCP tool definitions |
| `zod` | ^4.1.13 | Schema validation |

### CLI MCP (`agentmail-mcp` — npm published)

```
Name:    agentmail-mcp
Version: 0.2.1
License: MIT
Binary:  agentmail-mcp (via npx -y agentmail-mcp)
Repo:    https://github.com/agentmail-to/agentmail-mcp
```

---

## 3. Architecture

### Smithery MCP — Server Factory Pattern

```
src/index.ts (21 lines)
│
├── configSchema (Zod)          ← validates { apiKey: string }
│
└── createServer({ config })    ← factory, called per-session
    ├── new McpServer("AgentMail", "1.0.0")
    ├── new AgentMailClient({ apiKey })
    ├── new AgentMailToolkit(client)
    └── for tool of toolkit.getTools()
        └── server.registerTool(tool.name, tool, tool.callback)
```

Each client connection triggers a fresh `createServer()` call — sessions are isolated with their own API key and client instance.

### CLI MCP — stdio Transport

```
src/index.ts (41 lines)
│
├── parseToolsArg()             ← reads --tools from argv
├── process.env.AGENTMAIL_BASE_URL
├── process.env.AGENTMAIL_API_KEY  (read by agentmail SDK)
│
└── main()
    ├── new AgentMailClient({ baseUrl })
    ├── new AgentMailToolkit(client)
    ├── new McpServer("AgentMail", "0.1.0")
    ├── new StdioServerTransport()
    ├── register filtered/all tools
    └── server.connect(transport)
```

Uses stdio transport — communicates over stdin/stdout with the host process.

### Tool Registration Flow

```
Client connects with apiKey
  → configSchema validates apiKey
    → AgentMailClient initialized
      → AgentMailToolkit wraps client
        → toolkit.getTools([filter]) returns tool objects
          → server.registerTool() for each tool
            → Client can invoke tools via MCP protocol
```

---

## 4. Configuration & Running

### 4.1 Environment Variables

| Variable | Required | Default | Used By | Description |
|---|---|---|---|---|
| `AGENTMAIL_API_KEY` | **Yes** (CLI) | — | `agentmail-mcp` | API key from [console.agentmail.to](https://console.agentmail.to) |
| `AGENTMAIL_BASE_URL` | No | `https://api.agentmail.to` | `agentmail-mcp` | Custom API endpoint override |

**Smithery MCP** does not use environment variables — the API key is passed per-session via the Zod config schema (`config.apiKey`).

### 4.2 Smithery Installation

**Via Smithery CLI:**

```bash
npx @smithery/cli@latest mcp add agentmail
```

This registers the AgentMail MCP server with the Smithery platform. The user provides their API key through Smithery's configuration UI.

**Via npx (CLI MCP):**

```bash
npx -y agentmail-mcp
```

Runs the CLI MCP server directly. Requires `AGENTMAIL_API_KEY` in the environment.

**Local development (Smithery):**

```bash
cd agentmail-smithery-mcp/
npm install
npm run dev     # Starts dev server at http://127.0.0.1:8081
npm run build   # Creates bundle in .smithery/
```

The Smithery dev server exposes a playground at `http://localhost:8081` for interactive tool testing.

### 4.3 Selective Tool Enablement (`--tools` flag)

**CLI MCP only.** The `--tools` flag accepts a comma-separated list of tool names to register. If omitted, all tools are registered.

```bash
# Only expose read tools
npx -y agentmail-mcp --tools list_inboxes,get_inbox,list_threads,get_thread

# Only expose message tools
npx -y agentmail-mcp --tools send_message,reply_to_message,get_attachment
```

**Implementation** (`agentmail-mcp/src/index.ts:8-21`):

```typescript
const parseToolsArg = () => {
    const args = process.argv.slice(2)
    const toolsIndex = args.indexOf('--tools')
    if (toolsIndex === -1) return undefined
    const toolsArg = args[toolsIndex + 1]
    if (!toolsArg) {
        console.error('Error: --tools flag requires a comma-separated list of tool names')
        process.exit(1)
    }
    return toolsArg.split(',').map((tool) => tool.trim())
}
```

Filtered names are passed to `toolkit.getTools(toolNames)`, which only returns matching tools.

**Smithery MCP** does not implement `--tools` — all 10 tools are always registered. Selective enablement is handled at the Smithery platform level.

### 4.4 Client Configuration Examples

#### Claude Desktop

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "AgentMail": {
      "command": "npx",
      "args": ["-y", "agentmail-mcp"],
      "env": {
        "AGENTMAIL_API_KEY": "am_live_xxxxxxxxxxxx"
      }
    }
  }
}
```

With selective tools:

```json
{
  "mcpServers": {
    "AgentMail": {
      "command": "npx",
      "args": ["-y", "agentmail-mcp", "--tools", "list_inboxes,send_message,reply_to_message"],
      "env": {
        "AGENTMAIL_API_KEY": "am_live_xxxxxxxxxxxx"
      }
    }
  }
}
```

#### Cursor

**Location:** `.cursor/mcp.json` in workspace root, or global settings

```json
{
  "mcpServers": {
    "AgentMail": {
      "command": "npx",
      "args": ["-y", "agentmail-mcp"],
      "env": {
        "AGENTMAIL_API_KEY": "am_live_xxxxxxxxxxxx"
      }
    }
  }
}
```

#### Windsurf

```json
{
  "mcpServers": {
    "AgentMail": {
      "command": "npx",
      "args": ["-y", "agentmail-mcp"],
      "env": {
        "AGENTMAIL_API_KEY": "am_live_xxxxxxxxxxxx"
      }
    }
  }
}
```

#### Claude Code

```json
{
  "mcpServers": {
    "AgentMail": {
      "command": "npx",
      "args": ["-y", "agentmail-mcp"],
      "env": {
        "AGENTMAIL_API_KEY": "am_live_xxxxxxxxxxxx"
      }
    }
  }
}
```

---

## 5. Available MCP Tools

### 5.1 Tool Summary Table

| # | Tool | Type | Description | Destructive | Idempotent |
|---|---|---|---|---|---|
| 1 | `list_inboxes` | Read | List all inboxes in the organization | No | Yes |
| 2 | `get_inbox` | Read | Get details of a specific inbox | No | Yes |
| 3 | `create_inbox` | Write | Create a new inbox | No | No |
| 4 | `delete_inbox` | Write | Delete an inbox permanently | **Yes** | Yes |
| 5 | `list_threads` | Read | List threads in an inbox (with filters) | No | Yes |
| 6 | `get_thread` | Read | Get thread details with messages | No | Yes |
| 7 | `get_attachment` | Read | Download and extract attachment text | No | Yes |
| 8 | `send_message` | Write | Send a new email from an inbox | No | No |
| 9 | `reply_to_message` | Write | Reply to an existing message | No | No |
| 10 | `update_message` | Write | Update message labels | No | Yes |

### 5.2 Tool Reference

---

#### `list_inboxes`

**Description:** List inboxes
**Annotations:** `readOnlyHint: true`, `openWorldHint: false`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | number | No | 10 | Maximum number of inboxes to return |
| `pageToken` | string | No | — | Pagination token from previous response |

**Example use case:** "Show me all my inboxes" / Agent startup to discover available inboxes.

**API call:** `client.inboxes.list({ limit, pageToken })`

---

#### `get_inbox`

**Description:** Get inbox details
**Annotations:** `readOnlyHint: true`, `openWorldHint: false`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the inbox (e.g., `agent@agentmail.to`) |

**Example use case:** "What's the status of inbox agent@agentmail.to?"

**API call:** `client.inboxes.get(inboxId)`

---

#### `create_inbox`

**Description:** Create inbox
**Annotations:** `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: false`, `openWorldHint: false`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `username` | string | No | — | Username part of the email address |
| `domain` | string | No | — | Domain for the inbox |
| `displayName` | string | No | — | Display name for the inbox |

**Example use case:** "Create a new inbox called support-bot" → creates `support-bot@agentmail.to`

**API call:** `client.inboxes.create({ username, domain, displayName })`

---

#### `delete_inbox`

**Description:** Delete inbox
**Annotations:** `readOnlyHint: false`, `destructiveHint: true`, `idempotentHint: true`, `openWorldHint: false`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the inbox to delete |

**Example use case:** "Delete the test inbox"

**API call:** `client.inboxes.delete(inboxId)`

> **Warning:** This is a destructive operation. The inbox and all its data are permanently removed.

---

#### `list_threads`

**Description:** List threads in inbox
**Annotations:** `readOnlyHint: true`, `openWorldHint: true`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the inbox |
| `limit` | number | No | 10 | Maximum number of threads to return |
| `pageToken` | string | No | — | Pagination token |
| `labels` | string[] | No | — | Filter threads by labels |
| `before` | string (ISO 8601) | No | — | Filter threads before this datetime |
| `after` | string (ISO 8601) | No | — | Filter threads after this datetime |

**Example use case:** "Show me unread threads from today" → `labels: ["unread"], after: "2026-03-07T00:00:00Z"`

**API call:** `client.inboxes.threads.list(inboxId, { limit, pageToken, labels, before, after })`

---

#### `get_thread`

**Description:** Get thread details
**Annotations:** `readOnlyHint: true`, `openWorldHint: true`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the inbox |
| `threadId` | string | **Yes** | — | ID of the thread |

**Example use case:** "Show me the full conversation in thread X"

**API call:** `client.inboxes.threads.get(inboxId, threadId)`

---

#### `get_attachment`

**Description:** Get attachment (supports PDF and DOCX extraction)
**Annotations:** `readOnlyHint: true`, `openWorldHint: true`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the inbox |
| `threadId` | string | **Yes** | — | ID of the thread |
| `attachmentId` | string | **Yes** | — | ID of the attachment |

**Example use case:** "Read the PDF attached to that email"

**API call:** Downloads the file via `client.threads.getAttachment(threadId, attachmentId)`, then extracts text content (see [Section 6](#6-attachment-handling)).

**Returns:** `{ text: string, fileType: string }` on success, `{ error: string, fileType: string }` on failure.

---

#### `send_message`

**Description:** Send message
**Annotations:** `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: false`, `openWorldHint: true`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the sending inbox |
| `to` | string[] | **Yes** | — | Recipient email addresses |
| `cc` | string[] | No | — | CC recipients |
| `bcc` | string[] | No | — | BCC recipients |
| `subject` | string | No | — | Email subject line |
| `text` | string | No | — | Plain text body |
| `html` | string | No | — | HTML body |
| `labels` | string[] | No | — | Labels to apply to the sent message |

**Example use case:** "Send a welcome email to user@example.com from support@agentmail.to"

**API call:** `client.inboxes.messages.send(inboxId, { to, cc, bcc, subject, text, html, labels })`

---

#### `reply_to_message`

**Description:** Reply to message
**Annotations:** `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: false`, `openWorldHint: true`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the inbox |
| `messageId` | string | **Yes** | — | ID of the message to reply to |
| `text` | string | No | — | Plain text body |
| `html` | string | No | — | HTML body |
| `labels` | string[] | No | — | Labels to apply |
| `replyAll` | boolean | No | — | Reply to all recipients |

**Example use case:** "Reply to that customer saying we'll look into it"

**API call:** `client.inboxes.messages.reply(inboxId, messageId, { text, html, labels, replyAll })`

---

#### `update_message`

**Description:** Update message (labels)
**Annotations:** `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: true`, `openWorldHint: false`

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `inboxId` | string | **Yes** | — | ID of the inbox |
| `messageId` | string | **Yes** | — | ID of the message |
| `addLabels` | string[] | No | — | Labels to add |
| `removeLabels` | string[] | No | — | Labels to remove |

**Example use case:** "Mark that email as processed and remove the unread label"

**API call:** `client.inboxes.messages.update(inboxId, messageId, { addLabels, removeLabels })`

---

## 6. Attachment Handling

The `get_attachment` tool downloads and extracts text from email attachments. Supported file types are detected via magic bytes:

| File Type | Magic Bytes | Library Used | Output |
|---|---|---|---|
| PDF | `%PDF` (`[37, 80, 68, 70]`) | `unpdf` (`getDocumentProxy` + `extractText`) | Extracted text joined by newlines |
| DOCX | `PK\x03\x04` (`[80, 75, 3, 4]`) | `JSZip` (parse ZIP → `word/document.xml`) | XML tags stripped, entities decoded |
| Other | — | — | Error: `"Unsupported file type"` |

**Processing flow:**

```
1. client.threads.getAttachment(threadId, attachmentId) → { downloadUrl }
2. fetch(downloadUrl) → ArrayBuffer → Uint8Array
3. Detect type via first 4 bytes
4. PDF:  unpdf.getDocumentProxy(bytes) → extractText → join("\n")
   DOCX: JSZip.loadAsync(bytes) → zip.file("word/document.xml") → strip XML tags
5. Return { text, fileType } or { error, fileType }
```

**DOCX entity decoding handles:** `&lt;`, `&gt;`, `&amp;`, `&quot;`, `&apos;`

---

## 7. Error Handling

### Toolkit-Level Error Wrapping

All tool callbacks are wrapped in a `safeFunc` pattern within `agentmail-toolkit`:

```typescript
const safeFunc = async (func, client, args) => {
  try {
    return { isError: false, result: await func(client, args) }
  } catch (error) {
    if (error instanceof Error)
      return { isError: true, result: error.message }
    else
      return { isError: true, result: "Unknown error" }
  }
}
```

**MCP response format (all tools):**

```json
{
  "content": [
    { "type": "text", "text": "<JSON-stringified result or error message>" }
  ],
  "isError": false
}
```

On failure:

```json
{
  "content": [
    { "type": "text", "text": "Request failed: 401 Unauthorized" }
  ],
  "isError": true
}
```

### CLI-Level Error Handling

```typescript
// Missing --tools argument
console.error('Error: --tools flag requires a comma-separated list of tool names')
process.exit(1)

// Unhandled errors
main().catch((error) => {
    console.error(error)
    process.exit(1)
})
```

---

## 8. Common Support Issues

### 8.1 Connection Failures

| Symptom | Cause | Resolution |
|---|---|---|
| Server fails to start | Missing `AGENTMAIL_API_KEY` | Set the env var in your MCP client config |
| `ENOENT: npx not found` | Node.js not installed or not in PATH | Install Node.js (v18+) and ensure `npx` is accessible |
| `ERR_MODULE_NOT_FOUND` | Corrupted npx cache | Run `npx -y agentmail-mcp` (the `-y` flag ensures fresh install) |
| Timeout on first launch | npx downloading packages | Normal on first run; subsequent launches are faster |
| `Connection refused` (Smithery) | Dev server not running | Run `npm run dev` in the `agentmail-smithery-mcp/` directory |

### 8.2 Missing or Invalid API Key

| Symptom | Cause | Resolution |
|---|---|---|
| `401 Unauthorized` on every tool call | Invalid or expired API key | Generate a new key at [console.agentmail.to](https://console.agentmail.to) |
| Tools register but all return errors | API key not passed to client | **CLI:** Ensure `AGENTMAIL_API_KEY` is in the `env` block. **Smithery:** Ensure key is set in config UI |
| `configSchema` validation error | Empty or missing `apiKey` in Smithery config | Provide the key in the Smithery configuration panel |

### 8.3 Tool Call Errors

| Symptom | Cause | Resolution |
|---|---|---|
| `"Unknown error"` | Unhandled exception in toolkit | Check API key validity; inspect server logs |
| `"Unsupported file type"` from `get_attachment` | Attachment is not PDF or DOCX | Only PDF and DOCX text extraction is supported |
| `list_threads` returns empty | No threads match filters | Check `labels`, `before`, `after` parameters; remove filters to verify |
| `send_message` fails | Recipient address bounced/blocked | AgentMail permanently blocks bounced addresses; use a different recipient |
| `--tools` flag error | Missing comma-separated list | Provide tool names: `--tools list_inboxes,send_message` |

### 8.4 Integration Steps — Cursor

1. Open Cursor Settings → MCP Servers (or edit `.cursor/mcp.json`)
2. Add an MCP server with command `npx` and args `["-y", "agentmail-mcp"]`
3. Set `AGENTMAIL_API_KEY` in the environment variables section
4. Restart Cursor or reload the MCP server connection
5. Verify by asking the AI to "list my AgentMail inboxes"

### 8.5 Integration Steps — Claude Desktop

1. Open the Claude Desktop config file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
2. Add the `AgentMail` entry under `mcpServers` (see [Section 4.4](#44-client-configuration-examples))
3. Restart Claude Desktop
4. The AgentMail tools should appear in the tools panel
5. Test with: "List my AgentMail inboxes"

### 8.6 Integration Steps — Smithery (Hosted)

1. Run `npx @smithery/cli@latest mcp add agentmail`
2. Enter your API key when prompted
3. The server is registered with Smithery and available to connected clients
4. No local process management required — Smithery handles hosting

---

## 9. Appendix: Project Structure

### `agentmail-smithery-mcp/`

```
agentmail-smithery-mcp/
├── src/
│   └── index.ts              # Server factory (21 lines) — entry point
├── package.json              # agentmail-mcp-server v1.0.0
├── smithery.yaml             # runtime: typescript
├── smithery.config.js        # esbuild: external @napi-rs/canvas
├── README.md                 # Basic setup docs
├── AGENTS.md                 # Comprehensive dev guide (515 lines)
├── .prettierrc               # Code style config
└── pnpm-lock.yaml            # Dependency lock
```

### `agentmail-mcp/` (CLI — reference only)

```
agentmail-mcp/
├── src/
│   └── index.ts              # CLI server with --tools flag (41 lines)
├── build/
│   └── index.js              # Compiled entry (bin: agentmail-mcp)
├── package.json              # agentmail-mcp v0.2.1
└── tsconfig.json             # TypeScript config
```

### MCP Tool Annotations Reference

| Annotation | Meaning |
|---|---|
| `readOnlyHint: true` | Tool does not modify data |
| `destructiveHint: true` | Tool permanently deletes data |
| `idempotentHint: true` | Safe to retry without side effects |
| `openWorldHint: true` | Accesses external/live email data |

---

*Report generated from source code analysis of `agentmail-smithery-mcp/` and `agentmail-mcp/` packages.*
