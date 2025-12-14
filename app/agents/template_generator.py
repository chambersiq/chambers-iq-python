import json
from pathlib import Path
from app.agents.workflows.drafting.llm_utils import create_cached_llm, create_cached_messages_with_context
from app.core.config import settings

class TemplateGeneratorAgent:
    def __init__(self):
        # Use established pattern like other agents (Writer, Reviewer, etc.)
        self.llm = create_cached_llm(
            model=settings.LLM_MODEL,
            temperature=0.2,  # Good for template generation
            provider=settings.LLM_PROVIDER
        )

    def load_prompt(self, category: str, filename: str, prompt_type: str) -> str:
        """Load prompt from organized folder structure"""
        prompts_dir = Path(__file__).parent / "prompts"

        if prompt_type == "system":
            prompt_path = prompts_dir / "system_prompts" / category / f"{filename}.md"
        elif prompt_type == "user":
            prompt_path = prompts_dir / "user_prompts" / f"{filename}.md"
        else:
            raise ValueError(f"Invalid prompt_type: {prompt_type}")

        with open(prompt_path, 'r') as f:
            return f.read()

    async def generate_template(self, case_data: dict, document_type: str) -> str:
        """Generate legal template using comprehensive case data"""

        # Load prompts from organized structure
        system_prompt = self.load_prompt('draft_dynamic_template', 'template_creation', 'system')
        user_prompt_template = self.load_prompt('dynamic_template', 'dynamic_template', 'user')

        # Format case data for user prompt
        case_json = json.dumps(case_data.get('case', {}), indent=2, default=str)

        # Format user prompt with case data and document type
        user_message = user_prompt_template.replace('{json.dumps(case_data, indent=2, ensure_ascii=False)}', case_json)
        user_message = user_message.replace('{document_type}', document_type)

        # Use proper message format like other agents (this fixes the LLM call issue!)
        messages = create_cached_messages_with_context(
            system_prompt=system_prompt,
            user_message=user_message,
            context=None  # No additional context needed for template generation
        )

        # Call LLM with proper message structure (CachedLLM expects this format)
        response = await self.llm.ainvoke(messages, max_tokens=3000)

        return response.content
