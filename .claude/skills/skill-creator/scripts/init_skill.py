#!/usr/bin/env python3
"""
Skill Initializer - Creates a new skill from template

Usage:
    init_skill.py <skill-name> --desc <description>

Examples:
    init_skill.py my-new-skill --desc "Data analysis helper"
    init_skill.py my-api-helper --desc "API integration helper"

Note: Script automatically creates skills in both .claude/skills/ and .agents/skills/
"""

import sys
from pathlib import Path


SKILL_TEMPLATE = """---
name: {skill_name}
description: {description}
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" → "Reading" → "Creating" → "Editing"
- Structure: ## Overview → ## Workflow Decision Tree → ## Step 1 → ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" → "Merge PDFs" → "Split PDFs" → "Extract Text"
- Structure: ## Overview → ## Quick Start → ## Task Category 1 → ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" → "Colors" → "Typography" → "Features"
- Structure: ## Overview → ## Guidelines → ## Specifications → ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" → numbered capability list
- Structure: ## Overview → ## Core Capabilities → ### 1. Feature → ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Example helper script for {skill_name}

This is a placeholder script that can be executed directly.
Replace with actual implementation or delete if not needed.

Example real scripts from other skills:
- pdf/scripts/fill_fillable_fields.py - Fills PDF form fields
- pdf/scripts/convert_pdf_to_images.py - Converts PDF pages to images
"""

def main():
    print("This is an example script for {skill_name}")
    # TODO: Add actual script logic here
    # This could be data processing, file conversion, API calls, etc.

if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

This is a placeholder for detailed reference documentation.
Replace with actual reference content or delete if not needed.

Example real reference docs from other skills:
- product-management/references/communication.md - Comprehensive guide for status updates
- product-management/references/context_building.md - Deep-dive on gathering context
- bigquery/references/ - API references and query examples

## When Reference Docs Are Useful

Reference docs are ideal for:
- Comprehensive API documentation
- Detailed workflow guides
- Complex multi-step processes
- Information too lengthy for main SKILL.md
- Content that's only needed for specific use cases

## Structure Suggestions

### API Reference Example
- Overview
- Authentication
- Endpoints with examples
- Error codes
- Rate limits

### Workflow Guide Example
- Prerequisites
- Step-by-step instructions
- Common patterns
- Troubleshooting
- Best practices
"""

EXAMPLE_ASSET = """# Example Asset File

This placeholder represents where asset files would be stored.
Replace with actual asset files (templates, images, fonts, etc.) or delete if not needed.

Asset files are NOT intended to be loaded into context, but rather used within
the output Claude produces.

Example asset files from other skills:
- Brand guidelines: logo.png, slides_template.pptx
- Frontend builder: hello-world/ directory with HTML/React boilerplate
- Typography: custom-font.ttf, font-family.woff2
- Data: sample_data.csv, test_dataset.json

## Common Asset Types

- Templates: .pptx, .docx, boilerplate directories
- Images: .png, .jpg, .svg, .gif
- Fonts: .ttf, .otf, .woff, .woff2
- Boilerplate code: Project directories, starter files
- Icons: .ico, .svg
- Data files: .csv, .json, .xml, .yaml

