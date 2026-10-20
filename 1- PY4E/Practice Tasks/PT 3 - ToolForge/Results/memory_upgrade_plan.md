# Upgrade Plan: Integrating Long-Term Memory into Ali's Multi-Agent Orchestrator

## 1. Executive Summary
Ali's **Multi-Agent Orchestrator** currently relies on Python and SQLite to manage task planning, execution, and verification across specialized agents (planner, researcher, coder, verifier). While effective for single-session workflows, the system lacks long-term, episodic, and semantic memory capabilities. This upgrade plan outlines how to integrate a robust memory architecture into the existing SQLite-backed orchestrator to enable cross-session learning, historical task retrieval, and adaptive multi-agent collaboration.

---

## 2. Current Architecture vs. Target Architecture

| Dimension | Current State | Target State (Upgraded) |
| :--- | :--- | :--- |
| **Storage Layer** | Local SQLite for current task run execution state. | Expanded SQLite schema + Vector extension (`sqlite-vss`) or hybrid storage for embeddings. |
| **Memory Scope** | Intra-session working memory (ephemeral per run). | Cross-session episodic and semantic memory (persistent historical logs). |
| **Lifecycle Management** | Static task logging during execution. | Active agent-driven consolidation (summarization, reflection, pruning). |
| **Retrieval Mechanism** | Direct SQL queries on task IDs and statuses. | Semantic similarity search combined with relational filtering. |

---

## 3. Step-by-Step Upgrade Plan

### Step 1: Schema Expansion for Episodic & Semantic Memory
*   **Action:** Extend the existing SQLite database schema with new tables:
    *   `episodic_memory`: Stores complete task trajectories, agent rationales, successes, and failures.
    *   `semantic_memory`: Stores extracted domain knowledge, user preferences, and generalized facts.
    *   `memory_metadata`: Tracks access counts, creation timestamps, and relevance scores for lifecycle management.
*   **Implementation Note:** Keep SQLite lightweight by leveraging `sqlite-vss` or storing vector embeddings as BLOBs with cosine similarity helper functions in Python.

### Step 2: Implementing the Memory Lifecycle Pipeline
*   **Ingestion & Reflection:** After the Verifier agent successfully completes or fails a task, trigger a background reflection step where an LLM summarizes the execution trajectory and extracts key lessons.
*   **Consolidation:** Periodically distill working memory logs into compressed episodic records to prevent database bloat and keep context windows focused.
*   **Forgetting & Pruning:** Implement time-decay and utility-based scoring to archive or delete obsolete/redundant memories.

### Step 3: Agent Tool Integration
*   **Planner Enhancement:** Give the Planner agent access to a `search_past_episodes` tool so it can query historical orchestrations when confronted with novel or recurring user requests.
*   **Researcher Enhancement:** Allow the Researcher agent to query semantic memory for cached domain facts before triggering external web searches, reducing latency and token costs.

---

## 4. Short Checklist for Implementation

- [ ] **Design Schema:** Define SQLite tables for episodic trajectories and semantic facts with vector embedding support (`sqlite-vss` or BLOB storage).
- [ ] **Build Reflection Module:** Implement a post-execution summarization step in the Verifier agent to distill successful/failed runs into lessons.
- [ ] **Develop Retrieval Tools:** Create python functions for semantic and relational memory queries accessible by the Planner and Researcher agents.
- [ ] **Test Cross-Session Recall:** Run multi-step tasks across separate sessions to verify that past execution strategies improve current planning accuracy.
- [ ] **Implement Pruning & Maintenance:** Add utility scoring and time-decay routines to keep persistent storage lean and relevant.