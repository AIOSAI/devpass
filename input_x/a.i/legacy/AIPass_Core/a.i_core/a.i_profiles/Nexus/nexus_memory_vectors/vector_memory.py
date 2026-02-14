import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Configuration
MEMORY_POOL = Path(r"C:\AIPass-Ecosystem\a.i\legacy\AIPass_Core\a.i_core\a.i_profiles\Nexus")
VECTOR_MEMORY_FILE = MEMORY_POOL / "vector_memories.json"
MAX_VECTOR_MEMORIES = 5000  # Configurable limit - set to whatever you want


def create_simple_vector(text: str) -> list[float]:
    """Create a simple deterministic vector from text using hash-based approach."""
    # Use SHA256 hash to create deterministic "vector"
    hash_bytes = hashlib.sha256(text.encode('utf-8')).digest()
    
    # Convert first 32 bytes to normalized floats (simple vector)
    vector = []
    for i in range(0, min(32, len(hash_bytes)), 4):
        # Take 4 bytes, convert to int, normalize to [-1, 1]
        chunk = hash_bytes[i:i+4]
        if len(chunk) == 4:
            val = int.from_bytes(chunk, 'big')
            normalized = (val / (2**32)) * 2 - 1  # Normalize to [-1, 1]
            vector.append(round(normalized, 6))
    
    return vector

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Calculate magnitudes
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

def load_vector_memories_data() -> dict:
    """Load vector memories data structure."""
    if not VECTOR_MEMORY_FILE.exists():
        return {"next_id": 1, "memories": []}
    
    try:
        with VECTOR_MEMORY_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle old format (just array) vs new format (dict with metadata)
            if isinstance(data, list):
                return {"next_id": 1, "memories": data}
            else:
                return data
                
    except (json.JSONDecodeError, FileNotFoundError):
        logger.warning("Failed to load vector memories")
        return {"next_id": 1, "memories": []}

def save_vector_memories(data: dict) -> bool:
    """Save vector memories data structure to file."""
    try:
        # Create directory if it doesn't exist
        MEMORY_POOL.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with VECTOR_MEMORY_FILE.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save vector memories: {e}")
        return False

def search_vector_memories(query: str, top_k: int = 5, min_similarity: float = 0.1) -> List[Dict]:
    """
    Search vector memories using semantic similarity.
    
    Args:
        query: Search query text
        top_k: Number of top results to return
        min_similarity: Minimum similarity threshold
        
    Returns:
        List of matching memory entries with similarity scores
    """
    try:
        # Load vector memories
        data = load_vector_memories_data()
        memories = data.get("memories", [])
        
        if not memories:
            return []
        
        # Create query vector
        query_vector = create_simple_vector(query.lower().strip())
        
        # Calculate similarities
        results = []
        for memory in memories:
            memory_vector = memory.get('vector', [])
            if not memory_vector:
                continue
                
            similarity = cosine_similarity(query_vector, memory_vector)
            
            if similarity >= min_similarity:
                results.append({
                    'memory': memory,
                    'similarity': similarity,
                    'id': memory.get('id'),
                    'timestamp': memory.get('timestamp'),
                    'created_at': memory.get('created_at')
                })
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top_k results
        return results[:top_k]
        
    except Exception as e:
        logger.error(f"Vector memory search failed: {e}")
        return []

