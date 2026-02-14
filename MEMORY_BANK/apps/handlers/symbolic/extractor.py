#!/home/aipass/MEMORY_BANK/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: extractor.py - Symbolic Memory Extractor Handler
# Date: 2026-02-04
# Version: 0.1.0
# Category: memory_bank/handlers/symbolic
#
# CHANGELOG (Max 5 entries):
#   - v0.1.0 (2026-02-04): Initial version - ported from symbolic_memory.py
#
# CODE STANDARDS:
#   - Handler independence: No module imports
#   - Error handling: Return status dicts (3-tier architecture)
#   - File size: <300 lines target
# =============================================

"""
Symbolic Memory Extractor Handler

Extracts symbolic dimensions from conversations for fragmented memory storage.
Ported from symbolic_memory.py as part of Fragmented Memory Phase 1.

Key Functions:
    - extract_technical_flow() - problem/debug/breakthrough patterns
    - extract_emotional_journey() - frustration/excitement arcs
    - extract_collaboration_patterns() - user_directed/balanced dynamics
    - extract_key_learnings() - discoveries, insights
    - extract_context_triggers() - keywords that should surface this memory
    - extract_symbolic_dimensions() - calls all extractors
    - analyze_conversation() - main entry point for full analysis
"""

import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Any


# =============================================================================
# TECHNICAL FLOW EXTRACTION
# =============================================================================

