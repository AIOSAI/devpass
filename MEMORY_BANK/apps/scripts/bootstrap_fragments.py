#!/home/aipass/MEMORY_BANK/.venv/bin/python3

"""
Bootstrap fragments into ChromaDB from session JONLs.

Uses v1 regex extraction to create v2-format fragments and stores
them directly via the storage handler. Designed to run as a script
within the Memory Bank branch context.

Usage: .venv/bin/python3 apps/scripts/bootstrap_fragments.py
"""

import json
import sys
from pathlib import Path

# Setup paths for Memory Bank imports
BRANCH_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BRANCH_ROOT))
sys.path.insert(0, str(Path.home() / "aipass_core"))

from apps.handlers.symbolic import storage, extractor


def read_jsonl_messages(jsonl_path, max_msgs=100):
    """Read user/assistant messages from a Claude Code JSONL transcript."""
    messages = []
    with open(jsonl_path, 'r', errors='ignore') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
            except (json.JSONDecodeError, ValueError):
                continue
            msg = entry.get('message', {})
            role = msg.get('role', '')
            content = msg.get('content', '')

            if entry.get('type') == 'user' and isinstance(content, str) and content.strip():
                messages.append({'role': 'user', 'content': content.strip()[:1000]})
            elif entry.get('type') == 'assistant':
                if isinstance(content, str) and content.strip():
                    messages.append({'role': 'assistant', 'content': content.strip()[:1000]})
                elif isinstance(content, list):
                    texts = [
                        i.get('text', '').strip()[:500]
                        for i in content
                        if isinstance(i, dict) and i.get('type') == 'text'
                        and i.get('text', '').strip()
                    ]
                    if texts:
                        messages.append({'role': 'assistant', 'content': ' '.join(texts)[:1000]})

    return messages[:max_msgs]


def _map_arc_to_tone(arcs):
    """Map v1 emotional arcs to v2 emotional_tone enum."""
    arc_str = ' '.join(arcs)
    if 'frustration' in arc_str:
        return 'frustrated'
    if 'excitement' in arc_str or 'breakthrough' in arc_str:
        return 'excited'
    if 'curiosity' in arc_str:
        return 'curious'
    if 'confidence' in arc_str:
        return 'confident'
    return 'neutral'


def create_fragments_from_analysis(messages, branch_name):
    """Create v2-format fragments from v1 regex analysis of conversation."""
    if len(messages) < 4:
        return []

    dims = extractor.extract_symbolic_dimensions(messages)
    if not dims.get('success'):
        return []

    # All dimension values are lists (not dicts)
    d = dims.get('dimensions', {})
    tech_patterns = d.get('technical', [])    # e.g. ['problem_solution_flow']
    arcs = d.get('emotional', [])             # e.g. ['frustration_to_breakthrough']
    collab_patterns = d.get('collaboration', [])  # e.g. ['balanced', 'teaching']
    learning_items = d.get('learnings', [])   # e.g. ['chromadb', 'embeddings']
    kws = d.get('triggers', [])               # e.g. ['error', 'fix', 'chromadb']

    fragments = []

    # Fragment from technical flow
    if tech_patterns and tech_patterns != ['general_technical']:
        pattern = tech_patterns[0]
        fragments.append({
            'summary': f"Session with {branch_name}: {pattern.replace('_', ' ')} pattern detected",
            'insight': f"Conversation showed {pattern.replace('_', ' ')} flow across {len(messages)} messages",
            'type': 'episodic',
            'triggers': kws[:5],
            'emotional_tone': 'neutral',
            'technical_domain': branch_name.lower()
        })

    # Fragment from emotional arc
    if arcs and arcs != ['neutral_tone']:
        arc_str = ' to '.join(arcs)
        fragments.append({
            'summary': f"Emotional arc during {branch_name} session: {arc_str}",
            'insight': f"The conversation progressed through {arc_str}",
            'type': 'emotional',
            'triggers': kws[:3],
            'emotional_tone': _map_arc_to_tone(arcs),
            'technical_domain': branch_name.lower()
        })

    # Fragment from learnings
    if learning_items:
        fragments.append({
            'summary': f"Key learnings from {branch_name}: {', '.join(learning_items[:3])}",
            'insight': f"Discovered during a {len(messages)}-message conversation",
            'type': 'semantic',
            'triggers': learning_items[:5],
            'emotional_tone': 'curious',
            'technical_domain': branch_name.lower()
        })

    # Fragment from collaboration patterns
    if collab_patterns and collab_patterns != ['no_interaction']:
        fragments.append({
            'summary': f"Collaboration style with {branch_name}: {', '.join(collab_patterns)}",
            'insight': f"This interaction dynamic is typical for {branch_name} sessions",
            'type': 'procedural',
            'triggers': kws[:3],
            'emotional_tone': 'confident',
            'technical_domain': branch_name.lower()
        })

    # Fragment from trigger keywords
    if kws:
        fragments.append({
            'summary': f"Topics discussed with {branch_name}: {', '.join(kws[:8])}",
            'insight': f"These topics came up during a session - useful context triggers",
            'type': 'semantic',
            'triggers': kws[:10],
            'emotional_tone': 'neutral',
            'technical_domain': branch_name.lower()
        })

    return fragments


