# symbolic_memory.py - Real extraction functions
import json
import re
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import Counter

# Configuration
COMPRESSION_CONFIG = {
    "target_words": 20,
    "max_compression_ratio": 1000,
    "min_compression_ratio": 10,
    "vector_storage_path": "symbolic_vectors.json"
}

def set_compression_target(words):
    COMPRESSION_CONFIG["target_words"] = words

def get_compression_target():
    return COMPRESSION_CONFIG["target_words"]

def extract_technical_flow(chat_history):
    """Analyze actual technical patterns from conversation"""
    if not chat_history:
        return ["no_conversation"]
    
    patterns = []
    technical_indicators = {
        "problems": ["error", "bug", "issue", "problem", "broken", "fail", "wrong"],
        "debugging": ["debug", "trace", "check", "test", "try", "attempt"],
        "solutions": ["fix", "solve", "work", "success", "breakthrough", "got it"],
        "struggle": ["stuck", "confused", "difficult", "hard", "frustrating"],
        "learning": ["understand", "learn", "realize", "discover", "insight"]
    }
    
    # Analyze message flow for technical progression
    for i, message in enumerate(chat_history):
        content = message.get("content", "").lower()
        role = message.get("role", "")
        
        # Check for technical keywords
        for category, keywords in technical_indicators.items():
            if any(keyword in content for keyword in keywords):
                patterns.append(f"{category}_{role}")
    
    # Detect common technical flows
    pattern_string = " ".join(patterns)
    
    if "problems" in pattern_string and "solutions" in pattern_string:
        if "struggle" in pattern_string:
            return ["problem_struggle_breakthrough"]
        else:
            return ["problem_solution_flow"]
    elif "debugging" in pattern_string:
        return ["debugging_session"]
    elif "learning" in pattern_string:
        return ["learning_conversation"]
    else:
        return ["general_technical"]

def extract_emotional_journey(chat_history):
    """Detect emotional arc from conversation tone and patterns"""
    if not chat_history:
        return ["neutral"]
    
    emotions = []
    
    # Emotional indicators
    emotional_markers = {
        "frustration": ["frustrated", "annoying", "difficult", "stuck", "ugh", "damn"],
        "excitement": ["cool", "awesome", "great", "amazing", "perfect", "brilliant"],
        "confidence": ["sure", "certain", "definitely", "absolutely", "know"],
        "uncertainty": ["maybe", "possibly", "not sure", "think", "guess"],
        "breakthrough": ["got it", "understand", "works", "success", "finally"],
        "curiosity": ["wonder", "curious", "interesting", "what if", "how"]
    }
    
    # Analyze progression through conversation
    emotion_timeline = []
    
    for message in chat_history:
        content = message.get("content", "").lower()
        role = message.get("role", "")
        
        message_emotions = []
        for emotion, markers in emotional_markers.items():
            if any(marker in content for marker in markers):
                message_emotions.append(emotion)
        
        if message_emotions:
            emotion_timeline.append((role, message_emotions))
    
    # Extract emotional arc pattern
    if not emotion_timeline:
        return ["neutral_tone"]
    
    # Look for common emotional progressions
    all_emotions = [emotion for _, emotions in emotion_timeline for emotion in emotions]
    
    if "frustration" in all_emotions and "breakthrough" in all_emotions:
        return ["frustration_to_breakthrough"]
    elif "curiosity" in all_emotions and "excitement" in all_emotions:
        return ["curiosity_to_excitement"]
    elif "uncertainty" in all_emotions and "confidence" in all_emotions:
        return ["uncertainty_to_confidence"]
    else:
        # Return most common emotions
        emotion_counts = Counter(all_emotions)
        return [emotion for emotion, _ in emotion_counts.most_common(2)]

