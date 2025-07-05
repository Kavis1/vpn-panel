import os
from pathlib import Path

# Base directory for documentation
base_dir = Path(__file__).parent

docs_structure = {
    "installation/": [
        "requirements.md",
        "master.md",
        "node.md",
        "upgrade.md"
    ],
    "configuration/": [
        "environment.md",
        "database.md",
        "security.md",
        "email.md"
    ],
    "admin/": [
        "users.md",
        "nodes.md",
        "monitoring.md",
        "backup.md"
    ],
    "user/": [
        "quickstart.md",
        "clients.md",
        "devices.md",
        "stats.md"
    ],
    "api/": [
        "authentication.md",
        "endpoints.md",
        "examples.md",
        "errors.md"
    ],
    "development/": [
        "setup.md",
        "structure.md",
        "style.md",
        "contributing.md"
    ]
}

# Create directories and files
for directory, files in docs_structure.items():
    dir_path = base_dir / directory
    dir_path.mkdir(exist_ok=True)
    
    # Create README.md if it doesn't exist
    readme_path = dir_path / "README.md"
    if not readme_path.exists():
        with open(readme_path, 'w', encoding='utf-8') as f:
            title = directory.strip('/').capitalize()
            f.write(f"# {title}\n\nThis section contains {title.lower()} documentation.\n")
    
    # Create other markdown files
    for file in files:
        file_path = dir_path / file
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                title = file.replace('.md', '').replace('_', ' ').title()
                f.write(f"# {title}\n\nDocumentation for {title.lower()}.\n")

print("Documentation structure has been updated.")
