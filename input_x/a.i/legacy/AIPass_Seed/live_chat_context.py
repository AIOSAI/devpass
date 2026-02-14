from config import get_context_config


context_limit = get_context_config().get("limit", 3)
chat_context = []

def add_to_context(role, content):
    chat_context.append({"role": role, "content": content})
    if len(chat_context) > context_limit:
        chat_context.pop(0)

def get_context():
    return chat_context.copy()
