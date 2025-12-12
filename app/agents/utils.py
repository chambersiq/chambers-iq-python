import os
from functools import lru_cache


def load_system_prompt(category: str, filename: str) -> str:
    """
    Load a system prompt from the central prompts directory.
    
    Args:
        category: Subdirectory (e.g., 'concierge', 'drafting')
        filename: Filename without extension (e.g., 'assistant')
        
    Returns:
        The content of the markdown file.
    """
    # Base path: app/agents/prompts/system_prompts
    base_path = os.path.join(os.path.dirname(__file__), "prompts/system_prompts")
    file_path = os.path.join(base_path, category, f"{filename}.md")
    
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback or raise
        print(f"Warning: Prompt file not found at {file_path}")
        return ""

def generate_schema_description(model_class) -> str:
    """
    Auto-generate a readable schema description from a Pydantic model.
    Handles nested models and Unons if possible, or just flat fields.
    """
    schema_lines = []
    
    # Handle RootModel or Union types via checking __args__ or similar?
    # For now, simplistic approach using model_json_schema() might be safest,
    # but manually iterating fields is more readable for LLM.
    
    if hasattr(model_class, "model_fields"):
        for field_name, field_info in model_class.model_fields.items():
            # Skip internal/system fields
            if field_name in ["id", "createdAt", "updatedAt", "metadata", "companyId", "clientId"]:
                continue
                
            required = "Required" if field_info.is_required() else "Optional"
            
            # Get type annotation string representation
            try:
                type_str = str(field_info.annotation).replace("typing.", "").replace("Optional[", "").replace("]", "")
            except:
                type_str = "Any"
                
            description = field_info.description or ""
            if description:
                description = f" - {description}"
                
            schema_lines.append(f"- {field_name} ({type_str}) [{required}]{description}")
            
    return "\n".join(schema_lines)
