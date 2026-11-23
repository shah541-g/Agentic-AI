"""Main entry point: Distribute 20 tasks across a pool of 5 agents with SQLite tracking."""

import time
from database import ThreadSafeDatabase
from pool import AgentPool


def main():
    print("=" * 65)
    print("    CHALLENGE 3: THREAD-SAFE AGENT WORKER POOL (5 AGENTS / 20 TASKS)    ")
    print("=" * 65)

    db_path = "agent_pool.db"
    pool_size = 5
    num_tasks = 20

    # 1. Initialize Thread-safe Database and Agent Pool
    pool = AgentPool(size=pool_size, db_path=db_path)
    print(f"[*] Initialized pool with {pool_size} concurrent daemon agents.")

    # 2. Prepare 20 realistic agent tasks
    task_catalog = [
        "Ingest IEEE technical whitepaper on autonomous planning",
        "Scrape live pricing table from benchmark provider",
        "Compile Python script syntax check in sandbox",
        "Generate unit tests for vector similarity function",
        "Refactor database connector to use connection pool",
        "Execute prompt injection vulnerability scan",
        "Format report into GitHub-flavored Markdown",
        "Calculate token consumption metrics across runs",
        "Validate JSON schema for tool argument parser",
        "Simulate transient API failure with simulated error",
        "Optimize SQL indexes on conversation history table",
        "Verify cosine similarity math implementation",
        "Extract named entities from customer support transcript",
        "Format OpenAPI documentation for agent REST endpoints",
        "Aggregate RSS feeds from AI research laboratories",
        "Analyze memory leak in long-running streaming pipeline",
        "Generate Mermaid state diagram for multi-agent graph",
        "Sanitize user input against path traversal attacks",
        "Audit Dockerfile for non-root user security enforcement",
        "Finalize milestone deliverable package and changelog",
    ]

    # Pre-seed tasks in SQLite database
    seed_records = [(i + 1, f"Task-{i+1:02d}", task_catalog[i]) for i in range(num_tasks)]
    pool.db.seed_tasks(seed_records)
    print(f"[*] Pre-seeded {num_tasks} tasks in '{db_path}'.")

    # 3. Dispatch tasks into the thread-safe queue
    print("\n[*] Dispatching 20 tasks into queue.Queue()...\n")
    start_total = time.perf_counter()

    for task_id, task_name, payload in seed_records:
        pool.submit_task(task_id, task_name, payload)

    # 4. Wait for all tasks to complete cleanly
    pool.wait_completion()
    total_time = time.perf_counter() - start_total
    print(f"\n[+] All {num_tasks} tasks processed in {total_time:.2f} seconds.")

    # 5. Shut down pool threads gracefully
    pool.shutdown()
    print("[+] Agent pool shut down cleanly.")

    # 6. Print database summary tables
    print("\n" + "=" * 65)
    print("                  AGENT PERFORMANCE METRICS                     ")
    print("=" * 65)
    print(f"{'Agent Name':<25} | {'Completed':<10} | {'Failed':<8} | {'Total Time (s)':<14}")
    print("-" * 65)
    for row in pool.db.get_summary():
        print(f"{row['agent_name']:<25} | {row['tasks_completed']:<10} | {row['tasks_failed']:<8} | {row['total_runtime']:<14.2f}")

    print("\n" + "=" * 65)
    print("                  SAMPLE TASK EXECUTION LOGS                    ")
    print("=" * 65)
    all_tasks = pool.db.get_all_tasks()
    for task in all_tasks[:8]:
        status_flag = "[OK]" if task["status"] == "SUCCESS" else "[FAIL]"
        print(f"#{task['task_id']:02d} {status_flag} ({task['assigned_agent']}): {task['payload'][:45]}... [{task['duration_seconds']:.2f}s]")
    print(f"... and {len(all_tasks) - 8} more tasks recorded in '{db_path}'.")


if __name__ == "__main__":
    main()
