#!/usr/bin/env python3
"""
AI Developer - Automated Development Agent for ChatCPG v2
This script orchestrates the continuous development of the ChatCPG v2 platform
using AI assistance and automated workflows.
"""

import os
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIDeveloper:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.development_plan = self.load_development_plan()
        self.logs_dir = self.project_root / "automation" / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize logging
        self.log_file = self.logs_dir / f"ai_developer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
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
    
    def generate_code(self, task: Dict) -> str:
        """Generate code for a specific task using AI"""
        self.log(f"Generating code for task: {task['name']}")
        
        # Create comprehensive prompt
        prompt = self.create_task_prompt(task)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.development_plan["ai_settings"]["model"],
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert full-stack developer working on ChatCPG v2, 
                        an AI-powered business solution platform. Generate production-ready code 
                        following best practices, including proper error handling, typing, 
                        documentation, and security considerations."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.development_plan["ai_settings"]["temperature"],
                max_tokens=self.development_plan["ai_settings"]["max_tokens"]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log(f"Error generating code: {e}", "ERROR")
            return ""
    
    def create_task_prompt(self, task: Dict) -> str:
        """Create a comprehensive prompt for the task"""
        return f"""
# Task: {task['name']}

## Description
{task['description']}

## Requirements
{chr(10).join(f"- {req}" for req in task['requirements'])}

## Files to Create/Modify
{chr(10).join(f"- {file}" for file in task['files'])}

## Expected Output
{task['expected_output']}

## Project Context
- Project: {self.development_plan['project']}
- Version: {self.development_plan['version']}
- Description: {self.development_plan['description']}

## Technical Guidelines
- Use modern Python/TypeScript best practices
- Include comprehensive error handling
- Add proper logging and monitoring
- Implement security best practices
- Follow the project architecture
- Include type hints and documentation
- Write testable, maintainable code

Please generate the complete code for all specified files. For each file, 
provide the full implementation with proper imports, error handling, and documentation.
Structure your response as:

## File: path/to/file.py
```python
# Complete file content here
```

## File: path/to/another_file.py
```python
# Complete file content here
```
"""
    
    def implement_task(self, task: Dict) -> bool:
        """Implement a specific task"""
        self.log(f"Starting implementation of task: {task['name']}")
        
        try:
            # Generate code using AI
            generated_code = self.generate_code(task)
            
            if not generated_code:
                self.log(f"Failed to generate code for task: {task['name']}", "ERROR")
                return False
            
            # Parse and save generated files
            success = self.parse_and_save_files(generated_code, task)
            
            if success:
                self.log(f"Successfully implemented task: {task['name']}")
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                self.save_development_plan()
                return True
            else:
                self.log(f"Failed to save files for task: {task['name']}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error implementing task {task['name']}: {e}", "ERROR")
            return False
    
    def parse_and_save_files(self, generated_code: str, task: Dict) -> bool:
        """Parse generated code and save to appropriate files"""
        try:
            # Simple parsing - look for file markers
            lines = generated_code.split('\n')
            current_file = None
            current_content = []
            
            for line in lines:
                if line.startswith("## File:"):
                    # Save previous file if exists
                    if current_file and current_content:
                        self.save_file(current_file, '\n'.join(current_content))
                    
                    # Start new file
                    current_file = line.replace("## File:", "").strip()
                    current_content = []
                    
                elif line.startswith("```") and current_file:
                    # Skip code block markers
                    continue
                    
                elif current_file:
                    current_content.append(line)
            
            # Save last file
            if current_file and current_content:
                self.save_file(current_file, '\n'.join(current_content))
            
            return True
            
        except Exception as e:
            self.log(f"Error parsing generated code: {e}", "ERROR")
            return False
    
    def save_file(self, file_path: str, content: str):
        """Save content to a file"""
        full_path = self.project_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.log(f"Created/updated file: {file_path}")
    
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
            commit_message = f"AI Implementation: {task['name']} - {task['id']}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.project_root,
                check=True
            )
            
            self.log(f"Committed changes for task: {task['name']}")
            
        except subprocess.CalledProcessError as e:
            self.log(f"Git commit failed: {e}", "WARNING")
    
    def continuous_development_loop(self):
        """Main development loop"""
        self.log("Starting continuous development loop")
        
        iteration = 0
        max_iterations = 50  # Prevent infinite loops
        
        while iteration < max_iterations:
            try:
                iteration += 1
                self.log(f"Development iteration {iteration}")
                
                # Get current task
                current_task = self.get_current_task()
                
                if not current_task:
                    self.log("No pending tasks found. Development completed!")
                    break
                
                self.log(f"Working on task: {current_task['name']} ({current_task['id']})")
                
                # Implement the task
                success = self.implement_task(current_task)
                
                if success:
                    # Run tests
                    tests_passed = self.run_tests()
                    
                    if tests_passed:
                        self.log("Tests passed - committing changes")
                        self.commit_changes(current_task)
                    else:
                        self.log("Tests failed - task needs revision", "WARNING")
                        current_task["status"] = "needs_revision"
                        self.save_development_plan()
                else:
                    self.log("Task implementation failed", "ERROR")
                    current_task["status"] = "failed"
                    self.save_development_plan()
                
                # Wait before next iteration
                self.log("Waiting before next iteration...")
                time.sleep(30)  # 30 seconds between iterations
                
            except KeyboardInterrupt:
                self.log("Development interrupted by user")
                break
            except Exception as e:
                self.log(f"Error in development loop: {e}", "ERROR")
                time.sleep(60)  # Wait longer on errors
        
        self.log("Continuous development loop completed")
    
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
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return
    
    developer = AIDeveloper()
    
    # Print initial status
    status = developer.status_report()
    print(f"Project Status: {status['completed_tasks']}/{status['total_tasks']} tasks completed ({status['completion_percentage']:.1f}%)")
    
    # Start continuous development
    developer.continuous_development_loop()
    
    # Print final status
    final_status = developer.status_report()
    print(f"Final Status: {final_status['completed_tasks']}/{final_status['total_tasks']} tasks completed ({final_status['completion_percentage']:.1f}%)")

if __name__ == "__main__":
    main() 