def get_memory_context_for_query(query: str) -> str:
    """
    Get formatted memory context for a search query.
    
    Args:
        query: Search query
        
    Returns:
        Formatted string with relevant memories
    """
    results = search_vector_memories(query, top_k=3, min_similarity=0.15)
    
    if not results:
        return f"No relevant memories found for: {query}"
    
    context_lines = [f"🧠 MEMORY SEARCH: '{query}'"]
    context_lines.append(f"Found {len(results)} relevant memories:\n")
    
    for i, result in enumerate(results, 1):
        memory = result['memory']
        similarity = result['similarity']
        timestamp = result.get('timestamp', 'unknown')
        memory_id = result.get('id', 'unknown')
        
        # Try to parse timestamp for better formatting
        try:
            if timestamp != 'unknown':
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "unknown time"
        except:
            time_str = str(timestamp)[:16]  # Fallback
        
        context_lines.append(f"{i}. [{time_str}] (ID: {memory_id}, similarity: {similarity:.2f})")
        
        # Note: We don't have the original summary text stored in current format
        # This would need to be added to the vector memory structure
        context_lines.append("   [Memory content would be displayed here]")
        context_lines.append("")
    
    return "\n".join(context_lines)

def search_memories_by_timeframe(days_back: int = 7) -> List[Dict]:
    """
    Get memories from a specific timeframe.
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        List of memories from the timeframe
    """
    try:
        data = load_vector_memories_data()
        memories = data.get("memories", [])
        
        if not memories:
            return []
        
        # Calculate cutoff date
        cutoff = datetime.utcnow().timestamp() - (days_back * 24 * 60 * 60)
        
        # Filter memories by timeframe
        recent_memories = []
        for memory in memories:
            try:
                timestamp_str = memory.get('timestamp', '')
                if timestamp_str:
                    # Parse timestamp
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if dt.timestamp() >= cutoff:
                        recent_memories.append(memory)
            except:
                continue  # Skip memories with bad timestamps
        
        # Sort by timestamp (newest first)
        recent_memories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return recent_memories
        
    except Exception as e:
        logger.error(f"Timeframe search failed: {e}")
        return []

def get_vector_memory_stats() -> Dict:
    """Get comprehensive vector memory statistics."""
    try:
        data = load_vector_memories_data()
        memories = data.get("memories", [])
        
        if not memories:
            return {
                'total_memories': 0,
                'searchable': False,
                'status': 'empty'
            }
        
        # Get ID range
        ids = [m.get('id', 0) for m in memories if 'id' in m]
        min_id = min(ids) if ids else 0
        max_id = max(ids) if ids else 0
        
        # Get time range
        timestamps = []
        for m in memories:
            try:
                ts = m.get('timestamp', '')
                if ts:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    timestamps.append(dt)
            except:
                continue
        
        oldest_time = min(timestamps) if timestamps else None
        newest_time = max(timestamps) if timestamps else None
        
        # Calculate memory span
        memory_span = "unknown"
        if oldest_time and newest_time:
            span = newest_time - oldest_time
            if span.days > 0:
                memory_span = f"{span.days} days"
            else:
                memory_span = f"{span.seconds // 3600} hours"
        
        return {
            'total_memories': len(memories),
            'id_range': f"{min_id}-{max_id}",
            'memory_span': memory_span,
            'oldest_memory': oldest_time.strftime("%Y-%m-%d") if oldest_time else None,
            'newest_memory': newest_time.strftime("%Y-%m-%d") if newest_time else None,
            'searchable': True,
            'status': 'ready'
        }
        
    except Exception as e:
        logger.error(f"Stats calculation failed: {e}")
        return {
            'total_memories': 0,
            'searchable': False,
            'status': f'error: {e}'
        }

# Add these search functions to natural_flow.py for Nexus to use

