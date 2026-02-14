import ast
from typing import List

class PythonDocumentSymbol:
    def __init__(self, kind, name, start_line, end_line, children=None):
        self.kind = kind
        self.name = name
        self.range = type('Range', (), {'startLineNumber': start_line, 'endLineNumber': end_line})()
        self.children = children if children is not None else []

class PythonDocumentSymbolProvider:
    display_name = "Python Symbol Provider"
    
    async def provide_document_symbols(self, text_model, token=None):
        # text_model should have a .uri or .path attribute
        path = getattr(text_model, 'uri', None)
        if hasattr(path, 'fsPath'):
            file_path = path.fsPath
        elif hasattr(path, 'path'):
            file_path = path.path
        else:
            file_path = str(path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except Exception:
            return []
        tree = ast.parse(source, filename=file_path)
        symbols = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                start = node.lineno
                end = max(getattr(node, 'end_lineno', start), start)
                symbols.append(PythonDocumentSymbol('Class', node.name, start, end))
            elif isinstance(node, ast.FunctionDef):
                start = node.lineno
                end = max(getattr(node, 'end_lineno', start), start)
                symbols.append(PythonDocumentSymbol('Function', node.name, start, end))
        return symbols
