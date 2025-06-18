"""TestMate Studio - Workspace Manager"""

import os
import json
from datetime import datetime
from typing import Dict, Any

class WorkspaceManager:
    def __init__(self, base_workspace_dir="workspaces"):
        self.base_workspace_dir = base_workspace_dir
        os.makedirs(self.base_workspace_dir, exist_ok=True)
    
    def get_user_workspace_path(self, user_id: int) -> str:
        return os.path.join(self.base_workspace_dir, f"user_{user_id}")
    
    def create_user_workspace(self, user_id: int) -> Dict[str, Any]:
        try:
            workspace_path = self.get_user_workspace_path(user_id)
            os.makedirs(workspace_path, exist_ok=True)
            return {"success": True, "workspace_path": workspace_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

workspace_manager = WorkspaceManager()