def search_my_memories(query: str) -> str:
    """
    Natural language interface for Nexus to search his vector memories.
    
    Usage in conversation:
    - "Let me search my memories for cortex improvements"
    - "I need to recall our discussion about vector systems"
    """
    try:
        print(f"[Memory Search] Searching for: {query}")
        
        results = search_vector_memories(query, top_k=3, min_similarity=0.15)
        
        if not results:
            return f"I searched my memory for '{query}' but didn't find any relevant conversations. My memory might not have captured that topic, or we might have discussed it using different terms."
        
        # Format results for natural conversation
        response_lines = [f"I found {len(results)} relevant memories about '{query}':\n"]
        
        for i, result in enumerate(results, 1):
            memory = result['memory']
            similarity = result['similarity']
            timestamp = result.get('timestamp', 'unknown')
            
            # Format timestamp
            try:
                if timestamp != 'unknown':
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    if dt.date() == datetime.now().date():
                        time_str = f"today at {dt.strftime('%H:%M')}"
                    elif (datetime.now() - dt).days == 1:
                        time_str = f"yesterday at {dt.strftime('%H:%M')}"
                    elif (datetime.now() - dt).days < 7:
                        time_str = f"{(datetime.now() - dt).days} days ago"
                    else:
                        time_str = dt.strftime("%B %d")
                else:
                    time_str = "unknown time"
            except:
                time_str = "some time ago"
            
            confidence = "strong" if similarity > 0.7 else "moderate" if similarity > 0.4 else "weak"
            
            response_lines.append(f"{i}. Memory from {time_str} ({confidence} match)")
            # Note: We'd need to store original summary text to show actual content
            response_lines.append(f"   [Memory content would be recalled here]")
            response_lines.append("")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        return f"I encountered an error while searching my memories: {e}"

def get_memory_summary() -> str:
    """Get a brief summary of vector memory status for system awareness."""
    stats = get_vector_memory_stats()
    
    if not stats['searchable']:
        return "Vector Memory: No stored memories available"
    
    return f"Vector Memory: {stats['total_memories']} memories stored, span: {stats['memory_span']}, searchable: {stats['status']}"

def add_summary_to_vectors(summary_entry: dict) -> bool:
    """
    Add a summary entry to vector memory system.
    
    Args:
        summary_entry: Dict with 'timestamp' and 'summary' keys
        
    Returns:
        bool: True if successfully added, False otherwise
    """
    try:
        # Load existing memories with metadata
        data = load_vector_memories_data()
        memories = data["memories"]
        next_id = data["next_id"]
        
        # Create vector from summary text
        summary_text = summary_entry.get('summary', '')
        if not summary_text:
            logger.warning("Empty summary text, skipping vector creation")
            return False
            
        vector = create_simple_vector(summary_text)
        
        # Create vector memory entry with incrementing ID
        vector_entry = {
            'id': next_id,
            'timestamp': summary_entry.get('timestamp'),
            'vector': vector,
            'created_at': datetime.utcnow().isoformat(),
            'vector_length': len(vector)
        }
        
        # Add to memories (newest first)
        memories.insert(0, vector_entry)
        
        # Enforce limit - remove oldest entries
        removed_count = 0
        if len(memories) > MAX_VECTOR_MEMORIES:
            removed_count = len(memories) - MAX_VECTOR_MEMORIES
            memories = memories[:MAX_VECTOR_MEMORIES]
            logger.info(f"Removed {removed_count} old vector memories (limit: {MAX_VECTOR_MEMORIES})")
        
        # Update data structure
        data["memories"] = memories
        data["next_id"] = next_id + 1  # Always increment, never reset
        
        # Save back to file
        save_vector_memories(data)
        
        logger.info(f"Added vector memory ID {next_id}: {summary_text[:50]}...")
        if removed_count > 0:
            logger.info(f"Purged {removed_count} oldest entries")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to add summary to vectors: {e}")
        return False

# Test function
def test_memory_search():
    """Test the memory search functionality."""
    print("Testing vector memory search...")
    
    # Test basic search
    results = search_vector_memories("cortex system", top_k=3)
    print(f"Search results: {len(results)} found")
    
    for result in results:
        print(f"  ID: {result['id']}, Similarity: {result['similarity']:.3f}")
    
    # Test stats
    stats = get_vector_memory_stats()
    print(f"Memory stats: {stats}")
    
    # Test summary
    summary = get_memory_summary()
    print(f"Summary: {summary}")

if __name__ == "__main__":
    test_memory_search()