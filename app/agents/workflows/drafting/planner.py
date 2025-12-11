from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import DraftingPlan, Section, SectionStatus, AgentNode
from app.agents.workflows.drafting.llm_utils import (
    create_cached_llm,
    create_cached_messages_with_context
)
import uuid
import re
import json
from typing import List, Dict
import os

class DraftMasterPlanner:
    def __init__(self, llm=None):
        self.llm = llm  # Lazy init
        self.system_prompt = load_drafting_prompt("planner")

    async def _get_llm(self):
        if not self.llm:
            from app.agents.workflows.drafting.llm_utils import create_cached_llm
            self.llm = create_cached_llm(
                temperature=0.4
            )
        return self.llm

    async def create_plan(self, state: DraftState) -> dict:
        """
        Agent Node: Create the initial drafting plan.

        Parses the template to:
        1. Identify sections based on headings/structure
        2. Extract placeholders from each section
        3. Determine required facts and laws
        4. Create dependency relationships
        """
        print(f"--- [Planner] Creating plan for Case: {state.get('case_id')} Type: {state.get('case_type')} ---")

        template_content = state.get("template_content", "")
        template_data = state.get("template_data", {})
        case_type = state.get("case_type", "unknown")

        if not template_content:
            print("Warning: No template content provided, creating minimal plan")
            # Create a basic fallback plan
            sections = self._create_fallback_plan(state)
        else:
            # Try LLM-based intelligent parsing first (better quality)
            print("  Using LLM for intelligent template analysis...")
            try:
                sections = await self._parse_template_with_llm(template_content, template_data, state)
                print(f"  ✓ LLM parsing successful: {len(sections)} sections identified")
            except Exception as e:
                print(f"  Warning: LLM parsing failed ({str(e)}), falling back to regex")
                # Fallback to regex-based parsing
                sections = self._parse_template_sections(template_content, template_data)

        # Create the plan
        plan = DraftingPlan(
            sections=sections,
            total_estimated_sections=len(sections),
            complexity=self._assess_complexity(sections)
        )

        print(f"Created plan with {len(sections)} sections (complexity: {plan.complexity})")

        return {
            "plan": plan,
            "current_section_idx": 0,
            "completed_section_ids": [],
            "iteration_count": 0,
            "max_iterations": 3
        }

    async def _parse_template_with_llm(self, template_content: str, template_data: Dict, state: DraftState) -> List[Section]:
        """
        Use LLM to intelligently parse template into sections.

        Advantages over regex:
        - Understands semantic section boundaries
        - Identifies implicit requirements
        - Better dependency detection
        - Contextual understanding of Indian legal documents
        """
        # Load system prompt (will be cached at API level)
        system_prompt = load_drafting_prompt("planner")

        # Prepare context for caching (static per case)
        cache_context = {
            "case_data": state.get("case_data", {}),
            "case_type": state.get("case_type", "unknown"),
            "template_metadata": template_data,
            "document_count": len(state.get("documents", []))
        }

        # Create parsing query (NOT cached - changes per template)
        user_message = f"""Analyze the following legal document template and create a detailed drafting plan.

**Template Content**:
```
{template_content[:5000]}  # Limit to 5000 chars to save tokens
{('...[truncated]' if len(template_content) > 5000 else '')}
```

**Your Task**:
Parse this template into logical sections for sequential drafting. For each section:

1. **Identify Section Boundaries**: Where does each section start/end?
2. **Extract Placeholders**: Find all {{variable}} placeholders
3. **Identify Required Facts**: What case facts are needed?
4. **Identify Required Laws**: What legal provisions/cases need to be cited?
5. **Detect Dependencies**: Which sections depend on previous sections?

**Output JSON Format**:
{{
  "sections": [
    {{
      "title": "Section title",
      "template_text": "Full template text for this section",
      "required_facts": ["fact_key_1", "fact_key_2"],
      "required_laws": ["Legal provision or case law needed"],
      "dependencies": ["section_title_1"],  // Sections this depends on
      "order_index": 0,
      "complexity": "low|medium|high",
      "estimated_word_count": 200
    }}
  ],
  "overall_complexity": "low|medium|high",
  "special_requirements": ["Any special drafting requirements"],
  "indian_legal_standards": ["Relevant Indian legal standards to follow"]
}}

**Guidelines**:
- Identify sections by headings, structure, or logical breaks
- Extract ALL placeholders in {{braces}}
- Consider Indian legal document structure (Title, Parties, Background, Grounds, Prayer, Verification)
- Identify cross-section dependencies (e.g., Prayer depends on Background)
- Note any specialized Indian legal requirements (e.g., CPC, IPC sections)

Provide detailed analysis for high-quality drafting."""

        # Create messages with optimal caching structure
        messages = create_cached_messages_with_context(
            system_prompt=system_prompt,
            user_message=user_message,
            context=cache_context,
            cache_system=True,  # Cache the system prompt
            cache_context=True  # Cache the case context
        )

        # Invoke LLM
        response = await self.llm.ainvoke(messages)
        llm_analysis = response.content if hasattr(response, 'content') else str(response)

        # Log cache performance
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            cache_read = usage.get('cache_read_input_tokens', 0)
            if cache_read > 0:
                print(f"    ✓ Cache HIT: {cache_read} tokens from cache")

        # Parse JSON response
        json_match = re.search(r'\{[\s\S]*\}', llm_analysis)
        if not json_match:
            raise ValueError("LLM did not return valid JSON")

        plan_data = json.loads(json_match.group())

        # Convert LLM output to Section objects
        sections = []
        for idx, section_data in enumerate(plan_data.get('sections', [])):
            section = Section(
                id=str(uuid.uuid4()),
                title=section_data.get('title', f'Section {idx+1}'),
                template_text=section_data.get('template_text', ''),
                required_facts=section_data.get('required_facts', []),
                required_laws=section_data.get('required_laws', []),
                dependencies=section_data.get('dependencies', []),
                status=SectionStatus.PENDING,
                order_index=section_data.get('order_index', idx)
            )
            sections.append(section)

        # Log special requirements if any
        if plan_data.get('special_requirements'):
            print(f"    📋 Special requirements: {', '.join(plan_data['special_requirements'][:3])}")

        return sections

    def _parse_template_sections(self, template_content: str, template_data: Dict) -> List[Section]:
        """
        Parse template content to identify sections.

        Strategy:
        1. Split by major headings (##, H2 tags, or uppercase lines)
        2. Extract placeholders from each section
        3. Identify required facts and dependencies
        """
        sections = []

        # Try to split by markdown headings (##) or HTML headings (<h2>)
        # This is a simple heuristic - more sophisticated parsing could use LLM

        # Pattern 1: Markdown headings
        section_parts = re.split(r'\n#{1,2}\s+(.+?)\n', template_content)

        if len(section_parts) < 3:
            # Pattern 2: HTML headings
            section_parts = re.split(r'<h[12][^>]*>(.+?)</h[12]>', template_content, flags=re.IGNORECASE)

        if len(section_parts) < 3:
            # Pattern 3: Uppercase lines (common in legal templates)
            section_parts = re.split(r'\n([A-Z][A-Z\s]{5,})\n', template_content)

        if len(section_parts) < 3:
            # Fallback: Treat entire template as one section
            sections.append(self._create_section(
                title="Main Document",
                template_text=template_content,
                order_index=0
            ))
            return sections

        # Process matched sections
        current_title = None
        for i, part in enumerate(section_parts):
            part = part.strip()
            if not part:
                continue

            # Odd indices are titles (from split pattern)
            if i % 2 == 1:
                current_title = part
            elif current_title:
                # Even indices are content
                sections.append(self._create_section(
                    title=current_title,
                    template_text=part,
                    order_index=len(sections)
                ))
                current_title = None

        # If no sections found, create one section
        if not sections:
            sections.append(self._create_section(
                title="Main Document",
                template_text=template_content,
                order_index=0
            ))

        return sections

    def _create_section(self, title: str, template_text: str, order_index: int) -> Section:
        """
        Create a Section object from title and template text.
        """
        # Extract placeholders (variables in {braces})
        placeholders = re.findall(r'\{(\w+)\}', template_text)
        required_facts = list(set(placeholders))  # Unique placeholders

        # Identify if legal references are needed (heuristic)
        required_laws = []
        if any(keyword in template_text.lower() for keyword in ['section', 'act', 'law', 'statute', 'case']):
            required_laws.append(f"relevant laws for {title}")

        return Section(
            id=str(uuid.uuid4()),
            title=title,
            template_text=template_text,
            required_facts=required_facts,
            required_laws=required_laws,
            dependencies=[],  # TODO: More sophisticated dependency analysis
            status=SectionStatus.PENDING,
            order_index=order_index
        )

    def _create_fallback_plan(self, state: DraftState) -> List[Section]:
        """
        Create a minimal fallback plan when no template is available.
        """
        case_type = state.get("case_type", "unknown")

        # Create basic sections based on case type
        sections = [
            Section(
                id=str(uuid.uuid4()),
                title="Title and Parties",
                template_text="IN THE {court_name}\n\n{case_number}\n\n{petitioner_name} (Petitioner)\nv.\n{respondent_name} (Respondent)",
                required_facts=["court_name", "case_number", "petitioner_name", "respondent_name"],
                order_index=0,
                status=SectionStatus.PENDING
            ),
            Section(
                id=str(uuid.uuid4()),
                title="Background and Facts",
                template_text="[CASE_SUMMARY]\n\n[KEY_FACTS]",
                required_facts=["case_summary", "key_facts"],
                required_laws=[f"{case_type} relevant laws"],
                order_index=1,
                status=SectionStatus.PENDING
            ),
            Section(
                id=str(uuid.uuid4()),
                title="Prayer",
                template_text="Wherefore, the Petitioner most respectfully prays that:\n\n{prayer}",
                required_facts=["prayer"],
                order_index=2,
                status=SectionStatus.PENDING
            ),
            Section(
                id=str(uuid.uuid4()),
                title="Verification",
                template_text="I, {petitioner_name}, verify that the contents of the above petition are true to my knowledge.",
                required_facts=["petitioner_name"],
                dependencies=[],
                order_index=3,
                status=SectionStatus.PENDING
            )
        ]

        return sections

    def _assess_complexity(self, sections: List[Section]) -> str:
        """
        Assess document complexity based on sections and requirements.
        """
        total_sections = len(sections)
        total_facts = sum(len(s.required_facts) for s in sections)
        total_laws = sum(len(s.required_laws) for s in sections)

        if total_sections <= 3 and total_facts <= 10:
            return "Low"
        elif total_sections <= 7 and total_facts <= 30:
            return "Medium"
        else:
            return "High"

# Helper with caching
from app.agents.workflows.drafting.cache import cache_prompt

@cache_prompt
def load_drafting_prompt(filename: str) -> str:
    """Load system prompt with automatic caching."""
    path = os.path.join(os.path.dirname(__file__), f"../../prompts/system_prompts/drafting/{filename}.md")
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert legal assistant."

# Runnable/Node wrapper
planner_agent = DraftMasterPlanner()

async def planning_node(state: DraftState):
    return await planner_agent.create_plan(state)