def extract_technical_flow(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze technical patterns from conversation

    Detects problem/debug/breakthrough patterns by analyzing
    message content for technical indicators.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'patterns' list, and analysis details
    """
    if not chat_history:
        return {
            'success': True,
            'patterns': ['no_conversation'],
            'details': {}
        }

    patterns = []
    technical_indicators = {
        'problems': ['error', 'bug', 'issue', 'problem', 'broken', 'fail', 'wrong'],
        'debugging': ['debug', 'trace', 'check', 'test', 'try', 'attempt'],
        'solutions': ['fix', 'solve', 'work', 'success', 'breakthrough', 'got it'],
        'struggle': ['stuck', 'confused', 'difficult', 'hard', 'frustrating'],
        'learning': ['understand', 'learn', 'realize', 'discover', 'insight']
    }

    category_counts = {cat: 0 for cat in technical_indicators}

    for message in chat_history:
        content = (message.get('content') or '').lower()
        role = message.get('role', '')

        for category, keywords in technical_indicators.items():
            if any(keyword in content for keyword in keywords):
                patterns.append(f'{category}_{role}')
                category_counts[category] += 1

    pattern_string = ' '.join(patterns)

    # Detect flow type
    if 'problems' in pattern_string and 'solutions' in pattern_string:
        if 'struggle' in pattern_string:
            flow_type = ['problem_struggle_breakthrough']
        else:
            flow_type = ['problem_solution_flow']
    elif 'debugging' in pattern_string:
        flow_type = ['debugging_session']
    elif 'learning' in pattern_string:
        flow_type = ['learning_conversation']
    else:
        flow_type = ['general_technical']

    return {
        'success': True,
        'patterns': flow_type,
        'details': {
            'category_counts': category_counts,
            'raw_patterns': patterns[:10]  # Limit for brevity
        }
    }


# =============================================================================
# EMOTIONAL JOURNEY EXTRACTION
# =============================================================================

def extract_emotional_journey(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect emotional arc from conversation tone and patterns

    Analyzes emotional progression through the conversation
    to identify frustration-to-breakthrough or curiosity-to-excitement arcs.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'arc' list, and emotion timeline
    """
    if not chat_history:
        return {
            'success': True,
            'arc': ['neutral'],
            'details': {}
        }

    emotional_markers = {
        'frustration': ['frustrated', 'annoying', 'difficult', 'stuck', 'ugh', 'damn'],
        'excitement': ['cool', 'awesome', 'great', 'amazing', 'perfect', 'brilliant'],
        'confidence': ['sure', 'certain', 'definitely', 'absolutely', 'know'],
        'uncertainty': ['maybe', 'possibly', 'not sure', 'think', 'guess'],
        'breakthrough': ['got it', 'understand', 'works', 'success', 'finally'],
        'curiosity': ['wonder', 'curious', 'interesting', 'what if', 'how']
    }

    emotion_timeline = []

    for message in chat_history:
        content = (message.get('content') or '').lower()
        role = message.get('role', '')

        message_emotions = []
        for emotion, markers in emotional_markers.items():
            if any(marker in content for marker in markers):
                message_emotions.append(emotion)

        if message_emotions:
            emotion_timeline.append((role, message_emotions))

    if not emotion_timeline:
        return {
            'success': True,
            'arc': ['neutral_tone'],
            'details': {'timeline': []}
        }

    all_emotions = [emotion for _, emotions in emotion_timeline for emotion in emotions]

    # Determine emotional arc
    if 'frustration' in all_emotions and 'breakthrough' in all_emotions:
        arc = ['frustration_to_breakthrough']
    elif 'curiosity' in all_emotions and 'excitement' in all_emotions:
        arc = ['curiosity_to_excitement']
    elif 'uncertainty' in all_emotions and 'confidence' in all_emotions:
        arc = ['uncertainty_to_confidence']
    else:
        emotion_counts = Counter(all_emotions)
        arc = [emotion for emotion, _ in emotion_counts.most_common(2)]

    return {
        'success': True,
        'arc': arc,
        'details': {
            'timeline': emotion_timeline[:10],
            'emotion_counts': dict(Counter(all_emotions))
        }
    }


# =============================================================================
# COLLABORATION PATTERNS EXTRACTION
# =============================================================================

def extract_collaboration_patterns(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify relationship dynamics and interaction patterns

    Analyzes message lengths, question patterns, and coaching/teaching
    indicators to determine collaboration style.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'patterns' list, and interaction metrics
    """
    if not chat_history:
        return {
            'success': True,
            'patterns': ['no_interaction'],
            'details': {}
        }

    user_messages = [msg for msg in chat_history if msg.get('role') == 'user']
    assistant_messages = [msg for msg in chat_history if msg.get('role') == 'assistant']

    if not user_messages or not assistant_messages:
        return {
            'success': True,
            'patterns': ['one_sided_conversation'],
            'details': {}
        }

    patterns = []

    avg_user_length = sum(len(msg.get('content', '')) for msg in user_messages) / len(user_messages)
    avg_assistant_length = sum(len(msg.get('content', '')) for msg in assistant_messages) / len(assistant_messages)

    if avg_user_length > avg_assistant_length * 1.5:
        patterns.append('user_directed')
    elif avg_assistant_length > avg_user_length * 1.5:
        patterns.append('assistant_detailed')
    else:
        patterns.append('balanced_exchange')

    user_questions = sum(1 for msg in user_messages if '?' in msg.get('content', ''))
    if user_questions > len(user_messages) * 0.6:
        patterns.append('question_heavy')

    coaching_indicators = ['try', "let's", 'what if', 'how about', 'consider']
    teaching_indicators = ['explain', 'show', 'understand', 'learn', 'because']

    user_content = ' '.join(msg.get('content', '').lower() for msg in user_messages)
    assistant_content = ' '.join(msg.get('content', '').lower() for msg in assistant_messages)

    if any(indicator in user_content for indicator in coaching_indicators):
        patterns.append('user_coaching')
    if any(indicator in assistant_content for indicator in teaching_indicators):
        patterns.append('assistant_teaching')

    build_indicators = ["let's build", 'we can', 'together', 'collaborate']
    if any(indicator in user_content + assistant_content for indicator in build_indicators):
        patterns.append('collaborative_building')

    return {
        'success': True,
        'patterns': patterns if patterns else ['standard_interaction'],
        'details': {
            'avg_user_length': int(avg_user_length),
            'avg_assistant_length': int(avg_assistant_length),
            'user_questions': user_questions,
            'total_user_messages': len(user_messages)
        }
    }


# =============================================================================
# KEY LEARNINGS EXTRACTION
# =============================================================================

def extract_key_learnings(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract core insights and lessons from conversation

    Identifies discovery, problem-solving, understanding, and
    improvement patterns in the conversation content.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'insights' list, and detected categories
    """
    if not chat_history:
        return {
            'success': True,
            'insights': ['no_insights'],
            'details': {}
        }

    insights = []

    learning_patterns = {
        'discovery': ['discovered', 'found out', 'realized', 'learned'],
        'problem_solving': ['solution', 'approach', 'method', 'way to'],
        'understanding': ['understand', 'makes sense', 'clear', 'see'],
        'improvement': ['better', 'improve', 'optimize', 'enhance'],
        'mistakes': ['wrong', 'mistake', 'error', 'incorrect']
    }

    all_content = ' '.join((msg.get('content') or '').lower() for msg in chat_history)

    for category, indicators in learning_patterns.items():
        if any(indicator in all_content for indicator in indicators):
            insights.append(category)

    # Domain-specific insights
    if 'module' in all_content and 'toggle' in all_content:
        insights.append('module_system_learning')
    if 'memory' in all_content and 'compression' in all_content:
        insights.append('memory_system_learning')
    if 'debug' in all_content and 'fix' in all_content:
        insights.append('debugging_skills')

    return {
        'success': True,
        'insights': insights if insights else ['general_conversation'],
        'details': {
            'content_length': len(all_content)
        }
    }


# =============================================================================
# CONTEXT TRIGGERS EXTRACTION
# =============================================================================

def extract_context_triggers(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract keywords that should trigger this memory in future conversations

    Identifies significant technical terms and concepts that appear
    frequently in the conversation.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with 'success', 'triggers' list, and term frequencies
    """
    if not chat_history:
        return {
            'success': True,
            'triggers': [],
            'details': {}
        }

    all_content = ' '.join((msg.get('content') or '') for msg in chat_history).lower()

    technical_pattern = (
        r'\b(?:module|system|debug|memory|compression|vector|symbolic|cortex|'
        r'registry|toggle|profile|chat|context|api|token|embedding|storage|'
        r'json|function|method|class|import|file|script|error|fix|solution|'
        r'breakthrough|pattern|analysis|extraction|conversation|interaction|'
        r'collaboration|learning|insight|discovery|handler|branch|rollover)\b'
    )

    technical_terms = re.findall(technical_pattern, all_content)
    term_counts = Counter(technical_terms)

    triggers = [term for term, count in term_counts.most_common(10) if count > 1]

    return {
        'success': True,
        'triggers': triggers,
        'details': {
            'term_counts': dict(term_counts.most_common(15))
        }
    }


# =============================================================================
# MAIN EXTRACTION FUNCTIONS
# =============================================================================

def extract_symbolic_dimensions(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract all symbolic dimensions from conversation

    Calls all individual extractors and combines results into
    a unified symbolic representation.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with all extracted dimensions and metadata
    """
    technical = extract_technical_flow(chat_history)
    emotional = extract_emotional_journey(chat_history)
    collaboration = extract_collaboration_patterns(chat_history)
    learnings = extract_key_learnings(chat_history)
    triggers = extract_context_triggers(chat_history)

    return {
        'success': True,
        'dimensions': {
            'technical': technical.get('patterns', []),
            'emotional': emotional.get('arc', []),
            'collaboration': collaboration.get('patterns', []),
            'learnings': learnings.get('insights', []),
            'triggers': triggers.get('triggers', [])
        },
        'details': {
            'technical': technical.get('details', {}),
            'emotional': emotional.get('details', {}),
            'collaboration': collaboration.get('details', {}),
            'learnings': learnings.get('details', {}),
            'triggers': triggers.get('details', {})
        }
    }


def analyze_conversation(chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point for conversation analysis

    Extracts symbolic dimensions and adds conversation metadata
    for complete fragmented memory representation.

    Args:
        chat_history: List of message dicts with 'role' and 'content' keys

    Returns:
        Dict with full analysis including dimensions and metadata
    """
    if not chat_history:
        return {
            'success': True,
            'message_count': 0,
            'dimensions': {},
            'metadata': {}
        }

    dimensions = extract_symbolic_dimensions(chat_history)

    total_chars = sum(len(msg.get('content') or '') for msg in chat_history)
    total_words = sum(len((msg.get('content') or '').split()) for msg in chat_history)

    # Analyze conversation depth
    if total_words > 2000 and len(chat_history) > 20:
        depth = 'deep_extended'
    elif total_words > 1000 and len(chat_history) > 10:
        depth = 'substantial'
    elif total_words > 500:
        depth = 'moderate'
    else:
        depth = 'light'

    return {
        'success': True,
        'message_count': len(chat_history),
        'dimensions': dimensions.get('dimensions', {}),
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_chars': total_chars,
            'total_words': total_words,
            'depth': depth
        },
        'details': dimensions.get('details', {})
    }
