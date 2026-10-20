# Multi-Agent Orchestrator

A robust Python-based multi-agent task planning, execution, and verification system backed by SQLite persistence.

## Features
- **Task Planning (`PlannerAgent`)**: Breaks down high-level user goals into structured sub-tasks assigned to specialized agents.
- **Specialized Execution (`SpecializedAgent`)**: Handles domain-specific tasks such as research, coding, and writing documentation.
- **Verification & Retry (`VerifierAgent`)**: Evaluates task outcomes with automated quality checks and retry limits.
- **SQLite Persistence**: Maintains durable state across execution cycles, tracking task status (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`), attempts, and results.

## Getting Started

### Prerequisites
- Python 3.8+

### Running the Orchestrator
Execute the script with a custom goal:
```bash
python orchestrator.py "Build a real-time chat application in Python"
```

## Architecture
```
[User Goal] ---> [PlannerAgent] ---> (SQLite Tasks Table)
                                          |
        +---------------------------------+
        |
        v
[SpecializedAgent] ---> [VerifierAgent] ---> [Completed / Retry]
```