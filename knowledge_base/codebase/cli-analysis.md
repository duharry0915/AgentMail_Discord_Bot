# AgentMail CLI — Knowledge Base Research Report

> **Last updated:** 2026-03-07
> **Source directory:** `agentmail-cli/`
> **npm package:** [`agentmail-cli`](https://www.npmjs.com/package/agentmail-cli)
> **GitHub:** [`agentmail-to/agentmail-cli`](https://github.com/agentmail-to/agentmail-cli)

---

## Table of Contents

1. [Conclusion Summary](#1-conclusion-summary)
2. [CLI Overview](#2-cli-overview)
3. [Installation](#3-installation)
4. [Authentication](#4-authentication)
5. [Command Reference](#5-command-reference)
   - [Inboxes](#51-inboxes)
   - [Messages](#52-messages)
   - [Threads](#53-threads)
   - [Drafts](#54-drafts)
   - [Pods](#55-pods)
   - [Webhooks](#56-webhooks)
   - [Domains](#57-domains)
   - [API Keys](#58-api-keys)
   - [Metrics](#59-metrics)
   - [Organizations](#510-organizations)
6. [Global Flags & Output Formats](#6-global-flags--output-formats)
7. [Technical Architecture](#7-technical-architecture)
8. [Distribution & Platform Support](#8-distribution--platform-support)
9. [Related Tools Users May Confuse with the CLI](#9-related-tools-users-may-confuse-with-the-cli)
10. [Alternatives for Users Who Cannot Use the CLI](#10-alternatives-for-users-who-cannot-use-the-cli)
11. [Common Support Issues](#11-common-support-issues)

---

## 1. Conclusion Summary

**AgentMail has an official CLI.** It is called `agentmail-cli`, written in Go, distributed primarily via npm, and provides full command-line access to the AgentMail API.

| Question | Answer |
|----------|--------|
| Does an official CLI exist? | **Yes** |
| Package name | `agentmail-cli` (npm), `agentmail` (binary name) |
| Latest npm version | 0.7.1 (as of 2026-03-06) |
| Source code version | 0.6.0 |
| Language | Go |
| License | Apache-2.0 |
| Official docs page | [docs.agentmail.to/integrations/cli](https://docs.agentmail.to/integrations/cli) |
| Is it on PyPI? | **No** — only the Python SDK is on PyPI |
| Is it on GitHub? | **Yes** — [github.com/agentmail-to/agentmail-cli](https://github.com/agentmail-to/agentmail-cli) |

---

## 2. CLI Overview

The `agentmail` CLI provides direct terminal access to the AgentMail API. It follows a `resource subcommand` pattern with colon-delimited subresources:

```
agentmail [resource] <command> [flags...]
agentmail [resource]:[subresource] <command> [flags...]
```

Examples:

```bash
agentmail inboxes list
agentmail inboxes:messages send --inbox-id my-agent@agentmail.to --to "user@example.com" --subject "Hello" --text "Hi there"
agentmail pods:threads list --pod-id pod_xxx
```

---

## 3. Installation

### Via npm (recommended)

```bash
npm install -g agentmail-cli
```

Requires Node.js >= 16. The npm package is a thin wrapper that downloads the appropriate native Go binary for your platform during `postinstall`.

### Via Homebrew (macOS/Linux)

```bash
brew install agentmail-to/tap/agentmail
```

### Via GitHub Releases

Download the binary directly from [github.com/agentmail-to/agentmail-cli/releases](https://github.com/agentmail-to/agentmail-cli/releases). Available formats:

| Platform | Format |
|----------|--------|
| macOS (amd64, arm64) | `.zip` |
| Linux (386, arm, amd64, arm64) | `.tar.gz` |
| Windows (386, amd64, arm64) | `.zip` |

### Via Linux Package Managers

Packages are available in: `.apk`, `.deb`, `.rpm`, `.termux.deb`, `.archlinux`

### Verify Installation

```bash
agentmail --version
```

---

## 4. Authentication

The CLI requires an AgentMail API key, obtainable from [console.agentmail.to](https://console.agentmail.to).

**Option 1 — Environment variable (recommended):**

```bash
export AGENTMAIL_API_KEY=am_us_xxxxxxxxxxxx
agentmail inboxes list
```

**Option 2 — Per-command flag:**

```bash
agentmail inboxes list --api-key am_us_xxxxxxxxxxxx
```

---

## 5. Command Reference

### 5.1 Inboxes

```bash
# Create an inbox
agentmail inboxes create --display-name "My Agent" --username myagent --domain example.com

# List all inboxes
agentmail inboxes list

# Get inbox details
agentmail inboxes retrieve --inbox-id <inbox_id>

# Update an inbox
agentmail inboxes update --inbox-id <inbox_id> --display-name "New Name"

# Delete an inbox
agentmail inboxes delete --inbox-id <inbox_id>

# Get inbox metrics
agentmail inboxes metrics --inbox-id <inbox_id>
```

### 5.2 Messages

```bash
# Send a message
agentmail inboxes:messages send --inbox-id <inbox_id> \
  --to "recipient@example.com" \
  --subject "Hello" \
  --text "Message body"

# Send with HTML
agentmail inboxes:messages send --inbox-id <inbox_id> \
  --to "recipient@example.com" \
  --subject "Hello" \
  --html "<h1>Hello</h1>"

# List messages in an inbox
agentmail inboxes:messages list --inbox-id <inbox_id>

# Get a specific message
agentmail inboxes:messages retrieve --inbox-id <inbox_id> --message-id <message_id>

# Update message labels
agentmail inboxes:messages update --inbox-id <inbox_id> --message-id <message_id>

# Reply to a message
agentmail inboxes:messages reply --inbox-id <inbox_id> --message-id <message_id> \
  --text "Reply body"

# Reply all
agentmail inboxes:messages reply-all --inbox-id <inbox_id> --message-id <message_id> \
  --text "Reply body"

# Forward a message
agentmail inboxes:messages forward --inbox-id <inbox_id> --message-id <message_id> \
  --to "someone@example.com"

# Get raw message
agentmail inboxes:messages get-raw --inbox-id <inbox_id> --message-id <message_id>

# Get attachment
agentmail inboxes:messages get-attachment --inbox-id <inbox_id> --message-id <message_id> --attachment-id <attachment_id>
```

### 5.3 Threads

```bash
# List threads in an inbox
agentmail inboxes:threads list --inbox-id <inbox_id>

# Get thread details
agentmail inboxes:threads retrieve --inbox-id <inbox_id> --thread-id <thread_id>

# Delete a thread
agentmail inboxes:threads delete --inbox-id <inbox_id> --thread-id <thread_id>

# Get thread attachment
agentmail inboxes:threads get-attachment --inbox-id <inbox_id> --thread-id <thread_id> --attachment-id <attachment_id>

# List all threads org-wide
agentmail threads list
```

### 5.4 Drafts

```bash
# Create a draft
agentmail inboxes:drafts create --inbox-id <inbox_id> \
  --to "recipient@example.com" \
  --subject "Draft" \
  --text "Draft body"

# List drafts
agentmail inboxes:drafts list --inbox-id <inbox_id>

# Get a draft
agentmail inboxes:drafts retrieve --inbox-id <inbox_id> --draft-id <draft_id>

# Update a draft
agentmail inboxes:drafts update --inbox-id <inbox_id> --draft-id <draft_id>

# Send a draft
agentmail inboxes:drafts send --inbox-id <inbox_id> --draft-id <draft_id>

# Delete a draft
agentmail inboxes:drafts delete --inbox-id <inbox_id> --draft-id <draft_id>
```

### 5.5 Pods

```bash
# Create a pod
agentmail pods create --name "My Pod"

# List pods
agentmail pods list

# Get pod details
agentmail pods retrieve --pod-id <pod_id>

# Delete a pod (must be empty)
agentmail pods delete --pod-id <pod_id>

# Pod subresources
agentmail pods:inboxes create --pod-id <pod_id> --display-name "Pod Inbox"
agentmail pods:inboxes list --pod-id <pod_id>
agentmail pods:threads list --pod-id <pod_id>
agentmail pods:drafts list --pod-id <pod_id>
agentmail pods:domains list --pod-id <pod_id>
```

### 5.6 Webhooks

```bash
# Create a webhook
agentmail webhooks create --url "https://example.com/webhook" --event-type message.received

# List webhooks
agentmail webhooks list

# Get webhook details
agentmail webhooks retrieve --webhook-id <webhook_id>

# Update a webhook
agentmail webhooks update --webhook-id <webhook_id>

# Delete a webhook
agentmail webhooks delete --webhook-id <webhook_id>
```

### 5.7 Domains

```bash
# Add a custom domain
agentmail domains create --domain example.com --feedback-enabled false

# List domains
agentmail domains list

# Get domain details
agentmail domains retrieve --domain-id <domain_id>

# Verify domain DNS
agentmail domains verify --domain-id <domain_id>

# Get DNS zone file (records to configure)
agentmail domains get-zone-file --domain-id <domain_id>

# Delete a domain
agentmail domains delete --domain-id <domain_id>
```

### 5.8 API Keys

```bash
agentmail api-keys create
agentmail api-keys list
agentmail api-keys delete --api-key-id <api_key_id>
```

### 5.9 Metrics

```bash
agentmail metrics
```

### 5.10 Organizations

```bash
agentmail organizations retrieve
```

---

## 6. Global Flags & Output Formats

### Global Flags

All commands support these flags:

| Flag | Env Variable | Description |
|------|-------------|-------------|
| `--api-key` | `AGENTMAIL_API_KEY` | API key for authentication |
| `--base-url` | — | Override API base URL |
| `--environment` | — | Set API environment |
| `--format` | — | Output format (see below) |
| `--format-error` | — | Error output format |
| `--transform` | — | GJSON transformation expression for output |
| `--transform-error` | — | GJSON transformation for errors |
| `--debug` | — | Enable debug logging |
| `--help` | — | Show help |
| `--version` | — | Show version |

### Output Formats

Use `--format <format>` to control output:

| Format | Description |
|--------|-------------|
| `json` | JSON (default) |
| `pretty` | Human-readable pretty-printed output |
| `yaml` | YAML format |
| `jsonl` | JSON Lines (one object per line) |
| `raw` | Raw API response |
| `explore` | Interactive explorer |

### Data Querying with GJSON

Use `--transform` to extract specific fields using [GJSON](https://github.com/tidwall/gjson) syntax:

```bash
# Get just inbox IDs
agentmail inboxes list --transform "inboxes.#.inbox_id"

# Get first message subject
agentmail inboxes:messages list --inbox-id <id> --transform "messages.0.subject"
```

---

## 7. Technical Architecture

### Language & Framework

- **Language:** Go 1.25
- **CLI framework:** [urfave/cli/v3](https://github.com/urfave/cli)
- **API client:** `agentmail-go` (official Go SDK)
- **JSON querying:** [tidwall/gjson](https://github.com/tidwall/gjson)
- **Code generation:** OpenAPI spec via [Stainless](https://www.stainless.com/)

### Project Structure

```
agentmail-cli/
├── cmd/agentmail/main.go       # Entry point
├── pkg/cmd/                    # Command implementations (41 .go files)
├── internal/
│   ├── apiquery/               # API query handling
│   ├── autocomplete/           # Shell completion support (bash, zsh, fish)
│   ├── binaryparam/            # Binary parameter handling
│   ├── debugmiddleware/        # Debug logging
│   ├── apiform/                # Form encoding
│   ├── requestflag/            # Request flag handling
│   ├── mocktest/               # Mock testing utilities
│   └── jsonview/               # JSON visualization
├── npm/                        # npm package wrapper
├── scripts/                    # Build & utility scripts
├── .goreleaser.yml             # Multi-platform release config
└── SKILL.md                    # AgentSkills integration doc
```

### Shell Completions

The CLI generates shell completions for bash, zsh, and fish during the build process. Man pages are also generated automatically.

---

## 8. Distribution & Platform Support

### Build Targets (GoReleaser)

| Platform | Architectures | Format | Signing |
|----------|--------------|--------|---------|
| macOS | amd64, arm64 | .zip | Code-signed + notarized |
| Linux | 386, arm, amd64, arm64 | .tar.gz | — |
| Windows | 386, amd64, arm64 | .zip | — |

### Package Channels

| Channel | Command | Notes |
|---------|---------|-------|
| **npm** | `npm install -g agentmail-cli` | Downloads native binary via postinstall |
| **Homebrew** | `brew install agentmail-to/tap/agentmail` | Via `homebrew-tap` repo |
| **apt/deb** | `.deb` package from releases | Debian/Ubuntu |
| **rpm** | `.rpm` package from releases | Fedora/RHEL |
| **apk** | `.apk` package from releases | Alpine |
| **Arch Linux** | `.archlinux` package from releases | AUR-compatible |
| **Termux** | `.termux.deb` from releases | Android terminal |
| **GitHub Releases** | Direct binary download | All platforms |

---

## 9. Related Tools Users May Confuse with the CLI

### Smithery CLI (`npx @smithery/cli`)

```bash
npx @smithery/cli@latest mcp add agentmail
```

**This is NOT the AgentMail CLI.** The Smithery CLI is a generic tool for installing and managing MCP servers across AI clients (Claude Desktop, Cursor, etc.). Running the above command installs the **AgentMail MCP Server** — it does not install or invoke the `agentmail` CLI binary.

| | AgentMail CLI (`agentmail-cli`) | Smithery CLI (`@smithery/cli`) |
|---|---|---|
| **Purpose** | Human-operated command-line tool for the AgentMail API | MCP server installation and management |
| **Audience** | Developers, operators, scripts | AI client users setting up tool integrations |
| **Output** | JSON, YAML, pretty-printed data | MCP server configuration |
| **Runs** | Directly in terminal | Inside an AI client (Claude, Cursor) |

### AgentMail MCP Server (`agentmail-mcp`)

```bash
npx -y agentmail-mcp
```

**This is NOT the AgentMail CLI.** This is an MCP server that exposes AgentMail operations as tools for AI agents. It communicates over stdio with MCP-compatible clients — it is not a human-facing terminal tool. See the [MCP analysis report](mcp-analysis.md) for details.

### AgentMail SDKs

The Python SDK (`pip install agentmail`) and Node SDK (`npm install agentmail`) are programmatic libraries — they do not provide a `agentmail` command. Users looking for terminal-based access should use the CLI.

---

## 10. Alternatives for Users Who Cannot Use the CLI

While the official CLI is the recommended approach, these alternatives work for users in restricted environments.

### Direct REST API (curl)

```bash
# Set API key
export AGENTMAIL_API_KEY=am_us_xxxxxxxxxxxx

# List inboxes
curl -s -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  https://api.agentmail.to/v0/inboxes | jq

# Create inbox
curl -s -X POST -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username": "my-agent", "display_name": "My Agent"}' \
  https://api.agentmail.to/v0/inboxes | jq

# Send email
curl -s -X POST -H "Authorization: Bearer $AGENTMAIL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["user@example.com"],
    "subject": "Hello",
    "text": "Message body"
  }' \
  https://api.agentmail.to/v0/inboxes/<inbox_id>/messages | jq
```

### Python SDK Quick Scripts

```python
from agentmail import AgentMail

client = AgentMail()  # reads AGENTMAIL_API_KEY from env

# List inboxes (CLI equivalent: agentmail inboxes list)
for inbox in client.inboxes.list().inboxes:
    print(f"{inbox.inbox_id} — {inbox.display_name}")

# Send email (CLI equivalent: agentmail inboxes:messages send)
client.inboxes.messages.send(
    inbox_id="agent@agentmail.to",
    to=["user@example.com"],
    subject="Hello",
    text="Message body",
    html="<p>Message body</p>"
)

# List threads (CLI equivalent: agentmail inboxes:threads list)
for thread in client.inboxes.threads.list(inbox_id="agent@agentmail.to").threads:
    print(f"{thread.thread_id} — {thread.subject}")
```

### TypeScript SDK Quick Scripts

```typescript
import { AgentMailClient } from "agentmail";

const client = new AgentMailClient(); // reads AGENTMAIL_API_KEY from env

// List inboxes
const { inboxes } = await client.inboxes.list();
inboxes.forEach(i => console.log(`${i.inboxId} — ${i.displayName}`));

// Send email
await client.inboxes.messages.send("agent@agentmail.to", {
  to: ["user@example.com"],
  subject: "Hello",
  text: "Message body",
  html: "<p>Message body</p>"
});
```

### MCP via Cursor / Claude Desktop

For AI-assisted workflows, configure the AgentMail MCP server in your AI client and use natural language:

```
"List my AgentMail inboxes"
"Send an email from support@agentmail.to to user@example.com saying hello"
```

See the [MCP analysis report](mcp-analysis.md) for setup instructions.

---

## 11. Common Support Issues

### Installation

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `npm install -g agentmail-cli` fails | Node.js < 16 or network issues | Upgrade Node.js to >= 16; check proxy/firewall settings |
| Binary not found after install | PATH not updated | Run `npm bin -g` to find install location; add to PATH |
| Permission error on install | Global npm permissions | Use `sudo npm install -g agentmail-cli` or fix npm prefix |
| Homebrew formula not found | Tap not added | Run `brew tap agentmail-to/tap` first |

### Authentication

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `401 Unauthorized` | Invalid or missing API key | Verify key at [console.agentmail.to](https://console.agentmail.to); check `AGENTMAIL_API_KEY` env var |
| API key works in SDK but not CLI | Key not exported to shell | Ensure `export AGENTMAIL_API_KEY=...` is in your shell profile |

### Usage

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Unknown command error | Typo in resource/subcommand | Run `agentmail --help` for command list; note colon syntax for subresources (e.g., `inboxes:messages`) |
| Empty output | No results match query | Try without filters; check `--format pretty` for human-readable output |
| JSON parse errors in scripts | Using `pretty` format in pipes | Use `--format json` (default) when piping to `jq` or other tools |
| `--transform` not working | Invalid GJSON path | Test your GJSON expression at [gjson.dev](https://gjson.dev/) |

### Discord Support Quick Answers

**Q: "Does AgentMail have a CLI?"**
> Yes! Install it with `npm install -g agentmail-cli`, then authenticate with `export AGENTMAIL_API_KEY=<your-key>`. Run `agentmail --help` to see all commands. Docs: https://docs.agentmail.to/integrations/cli

**Q: "What's the difference between `agentmail-cli` and `agentmail-mcp`?"**
> `agentmail-cli` is a traditional command-line tool you run in your terminal. `agentmail-mcp` is an MCP server that gives AI assistants (Claude, Cursor) access to AgentMail operations. Different tools, different audiences.

**Q: "Can I use the CLI in CI/CD pipelines?"**
> Yes. Install via npm, set `AGENTMAIL_API_KEY` as a secret, and use `--format json` for machine-readable output. Pipe through `jq` or use `--transform` for field extraction.

---

*Report generated from source code analysis of `agentmail-cli/` (Go source, npm package, GoReleaser config) and cross-referenced with npm registry, GitHub, and official documentation.*
