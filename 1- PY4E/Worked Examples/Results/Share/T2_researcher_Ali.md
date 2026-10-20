<!-- Task T2: Research and document the APIs/libraries required for email fetching (IMAP/Gmail API), WhatsApp messaging (Twilio/Meta Cloud API), LinkedIn posting, and LLM integration. -->

### 1. Email Fetching

#### Option A: IMAP Protocol (Standard Email)
*   **Purpose:** Connecting to email providers (Gmail, Outlook, Yahoo, custom servers) to read, search, and fetch emails.
*   **Required Libraries:**
    *   **Python:** `imaplib` (built-in standard library), `email` (built-in standard library for parsing MIME messages). For higher-level abstractions, third-party libraries like `imap-tools` or `Mail-Parser` are commonly used.
    *   **Node.js / JavaScript:** `imap` or `node-imap`, `mailparser` (for parsing email bodies and attachments).
    *   **Go:** `github.com/emersion/go-imap` (comprehensive IMAP client/server library).

#### Option B: Gmail API (Google-Specific)
*   **Purpose:** Programmatic access to Gmail mailboxes via REST/JSON rather than raw IMAP, supporting advanced querying, labels, and threads.
*   **Required Libraries / SDKs:**
    *   **Python:** `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`.
    *   **Node.js / JavaScript:** `@googleapis/gmail`, `google-auth-library`.
    *   **Go:** `google.golang.org/api/gmail/v1`.
*   **Authentication Requirements:** OAuth 2.0 (for user mailboxes) or Service Accounts with Domain-Wide Delegation (for Google Workspace enterprise apps).

---

### 2. WhatsApp Messaging

#### Option A: Twilio API for WhatsApp
*   **Purpose:** Sending and receiving WhatsApp messages via Twilio’s unified communication abstraction layer.
*   **Required Libraries / SDKs:**
    *   **Python:** `twilio` (official PyPI package).
    *   **Node.js / JavaScript:** `twilio` (official npm package).
    *   **Go:** `github.com/twilio/twilio-go`.
*   **Requirements:** Twilio Account SID, Auth Token, and a configured WhatsApp Sender Number (Sandbox or Approved Business Profile).

#### Option B: Meta Cloud API (WhatsApp Business Platform)
*   **Purpose:** Direct integration with Meta’s official WhatsApp Business API for sending messages, media, and handling interactive components.
*   **Required Libraries / SDKs:**
    *   *Note:* Meta does not provide an official multi-language SDK; developers interact directly with the HTTP REST API using standard HTTP clients (e.g., `requests` in Python, `axios` in Node.js, `net/http` in Go).
    *   Community-maintained wrappers exist (e.g., `whatsapp-cloud-api` in Node.js), but official documentation recommends direct HTTP requests.
*   **Requirements:** Meta Developer Account, WhatsApp Business Account (WABA), Permanent Access Token, and Phone Number ID.

---

### 3. LinkedIn Posting

*   **Purpose:** Creating and publishing posts (text, images, articles) to personal profiles or company pages.
*   **API Endpoints:** LinkedIn Community Management API / Share on LinkedIn API (`/v2/ugcPosts` or `/v2/posts`).
*   **Required Libraries / SDKs:**
    *   *Note:* LinkedIn does not maintain an official, actively supported SDK for server-side posting. Integration is achieved via direct HTTP REST requests.
    *   **Python:** `requests`, `requests-oauthlib` (for OAuth 2.0 authentication flows).
    *   **Node.js / JavaScript:** `axios`, `oauth-1.5a` or standard OAuth 2.0 libraries.
*   **Authentication & Permissions:** OAuth 2.0 with scopes such as `w_member_social` (for personal profiles) or `w_organization_social` (for company pages). 
*   *Uncertainty/Caveat:* LinkedIn frequently deprecates and restricts its v2 APIs. Access to posting APIs often requires approval via specific LinkedIn Developer Products (e.g., "Share on LinkedIn" or "Community Management API").

---

### 4. LLM Integration

#### Option A: OpenAI API (GPT-4o, GPT-3.5, etc.)
*   **Purpose:** Text generation, summarization, intent classification, and function calling.
*   **Required Libraries / SDKs:**
    *   **Python:** `openai` (official OpenAI Python library).
    *   **Node.js / JavaScript:** `openai` (official OpenAI Node.js library).
    *   **Go:** `github.com/sashabaranov/go-openai` (popular community SDK).

#### Option B: Anthropic API (Claude 3.5 Sonnet, Haiku, etc.)
*   **Purpose:** Advanced reasoning, context analysis, and content generation.
*   **Required Libraries / SDKs:**
    *   **Python:** `anthropic` (official SDK).
    *   **Node.js / JavaScript:** `@anthropic-ai/sdk` (official SDK).

#### Option C: LangChain / LlamaIndex (Orchestration Frameworks)
*   **Purpose:** Building applications with LLMs through composable components (prompt management, memory, chains for connecting to emails/databases).
*   **Required Libraries / SDKs:**
    *   **Python:** `langchain`, `llama-index`.
    *   **Node.js / JavaScript:** `langchain` (Node package).
