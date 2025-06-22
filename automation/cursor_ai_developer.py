#!/usr/bin/env python3
"""
Cursor AI Developer - Automated Development Agent for ChatCPG v2
This script orchestrates continuous development using Cursor AI through file-based workflows.
No OpenAI API costs - leverages your existing Cursor AI subscription.
"""

import os
import json
import time
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class CursorAIDeveloper:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.development_plan = self.load_development_plan()
        self.logs_dir = self.project_root / "automation" / "logs"
        self.cursor_workspace = self.project_root / ".cursor_workspace"
        self.pending_tasks_dir = self.cursor_workspace / "pending_tasks"
        self.completed_tasks_dir = self.cursor_workspace / "completed_tasks"
        self.current_task_dir = self.cursor_workspace / "current_task"
        
        # Create directories
        self.logs_dir.mkdir(exist_ok=True)
        self.cursor_workspace.mkdir(exist_ok=True)
        self.pending_tasks_dir.mkdir(exist_ok=True)
        self.completed_tasks_dir.mkdir(exist_ok=True)
        self.current_task_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        self.log_file = self.logs_dir / f"cursor_ai_developer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def load_development_plan(self) -> Dict:
        """Load the development plan from JSON file"""
        plan_file = self.project_root / "development_plan.json"
        if not plan_file.exists():
            raise FileNotFoundError(f"Development plan not found: {plan_file}")
        
        with open(plan_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_development_plan(self):
        """Save the updated development plan"""
        plan_file = self.project_root / "development_plan.json"
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(self.development_plan, f, indent=2)
    
    def get_current_task(self) -> Optional[Dict]:
        """Get the current task to work on"""
        current_task_id = self.development_plan.get("current_task")
        
        for phase in self.development_plan["phases"]:
            for task in phase["tasks"]:
                if task["id"] == current_task_id and task.get("status") != "completed":
                    return task
        
        # If current task is completed, find next pending task
        for phase in self.development_plan["phases"]:
            for task in phase["tasks"]:
                if task.get("status") == "pending":
                    # Check if dependencies are met
                    if self.are_dependencies_met(task):
                        self.development_plan["current_task"] = task["id"]
                        self.save_development_plan()
                        return task
        
        return None
    
    def are_dependencies_met(self, task: Dict) -> bool:
        """Check if all task dependencies are completed"""
        dependencies = task.get("dependencies", [])
        
        for phase in self.development_plan["phases"]:
            for dep_task in phase["tasks"]:
                if dep_task["id"] in dependencies and dep_task.get("status") != "completed":
                    return False
        
        return True
    
    def create_cursor_task_instruction(self, task: Dict) -> str:
        """Create a comprehensive task instruction for Cursor AI"""
        return f"""# 🚀 ChatCPG v2 Development Task

## Task Overview
**Task ID:** {task['id']}
**Task Name:** {task['name']}
**Status:** {task.get('status', 'pending')}

## 📋 Description
{task['description']}

## ✅ Requirements
{chr(10).join(f"- {req}" for req in task['requirements'])}

## 📁 Files to Create/Modify
{chr(10).join(f"- `{file}`" for file in task['files'])}

## 🎯 Expected Output
{task['expected_output']}

## 🏗️ Project Context
- **Project:** {self.development_plan['project']}
- **Version:** {self.development_plan['version']}
- **Description:** {self.development_plan['description']}

## 🛠️ Technical Guidelines
- Use modern Python/TypeScript best practices
- Include comprehensive error handling and logging
- Add proper type hints and documentation
- Implement security best practices
- Follow the existing project architecture
- Write testable, maintainable code
- Include unit tests where appropriate

## 📂 Project Structure
```
chatcpg_v2/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── automation/       # AI development automation
├── docs/            # Documentation
└── tests/           # Test suites
```

## 🎨 Implementation Instructions

**Please implement this task by:**

1. **Creating/modifying the specified files** with complete, production-ready code
2. **Following the exact file paths** specified in the "Files to Create/Modify" section
3. **Including proper imports, error handling, and documentation**
4. **Adding any necessary configuration or setup files**
5. **Creating corresponding test files** in the `tests/` directory

## 💡 AI Assistant Instructions

When you're ready to implement this task:

1. Open Cursor AI (Cmd/Ctrl + K)
2. Reference this instruction file
3. Create each file specified in the "Files to Create/Modify" section
4. Ensure all code follows the technical guidelines
5. Test the implementation locally
6. Save all files and mark the task as completed

## 📝 Completion Checklist

- [ ] All specified files created/modified
- [ ] Code follows best practices
- [ ] Proper error handling implemented
- [ ] Documentation added
- [ ] Tests created (if applicable)
- [ ] Local testing completed
- [ ] Ready for integration

---
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** ChatCPG v2 - AI-Powered Business Solution Platform
"""
    
    def prepare_cursor_task(self, task: Dict) -> str:
        """Prepare a task for Cursor AI implementation"""
        self.log(f"Preparing Cursor task: {task['name']}")
        
        # Create task instruction file
        task_instruction = self.create_cursor_task_instruction(task)
        task_file = self.current_task_dir / f"TASK_{task['id']}_INSTRUCTIONS.md"
        
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(task_instruction)
        
        # Create a task context file with existing codebase info
        context_file = self.current_task_dir / f"TASK_{task['id']}_CONTEXT.md"
        context_content = self.create_task_context(task)
        
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(context_content)
        
        # Create a completion tracking file
        completion_file = self.current_task_dir / f"TASK_{task['id']}_COMPLETION.json"
        completion_data = {
            "task_id": task['id'],
            "task_name": task['name'],
            "status": "prepared",
            "created_at": datetime.now().isoformat(),
            "files_to_create": task['files'],
            "completed_files": [],
            "ready_for_review": False
        }
        
        with open(completion_file, 'w', encoding='utf-8') as f:
            json.dump(completion_data, f, indent=2)
        
        self.log(f"Task prepared for Cursor AI: {task_file}")
        return str(task_file)
    
    def create_task_context(self, task: Dict) -> str:
        """Create context information for the task"""
        context = f"""# 🔍 Task Context for {task['name']}

## Current Project State

### Existing Files
"""
        
        # Scan for existing relevant files
        relevant_extensions = ['.py', '.js', '.ts', '.tsx', '.json', '.yaml', '.yml', '.md']
        existing_files = []
        
        for ext in relevant_extensions:
            files = list(self.project_root.glob(f"**/*{ext}"))
            for file in files:
                if not any(skip in str(file) for skip in ['.git', 'node_modules', '__pycache__', '.cursor_workspace']):
                    rel_path = file.relative_to(self.project_root)
                    existing_files.append(str(rel_path))
        
        for file in sorted(existing_files):
            context += f"- `{file}`\n"
        
        context += f"""
### Dependencies
- Check existing `requirements.txt`, `package.json`, or `pyproject.toml` for current dependencies
- Add new dependencies as needed for this task

### Architecture Notes
- Backend: FastAPI with SQLAlchemy/Pydantic
- Frontend: Next.js with TypeScript
- Database: PostgreSQL (production), SQLite (development)
- Authentication: JWT-based
- Deployment: Docker containers

### Related Tasks
"""
        
        # Find related tasks
        for phase in self.development_plan["phases"]:
            for other_task in phase["tasks"]:
                if other_task["id"] != task["id"] and other_task.get("status") == "completed":
                    context += f"- ✅ {other_task['name']} (completed)\n"
                elif other_task["id"] != task["id"] and other_task.get("status") == "pending":
                    context += f"- ⏳ {other_task['name']} (pending)\n"
        
        return context
    
    def check_cursor_completion(self, task: Dict) -> bool:
        """Check if Cursor AI has completed the task"""
        completion_file = self.current_task_dir / f"TASK_{task['id']}_COMPLETION.json"
        
        if not completion_file.exists():
            return False
        
        try:
            with open(completion_file, 'r', encoding='utf-8') as f:
                completion_data = json.load(f)
            
            # Check if all required files exist
            all_files_exist = True
            for file_path in task['files']:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    all_files_exist = False
                    break
            
            # Update completion status
            if all_files_exist and completion_data.get("ready_for_review", False):
                return True
            
        except Exception as e:
            self.log(f"Error checking completion: {e}", "ERROR")
        
        return False
    
    def implement_task_with_cursor(self, task: Dict) -> bool:
        """Implement a task using Cursor AI workflow"""
        self.log(f"Starting Cursor AI implementation of task: {task['name']}")
        
        try:
            # 1. Prepare task for Cursor
            task_file = self.prepare_cursor_task(task)
            
            # 2. Open Cursor with the task
            self.open_cursor_with_task(task_file)
            
            # 3. Wait for user to complete task in Cursor
            self.log("⏳ Waiting for task completion in Cursor AI...")
            self.log(f"📂 Task instructions available at: {task_file}")
            self.log("🎯 Please complete the task in Cursor and mark it as ready for review")
            
            # 4. Interactive monitoring for completion
            print("\n" + "="*60)
            print(f"🎯 IMPLEMENTING: {task['name']}")
            print("="*60)
            print(f"📂 Task file: {task_file}")
            print("📋 Instructions:")
            print("1. Open Cursor AI and navigate to the task file")
            print("2. Implement the required functionality")
            print("3. Test your implementation")
            print("4. When ready, type 'completed' below")
            print("="*60)
            
            while True:
                user_input = input("\nTask status (completed/skip/failed): ").strip().lower()
                
                if user_input == "completed":
                    # Check if files exist
                    all_files_exist = True
                    missing_files = []
                    
                    for file_path in task['files']:
                        full_path = self.project_root / file_path
                        if not full_path.exists():
                            all_files_exist = False
                            missing_files.append(file_path)
                    
                    if all_files_exist:
                        self.log("✅ Task completed successfully in Cursor AI")
                        return True
                    else:
                        print(f"❌ Missing files: {missing_files}")
                        print("Please create the required files and try again.")
                        continue
                
                elif user_input == "skip":
                    self.log("⏭️ Task skipped by user")
                    return False
                
                elif user_input == "failed":
                    self.log("❌ Task marked as failed by user")
                    return False
                
                else:
                    print("Invalid input. Please type 'completed', 'skip', or 'failed'")
            
        except Exception as e:
            self.log(f"Error in Cursor implementation: {e}", "ERROR")
            return False
    
    def open_cursor_with_task(self, task_file: str):
        """Open Cursor with the task file"""
        try:
            # Try to open Cursor with the task file
            if shutil.which("cursor"):
                subprocess.run(['cursor', str(self.project_root)], check=False)
                subprocess.run(['cursor', task_file], check=False)
                self.log("📂 Opened Cursor with task file")
            else:
                self.log("Cursor CLI not found. Please open Cursor manually.", "WARNING")
                self.log(f"Task file location: {task_file}")
                
        except Exception as e:
            self.log(f"Error opening Cursor: {e}", "WARNING")
    
    def run_tests(self) -> bool:
        """Run automated tests"""
        try:
            # Try to run pytest if available
            result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/', '-v'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("Tests passed successfully")
                return True
            else:
                self.log(f"Tests failed: {result.stderr}", "WARNING")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Tests timed out", "WARNING")
            return False
        except Exception as e:
            self.log(f"Error running tests: {e}", "WARNING")
            return False
    
    def commit_changes(self, task: Dict):
        """Commit changes to git"""
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], cwd=self.project_root, check=True)
            
            # Commit with descriptive message
            commit_message = f"Cursor AI Implementation: {task['name']} - {task['id']}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.project_root,
                check=True
            )
            
            self.log(f"Committed changes for task: {task['name']}")
            
        except subprocess.CalledProcessError as e:
            self.log(f"Git commit failed: {e}", "WARNING")
    
    def prepare_all_tasks(self, max_tasks: int = 5):
        """Prepare multiple tasks for Cursor AI"""
        self.log(f"Preparing up to {max_tasks} tasks for Cursor AI")
        
        prepared_count = 0
        for phase in self.development_plan["phases"]:
            for task in phase["tasks"]:
                if task.get("status") == "pending" and self.are_dependencies_met(task):
                    if prepared_count >= max_tasks:
                        break
                    
                    # Prepare task in pending_tasks directory
                    task_file = self.pending_tasks_dir / f"TASK_{task['id']}_INSTRUCTIONS.md"
                    context_file = self.pending_tasks_dir / f"TASK_{task['id']}_CONTEXT.md"
                    
                    with open(task_file, 'w', encoding='utf-8') as f:
                        f.write(self.create_cursor_task_instruction(task))
                    
                    with open(context_file, 'w', encoding='utf-8') as f:
                        f.write(self.create_task_context(task))
                    
                    self.log(f"Prepared task: {task['name']}")
                    prepared_count += 1
            
            if prepared_count >= max_tasks:
                break
        
        self.log(f"Prepared {prepared_count} tasks for Cursor AI")
        return prepared_count
    
    def interactive_development_loop(self):
        """Interactive development loop with Cursor AI"""
        self.log("Starting Cursor AI interactive development loop")
        
        while True:
            try:
                # Get current task
                current_task = self.get_current_task()
                
                if not current_task:
                    self.log("No pending tasks found. Development completed!")
                    break
                
                self.log(f"Current task: {current_task['name']} ({current_task['id']})")
                
                # Present options to user
                print("\n" + "="*60)
                print(f"TASK: {current_task['name']}")
                print("="*60)
                print("1. Implement with Cursor AI")
                print("2. Skip this task")
                print("3. Mark as completed manually")
                print("4. Show project status")
                print("5. Exit")
                print("="*60)
                
                choice = input("\nSelect option (1-5): ").strip()
                
                if choice == "1":
                    print(f"Task: {current_task['name']}")
                    print(f"Description: {current_task['description']}")
                    print(f"Files to create: {', '.join(current_task['files'])}")
                    
                    completed = input("\nMark as completed? (y/n): ").strip().lower()
                    if completed == 'y':
                        current_task["status"] = "completed"
                        current_task["completed_at"] = datetime.now().isoformat()
                        self.save_development_plan()
                        self.log(f"Task completed: {current_task['name']}")
                
                elif choice == "2":
                    self.log(f"Skipping task: {current_task['name']}")
                    current_task["status"] = "skipped"
                    self.save_development_plan()
                
                elif choice == "3":
                    current_task["status"] = "completed"
                    current_task["completed_at"] = datetime.now().isoformat()
                    self.save_development_plan()
                    self.log(f"Marked task as completed: {current_task['name']}")
                
                elif choice == "4":
                    status = self.status_report()
                    print(f"\nProject Status:")
                    print(f"Total Tasks: {status['total_tasks']}")
                    print(f"Completed: {status['completed_tasks']}")
                    print(f"Pending: {status['pending_tasks']}")
                    print(f"Progress: {status['completion_percentage']:.1f}%")
                
                elif choice == "5":
                    self.log("Development loop terminated by user")
                    break
                
                else:
                    print("Invalid option. Please try again.")
                
            except KeyboardInterrupt:
                self.log("Development interrupted by user")
                break
            except Exception as e:
                self.log(f"Error in development loop: {e}", "ERROR")
        
        self.log("Interactive development loop completed")
    
    def status_report(self) -> Dict:
        """Generate a status report"""
        total_tasks = 0
        completed_tasks = 0
        pending_tasks = 0
        failed_tasks = 0
        
        for phase in self.development_plan["phases"]:
            for task in phase["tasks"]:
                total_tasks += 1
                status = task.get("status", "pending")
                if status == "completed":
                    completed_tasks += 1
                elif status == "pending":
                    pending_tasks += 1
                elif status == "failed":
                    failed_tasks += 1
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "failed_tasks": failed_tasks,
            "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }

def main():
    """Main function"""
    print("Cursor AI Developer - ChatCPG v2")
    print("Zero OpenAI costs - Using your Cursor AI subscription")
    print("="*60)
    
    developer = CursorAIDeveloper()
    
    # Print initial status
    status = developer.status_report()
    print(f"Project Status: {status['completed_tasks']}/{status['total_tasks']} tasks completed ({status['completion_percentage']:.1f}%)")
    
    # Start interactive development
    developer.interactive_development_loop()
    
    # Print final status
    final_status = developer.status_report()
    print(f"Final Status: {final_status['completed_tasks']}/{final_status['total_tasks']} tasks completed ({final_status['completion_percentage']:.1f}%)")

if __name__ == "__main__":
    main() 