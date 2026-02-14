def get_prompt():
    """Prompt for dependency tracing capabilities."""
    return '''
# Dependency Tracing

Seed can trace dependencies between files and modules in your project. Use these commands:
- `trace dependencies <file_path>`: List all files/modules imported or required by the specified file.
- `show dependency graph <file_path>`: Display a graph or list of direct and indirect dependencies.
- `trace dependents <file_path>`: List all files that depend on the specified file.

Seed will remember the last dependency trace operation in session memory for follow-up questions.
'''
