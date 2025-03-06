from typing import Any, Dict
import json
import base64
from github import Github
from github.Repository import Repository

from app.services.core.storage.base import BaseStorageService
from app.core.config import get_settings


class GitHubService(BaseStorageService):
    """GitHub storage service implementation"""
    
    def __init__(self):
        """Initialize GitHub service"""
        settings = get_settings()
        self.client = Github(settings.GITHUB_ACCESS_TOKEN)
        self.username = settings.GITHUB_USERNAME
        self.repo_name = settings.GITHUB_REPO
        self.repo: Repository = self.client.get_repo(f"{self.username}/{self.repo_name}")
        
    async def save(self, content: str, path: str) -> str:
        """Save content to GitHub repository"""
        try:
            # Try to get existing file
            file = self.repo.get_contents(path)
            # Update file if it exists
            self.repo.update_file(
                path=path,
                message=f"Update {path}",
                content=content,
                sha=file.sha
            )
        except:
            # Create new file if it doesn't exist
            self.repo.create_file(
                path=path,
                message=f"Create {path}",
                content=content
            )

        return f"https://github.com/{self.username}/{self.repo_name}/blob/main/{path}"
        
    async def load(self, identifier: str) -> Dict[str, Any]:
        """Load data from GitHub repository"""
        try:
            file = self.repo.get_contents(identifier)
            content = base64.b64decode(file.content).decode()
            return json.loads(content)
        except Exception as e:
            raise Exception(f"Failed to load data from GitHub: {str(e)}")
        
    async def delete(self, identifier: str) -> bool:
        """Delete data from GitHub repository"""
        try:
            file = self.repo.get_contents(identifier)
            self.repo.delete_file(identifier, "Delete data", file.sha)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete data from GitHub: {str(e)}")
            return False