def main():
    """Bootstrap fragments from diverse session JONLs."""
    projects_dir = Path.home() / ".claude" / "projects"

    # Session files: diverse branches, medium-sized files
    session_candidates = [
        ('-home-aipass-MEMORY-BANK', 'MEMORY_BANK'),
        ('-home-aipass-aipass-os-dev-central', 'DEV_CENTRAL'),
        ('-home-aipass-seed', 'SEED'),
        ('-home-aipass-aipass-core-drone', 'DRONE'),
        ('-home-aipass-aipass-core-flow', 'FLOW'),
        ('-home-aipass-The-Commons', 'THE_COMMONS'),
        ('-home-aipass-aipass-core-prax', 'PRAX'),
        ('-home-aipass-aipass-core-cortex', 'CORTEX'),
        ('-home-aipass-aipass-core-ai-mail', 'AI_MAIL'),
        ('-home-aipass-aipass-core-api', 'API'),
    ]

    sessions = []
    for dirname, branch in session_candidates:
        branch_dir = projects_dir / dirname
        if not branch_dir.exists():
            continue
        candidates = []
        for f in branch_dir.glob("*.jsonl"):
            if f.name.startswith("agent-"):
                continue
            size = f.stat().st_size
            if 50_000 <= size <= 5_000_000:
                candidates.append((f, size))
        if candidates:
            # Pick largest 2 per branch for variety
            candidates.sort(key=lambda x: x[1], reverse=True)
            for f, s in candidates[:2]:
                sessions.append((f, branch))

    print(f"Found {len(sessions)} sessions to process\n")

    all_fragments = []
    for jsonl_path, branch in sessions:
        messages = read_jsonl_messages(jsonl_path)
        if len(messages) < 4:
            print(f"  {branch}: {len(messages)} msgs - too few, skipping")
            continue

        frags = create_fragments_from_analysis(messages, branch)
        print(f"  {branch}: {len(messages)} msgs -> {len(frags)} fragments")
        all_fragments.extend([(f, branch) for f in frags])

    print(f"\nTotal fragments to store: {len(all_fragments)}")

    if not all_fragments:
        print("No fragments generated!")
        return 1

    # Group by branch for batch storage
    by_branch = {}
    for frag, branch in all_fragments:
        if branch not in by_branch:
            by_branch[branch] = []
        by_branch[branch].append(frag)

    total_stored = 0
    for branch, frags in by_branch.items():
        result = storage.store_llm_fragments_batch(frags, source_branch=branch)
        if result.get('success'):
            count = result.get('stored', 0)
            total_stored += count
            print(f"  {branch}: stored {count}")
        else:
            print(f"  {branch}: FAILED - {result.get('error', 'unknown')}")

    print(f"\nTotal stored: {total_stored}")

    # Verify
    import chromadb
    client = chromadb.PersistentClient(path=str(BRANCH_ROOT / '.chroma'))
    col = client.get_collection('symbolic_fragments')
    print(f"Collection count: {col.count()}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
