from typing import Any, Dict, List
import json
import base64
from github import Github
from github.GithubException import GithubException

from app.services.storage.base import BaseStorageService
from app.core.config import get_settings

settings = get_settings()

class GitHubService(BaseStorageService):
    """GitHub storage service implementation"""
    
    def __init__(self):
        super().__init__()
        self.client = Github(settings.GITHUB_ACCESS_TOKEN)
        self.repo = self.client.get_repo(f"{settings.GITHUB_USERNAME}/{settings.GITHUB_REPO}")
        
    async def save(self, data: Dict[str, Any], **kwargs: Dict[str, Any]) -> str:
        """Save data to GitHub repository"""
        path = kwargs.get("path", "data.json")
        message = kwargs.get("message", "Update data")
        
        try:
            content = base64.b64encode(json.dumps(data).encode()).decode()
            try:
                file = self.repo.get_contents(path)
                self.repo.update_file(path, message, content, file.sha)
            except GithubException:
                self.repo.create_file(path, message, content)
            return path
        except Exception as e:
            raise Exception(f"Failed to save data to GitHub: {str(e)}")
        
    async def load(self, identifier: str, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Load data from GitHub repository"""
        try:
            file = self.repo.get_contents(identifier)
            content = base64.b64decode(file.content).decode()
            return json.loads(content)
        except Exception as e:
            raise Exception(f"Failed to load data from GitHub: {str(e)}")
        
    async def delete(self, identifier: str, **kwargs: Dict[str, Any]) -> bool:
        """Delete data from GitHub repository"""
        try:
            file = self.repo.get_contents(identifier)
            self.repo.delete_file(identifier, "Delete data", file.sha)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete data from GitHub: {str(e)}")
            return False
