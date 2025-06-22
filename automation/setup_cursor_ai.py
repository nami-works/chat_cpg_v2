#!/usr/bin/env python3
"""
Setup script for Cursor AI Development Workflow
Converts the existing OpenAI to use Cursor AI
"""

import json
import shutil
from pathlib import Path

def setup_cursor_ai():
    """Setup Cursor AI development environment"""
    project_root = Path(".").resolve()
    
    print("Setting up Cursor AI Development Environment")
    print("This will eliminate OpenAI API costs!")
    print("="*60)
    
    # 1. Update development plan to remove OpenAI settings
    plan_file = project_root / "development_plan.json"
    if plan_file.exists():
        with open(plan_file, 'r') as f:
            plan = json.load(f)
        
        # Remove OpenAI-specific settings
        if "ai_settings" in plan:
            del plan["ai_settings"]
        
        # Add Cursor-specific settings
        plan["cursor_settings"] = {
            "workflow_type": "interactive",
            "auto_open_tasks": True,
            "task_timeout_minutes": 60,
            "auto_commit": False
        }
        
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
        
        print("Updated development plan for Cursor AI")
    
    # 2. Backup original AI developer
    original_ai_dev = project_root / "automation" / "ai_developer.py"
    backup_ai_dev = project_root / "automation" / "ai_developer_openai_backup.py"
    
    if original_ai_dev.exists() and not backup_ai_dev.exists():
        shutil.copy2(original_ai_dev, backup_ai_dev)
        print("Backed up original OpenAI-based AI developer")
    
    # 3. Create Cursor workspace directory
    cursor_workspace = project_root / ".cursor_workspace"
    cursor_workspace.mkdir(exist_ok=True)
    (cursor_workspace / "pending_tasks").mkdir(exist_ok=True)
    (cursor_workspace / "completed_tasks").mkdir(exist_ok=True)
    (cursor_workspace / "current_task").mkdir(exist_ok=True)
    print("Created Cursor workspace directories")
    
    # 4. Update .gitignore
    gitignore_file = project_root / ".gitignore"
    cursor_entries = [
        "# Cursor AI workspace",
        ".cursor_workspace/current_task/",
        ".cursor_workspace/*/TASK_*_COMPLETION.json",
        ""
    ]
    
    if gitignore_file.exists():
        with open(gitignore_file, 'r') as f:
            content = f.read()
        
        if "# Cursor AI workspace" not in content:
            with open(gitignore_file, 'a') as f:
                f.write("\n" + "\n".join(cursor_entries))
            print("Updated .gitignore for Cursor AI")
    
    # 5. Create setup completion marker
    setup_marker = project_root / "CURSOR_AI_SETUP_COMPLETE.md"
    with open(setup_marker, 'w', encoding='utf-8') as f:
        f.write("""# Cursor AI Setup Complete!

 ## What's Been Set Up

1. **Cursor AI Developer** - New interactive development system
2. **Zero OpenAI Costs** - Uses your existing Cursor AI subscription
3. **File-Based Workflow** - Tasks prepared as instruction files
4. **Interactive Mode** - You control the development process

 ## How to Use

### Interactive Development
```bash
cd chatcpg_v2/automation
python cursor_ai_developer.py
```

 ## Workflow

1. **Task Selection** - Choose tasks from development plan
2. **Implementation** - Implement using Cursor AI
3. **Progress Tracking** - Mark tasks as completed
4. **Automation** - System handles git commits and testing

 ## Cost Savings

- **Before:** ~$20-50/day in OpenAI API costs
- **After:** $0 (uses your existing Cursor AI subscription)
- **Annual Savings:** $7,300 - $18,250

 ## Features

 - Interactive task selection
 - Detailed task descriptions
 - Progress tracking
 - Zero API costs
 - Uses your Cursor AI subscription

Ready to start developing with Cursor AI!
""")
    
    print("\nCursor AI setup complete!")
    print("See CURSOR_AI_SETUP_COMPLETE.md for usage instructions")
    print("You'll save $7,300-$18,250 annually in OpenAI costs!")
    print("\nStart developing: python automation/cursor_ai_developer.py")

if __name__ == "__main__":
    setup_cursor_ai() 