def extract_collaboration_patterns(chat_history):
    """Identify relationship dynamics and interaction patterns"""
    if not chat_history:
        return ["no_interaction"]
    
    patterns = []
    user_messages = [msg for msg in chat_history if msg.get("role") == "user"]
    assistant_messages = [msg for msg in chat_history if msg.get("role") == "assistant"]
    
    if not user_messages or not assistant_messages:
        return ["one_sided_conversation"]
    
    # Analyze message characteristics
    avg_user_length = sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)
    avg_assistant_length = sum(len(msg.get("content", "")) for msg in assistant_messages) / len(assistant_messages)
    
    # Detect interaction styles
    if avg_user_length > avg_assistant_length * 1.5:
        patterns.append("user_directed")
    elif avg_assistant_length > avg_user_length * 1.5:
        patterns.append("assistant_detailed")
    else:
        patterns.append("balanced_exchange")
    
    # Analyze question patterns
    user_questions = sum(1 for msg in user_messages if "?" in msg.get("content", ""))
    if user_questions > len(user_messages) * 0.6:
        patterns.append("question_heavy")
    
    # Detect coaching/teaching patterns
    coaching_indicators = ["try", "let's", "what if", "how about", "consider"]
    teaching_indicators = ["explain", "show", "understand", "learn", "because"]
    
    user_content = " ".join(msg.get("content", "").lower() for msg in user_messages)
    assistant_content = " ".join(msg.get("content", "").lower() for msg in assistant_messages)
    
    if any(indicator in user_content for indicator in coaching_indicators):
        patterns.append("user_coaching")
    if any(indicator in assistant_content for indicator in teaching_indicators):
        patterns.append("assistant_teaching")
    
    # Detect collaborative building
    build_indicators = ["let's build", "we can", "together", "collaborate"]
    if any(indicator in user_content + assistant_content for indicator in build_indicators):
        patterns.append("collaborative_building")
    
    return patterns if patterns else ["standard_interaction"]

def extract_key_learnings(chat_history):
    """Extract core insights and lessons from conversation"""
    if not chat_history:
        return ["no_insights"]
    
    insights = []
    
    # Learning indicators
    learning_patterns = {
        "discovery": ["discovered", "found out", "realized", "learned"],
        "problem_solving": ["solution", "approach", "method", "way to"],
        "understanding": ["understand", "makes sense", "clear", "see"],
        "improvement": ["better", "improve", "optimize", "enhance"],
        "mistakes": ["wrong", "mistake", "error", "incorrect"]
    }
    
    all_content = " ".join(msg.get("content", "").lower() for msg in chat_history)
    
    for category, indicators in learning_patterns.items():
        if any(indicator in all_content for indicator in indicators):
            insights.append(category)
    
    # Extract specific technical insights
    if "module" in all_content and "toggle" in all_content:
        insights.append("module_system_learning")
    if "memory" in all_content and "compression" in all_content:
        insights.append("memory_system_learning")
    if "debug" in all_content and "fix" in all_content:
        insights.append("debugging_skills")
    
    return insights if insights else ["general_conversation"]

def compress_to_symbols(essence_dict, target_words):
    """Convert essence to compressed symbolic format with better logic"""
    symbols = []
    
    # Prioritize by importance for compression
    priority_order = ["insights", "technical", "emotional", "relationship"]
    
    for category in priority_order:
        if category in essence_dict and isinstance(essence_dict[category], list):
            # Add category prefix for clarity
            category_symbols = [f"{category}:{item}" for item in essence_dict[category][:3]]  # Limit each category
            symbols.extend(category_symbols)
    
    # Add timestamp info if space allows
    if len(symbols) < target_words - 2:
        if "timestamp" in essence_dict:
            date_part = essence_dict["timestamp"][:10]  # Just date
            symbols.append(f"date:{date_part}")
    
    # Compress to target word count
    if len(symbols) > target_words:
        symbols = symbols[:target_words]
    
    return " ".join(symbols)

def analyze_conversation_depth(chat_history):
    """Analyze how deep/complex the conversation was"""
    if not chat_history:
        return "shallow"
    
    total_words = sum(len(msg.get("content", "").split()) for msg in chat_history)
    message_count = len(chat_history)
    
    if total_words > 2000 and message_count > 20:
        return "deep_extended"
    elif total_words > 1000 and message_count > 10:
        return "substantial"
    elif total_words > 500:
        return "moderate"
    else:
        return "light"

def extract_context_triggers(chat_history):
    """Extract keywords that should trigger this memory in future conversations"""
    if not chat_history:
        return []
    
    # Extract significant nouns and technical terms
    all_content = " ".join(msg.get("content", "") for msg in chat_history).lower()
    
    # Common technical terms that should trigger memories
    technical_terms = re.findall(r'\b(?:module|system|debug|memory|compression|vector|symbolic|cortex|registry|toggle|profile|chat|context|api|token|embedding|storage|json|function|method|class|import|file|script|error|fix|solution|breakthrough|pattern|analysis|extraction|conversation|interaction|collaboration|learning|insight|discovery)\b', all_content)
    
    # Get unique terms, most frequent first
    term_counts = Counter(technical_terms)
    return [term for term, count in term_counts.most_common(10) if count > 1]

