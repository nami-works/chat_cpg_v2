from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
import re
import ast

from app.models.content import ContentProject, ContentOutput
from app.models.user import User
from app.models.brand import Brand


class ContentService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_project(
        self,
        user_id: UUID,
        name: str,
        project_type: str = "redacao",
        description: Optional[str] = None,
        brand_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContentProject:
        """Create a new content project"""
        db_project = ContentProject(
            user_id=user_id,
            brand_id=brand_id,
            name=name,
            description=description,
            project_type=project_type,
            metadata=metadata or {}
        )
        
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        
        return db_project
    
    def get_project_by_id(self, project_id: UUID) -> Optional[ContentProject]:
        """Get project by ID"""
        return self.db.query(ContentProject).filter(ContentProject.id == project_id).first()
    
    def get_user_projects(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ContentProject]:
        """Get all projects for a user"""
        return (self.db.query(ContentProject)
                .filter(ContentProject.user_id == user_id)
                .order_by(ContentProject.updated_at.desc())
                .offset(skip)
                .limit(limit)
                .all())
    
    def parse_creative_outputs(self, response_text: str, project_id: UUID) -> Dict[str, Any]:
        """Parse themes, seo_themes, and macro_name from AI response"""
        result = {}
        
        # Parse themes dictionary
        theme_pattern = re.search(r'themes\s*=\s*\{[^}]+\}', response_text, re.DOTALL)
        if theme_pattern:
            try:
                theme_text = theme_pattern.group(0)
                theme_dict = ast.literal_eval(theme_text.split('=')[1].strip())
                if isinstance(theme_dict, dict):
                    result['themes'] = theme_dict
            except Exception:
                pass
        
        # Parse seo_themes dictionary
        seo_theme_pattern = re.search(r'seo_themes\s*=\s*\{[^}]+\}', response_text, re.DOTALL)
        if seo_theme_pattern:
            try:
                seo_theme_text = seo_theme_pattern.group(0)
                seo_theme_dict = ast.literal_eval(seo_theme_text.split('=')[1].strip())
                if isinstance(seo_theme_dict, dict):
                    result['seo_themes'] = seo_theme_dict
            except Exception:
                pass
        
        # Parse macro_name
        macro_name_pattern = re.search(r'macro_name\s*=\s*["\']([^"\']+)["\']', response_text)
        if macro_name_pattern:
            try:
                macro_name = macro_name_pattern.group(1)
                result['macro_name'] = macro_name
            except Exception:
                pass
        
        # Update project if data was found
        if result and ('themes' in result or 'seo_themes' in result or 'macro_name' in result):
            self.update_project_themes(project_id, result)
        
        return result
    
    def update_project_themes(self, project_id: UUID, data: Dict[str, Any]) -> Optional[ContentProject]:
        """Update project with themes and related data"""
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        
        if 'themes' in data:
            project.themes = data['themes']
        if 'seo_themes' in data:
            project.seo_themes = data['seo_themes']
        if 'macro_name' in data:
            project.macro_name = data['macro_name']
        
        # Update status if themes are complete
        if project.themes and project.seo_themes:
            project.status = "themes_generated"
        
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def create_content_outputs(self, project_id: UUID) -> List[ContentOutput]:
        """Create content output records for all themes in a project"""
        project = self.get_project_by_id(project_id)
        if not project or not project.themes:
            return []
        
        outputs = []
        for theme_key, theme_title in project.themes.items():
            output = ContentOutput(
                project_id=project_id,
                theme_key=theme_key,
                theme_title=theme_title,
                content_type="blog_post"
            )
            outputs.append(output)
            self.db.add(output)
        
        # Update project status
        project.status = "content_requested"
        
        self.db.commit()
        
        for output in outputs:
            self.db.refresh(output)
        
        return outputs
    
    def update_content_output(
        self,
        output_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        seo_title: Optional[str] = None,
        meta_description: Optional[str] = None,
        h1_tag: Optional[str] = None,
        h2_tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ContentOutput]:
        """Update content output with generated content"""
        output = self.db.query(ContentOutput).filter(ContentOutput.id == output_id).first()
        if not output:
            return None
        
        if title is not None:
            output.title = title
        if content is not None:
            output.content = content
        if seo_title is not None:
            output.seo_title = seo_title
        if meta_description is not None:
            output.meta_description = meta_description
        if h1_tag is not None:
            output.h1_tag = h1_tag
        if h2_tags is not None:
            output.h2_tags = h2_tags
        if keywords is not None:
            output.keywords = keywords
        if status is not None:
            output.status = status
        if metadata is not None:
            output.meta = {**(output.meta or {}), **metadata}
        
        self.db.commit()
        self.db.refresh(output)
        
        return output
    
    def get_project_outputs(self, project_id: UUID) -> List[ContentOutput]:
        """Get all content outputs for a project"""
        return (self.db.query(ContentOutput)
                .filter(ContentOutput.project_id == project_id)
                .order_by(ContentOutput.created_at)
                .all()) 