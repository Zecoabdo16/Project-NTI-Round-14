from pathlib import Path

# Root project folder
root = Path("RAFIQ")

# Folders to create
folders = [
    "api/routers",
    "core",
    "agents",
    "adapters",
    "db"
]

# Files to create
files = [
    "api/main.py",
    "api/dependencies.py",
    "api/routers/chat.py",
    "api/routers/hitl.py",

    "core/state.py",
    "core/graph.py",
    "core/nodes.py",

    "agents/supervisor.py",
    "agents/triage.py",
    "agents/operations.py",
    "agents/medical_memory.py",
    "agents/clinical_dss.py",
    "agents/verification.py",
    "agents/hitl_manager.py",

    "adapters/his_adapter.py",
    "adapters/emr_adapter.py",
    "adapters/kg_adapter.py",
    "adapters/rag_adapter.py",
    "adapters/comms_adapter.py",

    "db/sql_models.py",
    "db/seed_data.sql",

    "docker-compose.yml",
    ".env"
]

# Create folders
for folder in folders:
    (root / folder).mkdir(parents=True, exist_ok=True)

# Create files
for file in files:
    file_path = root / file
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        file_path.touch()

print(f"✅ RAFIQ project structure created successfully in: {root.resolve()}")


python_packages = [
    "api",
    "api/routers",
    "core",
    "agents",
    "adapters",
    "db"
]

for package in python_packages:
    init_file = root / package / "__init__.py"
    init_file.touch(exist_ok=True)