def store_as_vector(essence, conversation_id):
    """Store symbolic essence as vector embedding"""
    vector_data = {
        "id": conversation_id,
        "essence": essence,
        "embedding": generate_embedding(essence),
        "stored_at": datetime.now().isoformat()
    }
    
    # Load existing vectors
    vectors = load_vector_storage()
    vectors[conversation_id] = vector_data
    save_vector_storage(vectors)
    
    return vector_data

def retrieve_relevant(current_context, similarity_threshold=0.7):
    """Find relevant symbolic memories"""
    query_embedding = generate_embedding(current_context)
    vectors = load_vector_storage()
    
    relevant_memories = []
    for conv_id, data in vectors.items():
        similarity = calculate_similarity(query_embedding, data["embedding"])
        if similarity > similarity_threshold:
            relevant_memories.append({
                "conversation_id": conv_id,
                "essence": data["essence"],
                "similarity": similarity
            })
    
    return sorted(relevant_memories, key=lambda x: x["similarity"], reverse=True)

def generate_embedding(text):
    """Generate vector embedding (simplified)"""
    # In real implementation, use actual embedding model
    words = text.split()
    return np.random.rand(20).tolist()  # Placeholder embedding

def calculate_similarity(embedding1, embedding2):
    """Calculate cosine similarity"""
    a = np.array(embedding1)
    b = np.array(embedding2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_vector_storage():
    """Load stored vectors"""
    storage_path = Path(COMPRESSION_CONFIG["vector_storage_path"])
    if storage_path.exists():
        with open(storage_path, 'r') as f:
            return json.load(f)
    return {}

def save_vector_storage(vectors):
    """Save vectors to storage"""
    storage_path = Path(COMPRESSION_CONFIG["vector_storage_path"])
    with open(storage_path, 'w') as f:
        json.dump(vectors, f, indent=2)

def end_chat_compression(chat_history, conversation_id):
    """Complete end-of-chat symbolic memory storage"""
    essence = compress_conversation(chat_history)
    vector_data = store_as_vector(essence, conversation_id)
    
    print(f"Stored symbolic memory: {len(chat_history)} words → {COMPRESSION_CONFIG['target_words']} symbols")
    return vector_data

def start_chat_context(current_topic):
    """Load relevant symbolic memories for new chat"""
    relevant = retrieve_relevant(current_topic)
    context = load_essence_for_context(relevant)
    
    print(f"Loaded {len(relevant)} relevant symbolic memories")
    return context

def load_essence_for_context(relevant_memories):
    """Convert symbolic memories back to context"""
    context_essence = []
    for memory in relevant_memories[:3]:  # Top 3 most relevant
        context_essence.append(memory["essence"])
    
    return merge_symbolic_contexts(context_essence)

def merge_symbolic_contexts(contexts):
    """Merge multiple symbolic contexts"""
    merged = {
        "combined_patterns": [],
        "dominant_emotions": [],
        "relationship_continuity": []
    }
    
    for context in contexts:
        # Merge logic here
        pass
    
    return merged

def analyze_and_compress(chat_history, target_words):
    """Extract symbolic essence from conversation using real analysis"""
    # Real pattern extraction
    technical_patterns = extract_technical_flow(chat_history)
    emotional_arc = extract_emotional_journey(chat_history) 
    relationship_dynamics = extract_collaboration_patterns(chat_history)
    core_insights = extract_key_learnings(chat_history)
    context_triggers = extract_context_triggers(chat_history)
    conversation_depth = analyze_conversation_depth(chat_history)
    
    # Calculate actual compression ratio
    total_chars = sum(len(msg.get("content", "")) for msg in chat_history)
    
    # Enhanced symbolic compression
    essence = {
        "technical": technical_patterns,
        "emotional": emotional_arc,
        "relationship": relationship_dynamics,
        "insights": core_insights,
        "triggers": context_triggers[:5],  # Top 5 trigger words
        "depth": conversation_depth,
        "timestamp": datetime.now().isoformat(),
        "message_count": len(chat_history),
        "compression_ratio": total_chars / target_words if target_words > 0 else 0
    }
    
    return compress_to_symbols(essence, target_words)

def compress_conversation(chat_history, target_words=None):
    """Main compression function"""
    if target_words is None:
        target_words = COMPRESSION_CONFIG["target_words"]
    
    return analyze_and_compress(chat_history, target_words)