import sqlite3
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MultiAgentOrchestrator")

DB_PATH = "orchestrator.db"

def init_db():
    """Initializes the SQLite database with necessary tables for tasks and state."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            agent_type TEXT NOT NULL,
            status TEXT NOT NULL, -- PENDING, IN_PROGRESS, COMPLETED, FAILED
            result TEXT,
            attempt INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

class PlannerAgent:
    """Splits the high-level request into smaller specialized tasks."""
    def plan(self, goal: str):
        logger.info(f"Planner received goal: '{goal}'")
        # In a full LLM system, an LLM would break this down. Here we simulate a robust breakdown:
        if "web app" in goal.lower() or "application" in goal.lower():
            tasks = [
                {"agent_type": "researcher", "goal": f"Research best practices and architecture for: {goal}"},
                {"agent_type": "coder", "goal": f"Write the core Python code/modules for: {goal}"},
                {"agent_type": "writer", "goal": f"Write user documentation and README for: {goal}"}
            ]
        else:
            tasks = [
                {"agent_type": "researcher", "goal": f"Gather necessary info/data for: {goal}"},
                {"agent_type": "coder", "goal": f"Implement the solution/script for: {goal}"}
            ]
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for t in tasks:
            cursor.execute(
                "INSERT INTO tasks (goal, agent_type, status, attempt) VALUES (?, ?, 'PENDING', 0)",
                (t["goal"], t["agent_type"])
            )
        conn.commit()
        conn.close()
        logger.info(f"Planner created {len(tasks)} tasks in SQLite.")

class SpecializedAgent:
    """Executes tasks based on agent type (researcher, coder, writer)."""
    def execute(self, task_id: int, agent_type: str, goal: str) -> str:
        logger.info(f"Executing task {task_id} [{agent_type}]: {goal}")
        time.sleep(0.5) # Simulate processing time
        if agent_type == "researcher":
            return f"[RESEARCH RESULT] Found relevant documentation and optimal approaches for: {goal}"
        elif agent_type == "coder":
            return f"# [CODE RESULT]\n# Implementation for: {goal}\ndef solution():\n    print('Executing solution...')\n    return True"
        elif agent_type == "writer":
            return f"# [DOCUMENTATION]\n# Guide and README for: {goal}\nThis project successfully meets all requirements."
        else:
            return f"[GENERAL RESULT] Completed task: {goal}"

class VerifierAgent:
    """Verifies task results and decides whether to approve or retry."""
    def verify(self, task_id: int, result: str) -> bool:
        logger.info(f"Verifying result for task {task_id}...")
        if not result or len(result.strip()) < 10:
            return False
        # Simple heuristic verification check
        return True

def run_orchestrator(goal: str):
    init_db()
    
    # 1. Planning phase
    planner = PlannerAgent()
    planner.plan(goal)
    
    executor = SpecializedAgent()
    verifier = VerifierAgent()
    
    # 2. Execution & Verification loop
    while True:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, goal, agent_type, status, attempt FROM tasks WHERE status IN ('PENDING', 'FAILED') LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            break # No more pending/failed tasks
            
        task_id, task_goal, agent_type, status, attempt = row
        
        if attempt >= 3:
            logger.error(f"Task {task_id} exceeded maximum retry attempts. Marking as FAILED permanently.")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE tasks SET status = 'FAILED' WHERE id = ?", (task_id,))
            conn.commit()
            conn.close()
            continue
            
        # Update attempt and status
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = 'IN_PROGRESS', attempt = ? WHERE id = ?", (attempt + 1, task_id))
        conn.commit()
        conn.close()
        
        # Execute
        result = executor.execute(task_id, agent_type, task_goal)
        
        # Verify
        is_valid = verifier.verify(task_id, result)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if is_valid:
            logger.info(f"Task {task_id} VERIFIED successfully.")
            cursor.execute("UPDATE tasks SET status = 'COMPLETED', result = ? WHERE id = ?", (result, task_id))
        else:
            logger.warning(f"Task {task_id} verification failed. Will retry.")
            cursor.execute("UPDATE tasks SET status = 'FAILED', result = ? WHERE id = ?", (result, task_id))
        conn.commit()
        conn.close()

    # Summary report
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, goal, agent_type, status, result FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    
    logger.info("=== ORCHESTRATION SUMMARY ===")
    for t in tasks:
        logger.info(f"Task {t[0]} [{t[2]}]: {t[3]} - Goal: {t[1]}")
        if t[4]:
            logger.info(f"  Result snippet: {t[4][:80]}...")

if __name__ == "__main__":
    import sys
    user_goal = sys.argv[1] if len(sys.argv) > 1 else "Build a Python CLI tool for log analysis"
    run_orchestrator(user_goal)