Note: This is a text placeholder. Actual assets can be any file type.
"""


def title_case_skill_name(skill_name):
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def find_project_root():
    current_path = Path(__file__).resolve().parent.parent.parent.parent

    while current_path != current_path.parent:
        agents_md_path = current_path / "AGENTS.md"
        if agents_md_path.exists():
            return current_path
        current_path = current_path.parent

    return None


def init_skill(skill_name, description):
    project_root = find_project_root()
    if not project_root:
        print("❌ Error: Could not find project root (AGENTS.md not found)")
        return None, None

    claude_skill_dir = project_root / ".claude" / "skills" / skill_name
    agents_skill_dir = project_root / ".agents" / "skills" / skill_name

    if claude_skill_dir.exists() or agents_skill_dir.exists():
        existing = claude_skill_dir if claude_skill_dir.exists() else agents_skill_dir
        print(f"❌ Error: Skill directory already exists: {existing}")
        return None, None

    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(skill_name=skill_name, description=description, skill_title=skill_title)

    created_dirs = []

    for skill_dir in [claude_skill_dir, agents_skill_dir]:
        try:
            skill_dir.mkdir(parents=True, exist_ok=False)
            print(f"✅ Created skill directory: {skill_dir}")
        except Exception as e:
            print(f"❌ Error creating directory {skill_dir}: {e}")
            return None, None

        skill_md_path = skill_dir / "SKILL.md"
        try:
            skill_md_path.write_text(skill_content)
            print(f"✅ Created {skill_dir.name}/SKILL.md")
        except Exception as e:
            print(f"❌ Error creating SKILL.md in {skill_dir}: {e}")
            return None, None

        try:
            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            example_script = scripts_dir / "example.py"
            example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
            example_script.chmod(0o755)
            print(f"✅ Created {skill_dir.name}/scripts/example.py")

            references_dir = skill_dir / "references"
            references_dir.mkdir(exist_ok=True)
            example_reference = references_dir / "api_reference.md"
            example_reference.write_text(EXAMPLE_REFERENCE.format(skill_title=skill_title))
            print(f"✅ Created {skill_dir.name}/references/api_reference.md")

            assets_dir = skill_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            example_asset = assets_dir / "example_asset.txt"
            example_asset.write_text(EXAMPLE_ASSET)
            print(f"✅ Created {skill_dir.name}/assets/example_asset.txt")
        except Exception as e:
            print(f"❌ Error creating resource directories in {skill_dir}: {e}")
            return None, None

        created_dirs.append(skill_dir)

    print(f"\n✅ Skill '{skill_name}' initialized successfully")
    print(f"   Claude location: {claude_skill_dir}")
    print(f"   Agents location: {agents_skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items and update the description")
    print("2. Customize or delete the example files in scripts/, references/, and assets/")
    print("3. Run the validator when ready to check the skill structure")

    return claude_skill_dir, agents_skill_dir


def register_skill_in_agents_md(skill_name, description):
    project_root = find_project_root()
    if not project_root:
        print("❌ Error: Could not find project root (AGENTS.md not found)")
        return False

    agents_md_path = project_root / "AGENTS.md"

    try:
        content = agents_md_path.read_text()
    except Exception as e:
        print(f"❌ Error reading AGENTS.md: {e}")
        return False

    if "<available_skills>" not in content:
        print("❌ Error: <available_skills> tag not found in AGENTS.md")
        return False

    skill_entry = f"""  <skill>
    <name>{skill_name}</name>
    <description>{description}</description>
  </skill>"""

    closing_tag = "</available_skills>"
    if closing_tag not in content:
        print("❌ Error: </available_skills> tag not found in AGENTS.md")
        return False

    if f"<name>{skill_name}</name>" in content:
        print(f"⚠️  Warning: Skill '{skill_name}' already registered in AGENTS.md")
        return True

    new_content = content.replace(closing_tag, skill_entry + "\n" + closing_tag)

    try:
        agents_md_path.write_text(new_content)
        print(f"✅ Registered skill '{skill_name}' in AGENTS.md")
        return True
    except Exception as e:
        print(f"❌ Error writing AGENTS.md: {e}")
        return False


def main():
    if len(sys.argv) < 4 or sys.argv[2] != "--desc":
        print("Usage: init_skill.py <skill-name> --desc <description>")
        print("\nSkill name requirements:")
        print("  - Hyphen-case identifier (e.g., 'data-analyzer')")
        print("  - Lowercase letters, digits, and hyphens only")
        print("  - Max 40 characters")
        print("  - Must match directory name exactly")
        print("\nDescription requirements:")
        print("  - Brief explanation of what the skill does")
        print("  - Include when to use this skill")
        print("\nExamples:")
        print('  init_skill.py my-new-skill --desc "Data analysis helper for processing CSV files"')
        print('  init_skill.py my-api-helper --desc "API integration helper for REST services"')
        sys.exit(1)

    skill_name = sys.argv[1]
    description = sys.argv[3]

    print(f"🚀 Initializing skill: {skill_name}")
    print(f"   Description: {description}")
    print()

    claude_dir, agents_dir = init_skill(skill_name, description)

    if not claude_dir or not agents_dir:
        sys.exit(1)

    print("\n📝 Registering skill in AGENTS.md...")
    if not register_skill_in_agents_md(skill_name, description):
        sys.exit(1)

    print("\n✅ Skill creation complete!")
    sys.exit(0)


if __name__ == "__main__":
    main()
