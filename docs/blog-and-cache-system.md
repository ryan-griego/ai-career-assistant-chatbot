# Blog Integration & Semantic Caching System

## Overview

This system extends the AI Career Assistant with two powerful features:

1. **Automated Blog Scraping**: Periodically fetches and includes blog articles in chat context
2. **Semantic Caching**: Uses embeddings to reduce OpenAI API costs by caching similar queries

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Query                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Semantic Cache Check                            │
│  • Generate query embedding                                  │
│  • Search for similar cached queries (cosine similarity)     │
│  • If similarity > 92% → return cached response             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Cache Miss
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Load Context with Blog Articles                    │
│  • Resume + LinkedIn + Summary                               │
│  • Latest 10 blog articles from ryangriego.com/blog         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Generate AI Response                            │
│  • Main LLM with full context                               │
│  • Evaluator LLM validates response                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Cache Response for Future Queries                  │
│  • Store query embedding + response                          │
│  • Associated with context hash                              │
└─────────────────────────────────────────────────────────────┘

Background Scheduler:
  • Sunday 2 AM → Update blog articles
  • Daily 3 AM → Clean old cache entries (30+ days)
```

## Components

### 1. Blog Scraper (`models/blog_scraper.py`)

Fetches articles from your blog:

```python
from models.blog_scraper import BlogScraper

scraper = BlogScraper("https://ryangriego.com/blog")
articles = scraper.scrape_all_articles_with_content()

for article in articles:
    print(f"{article.title} - {article.date}")
```

**Features:**
- Parses blog index page for article metadata
- Fetches full article content
- Generates content hashes for change detection
- Formats articles for chat context

### 2. Blog Manager (`models/blog_manager.py`)

Manages blog content with versioning:

```python
from models.blog_manager import BlogManager

manager = BlogManager(
    storage_path="data/blog_articles.json",
    blog_url="https://ryangriego.com/blog"
)

# Force update
stats = manager.update_articles(force=True)
# {'new': 2, 'updated': 1, 'unchanged': 3}

# Get context for chat
context = manager.get_articles_as_context(max_articles=10)

# Search articles
matches = manager.search_articles("AI")
```

**Features:**
- Stores articles in JSON with metadata
- Detects new/updated/unchanged articles
- Weekly update scheduling (configurable)
- Content hashing for cache invalidation
- Article search functionality

### 3. Semantic Cache (`models/semantic_cache.py`)

Caches responses using embeddings:

```python
from models.semantic_cache import SemanticCache
from openai import OpenAI

cache = SemanticCache(
    db_path="data/semantic_cache.db",
    similarity_threshold=0.92,
    cache_ttl_days=30,
    openai_client=OpenAI()
)

# Check cache
context_hash = "abc123"
result = cache.get_cached_response("What companies has Ryan worked for?", context_hash)

if result:
    response, similarity = result
    print(f"Cache hit! Similarity: {similarity}")
else:
    # Generate new response
    response = "Ryan has worked for..."
    cache.cache_response("What companies has Ryan worked for?", response, context_hash)
```

**How It Works:**

1. **Embedding Generation**: Uses OpenAI's `text-embedding-3-small` model (cheaper than ada-002)
2. **Similarity Search**: Compares query embedding with all cached embeddings using cosine similarity
3. **Threshold Matching**: Returns cached response if similarity ≥ 92%
4. **Context Validation**: Only returns cache if context hash matches (prevents stale data)

**Cost Savings:**

- **Embedding cost**: $0.00002 per 1K tokens (~0.2¢ per query)
- **GPT-4o-mini cost**: $0.00015 per 1K input tokens + $0.0006 per 1K output
- **Savings**: ~95% cost reduction on cache hits

Example:
- 100 similar queries without cache: $0.50
- 100 similar queries with cache (90% hit rate): $0.05 + (10 * $0.005) = $0.10
- **Savings: $0.40 (80%)**

### 4. Scheduler (`models/scheduler.py`)

Background task scheduler:

```python
from models.scheduler import BlogUpdateScheduler

scheduler = BlogUpdateScheduler(blog_manager, semantic_cache)

# Schedule tasks
scheduler.schedule_tasks()

# Run in background thread
import threading
thread = threading.Thread(target=scheduler.run, daemon=True)
thread.start()
```

**Schedule:**
- **Blog Updates**: Every Sunday at 2:00 AM
- **Cache Cleanup**: Daily at 3:00 AM

## Integration with Career Chatbot

The system is fully integrated into `CareerChatbot`:

```python
from career_chatbot import CareerChatbot
from models import ChatbotConfig

config = ChatbotConfig(name="Ryan Griego", github_username="ryan-griego")
chatbot = CareerChatbot(config)

# Blog articles automatically loaded
# Semantic cache automatically checked
# Scheduler can be started separately

response = chatbot.chat("What projects have you worked on?", [])
```

### Startup Flow:

1. Initialize blog manager
2. Update blog articles (if 7+ days since last update)
3. Initialize semantic cache
4. Load context (resume + LinkedIn + summary + blog)
5. Generate context hash
6. Ready to chat!

### Chat Flow:

1. User asks question
2. Generate context hash (includes blog content)
3. Check semantic cache with query + context hash
4. If cache hit → return cached response ✅
5. If cache miss → generate response → cache it 💾

## Database Structure

### Blog Articles (`data/blog_articles.json`)

```json
{
  "articles": [
    {
      "title": "Building an AI Career Assistant",
      "date": "October 15, 2025",
      "tags": ["AI", "Python", "OpenAI"],
      "summary": "How I built...",
      "url": "https://ryangriego.com/blog/ai-career-assistant",
      "content": "Full article text...",
      "content_hash": "abc123def456"
    }
  ],
  "last_update": "2025-10-22T14:30:00"
}
```

### Semantic Cache (`data/semantic_cache.db`)

```sql
CREATE TABLE response_cache (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL,
    query_embedding BLOB NOT NULL,  -- JSON-encoded embedding
    response TEXT NOT NULL,
    context_hash TEXT NOT NULL,     -- For cache invalidation
    created_at TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 1
);
```

## Configuration

### Environment Variables

All existing `.env` variables work. No new variables required!

```env
OPENAI_API_KEY=sk-...
GITHUB_USERNAME=ryan-griego
PUSHOVER_USER=...
PUSHOVER_TOKEN=...
```

### Tuning Parameters

**Semantic Cache:**
```python
similarity_threshold=0.92  # Higher = stricter matching (0.85-0.95 recommended)
cache_ttl_days=30          # How long to keep cache entries
```

**Blog Manager:**
```python
max_articles=10            # How many articles to include in context
```

## Testing

### Test Blog Scraper

```bash
cd /Volumes/HomeX/ryangriegox/Desktop/projects/ai-career_chatbot
python -m models.blog_scraper
```

### Test Semantic Cache

```bash
python -m models.semantic_cache
```

### Test Blog Manager

```bash
python -m models.blog_manager
```

### Test Scheduler

```bash
python -m models.scheduler
```

## Monitoring & Analytics

### Cache Statistics

```python
stats = chatbot.semantic_cache.get_cache_stats()
print(stats)
# {
#   'total_entries': 150,
#   'total_accesses': 450,
#   'reused_entries': 120,
#   'avg_reuse': 3.75,
#   'cache_hit_rate': '80.0%'
# }
```

### Blog Update Status

```python
if chatbot.blog_manager.should_update():
    print("Blog update due")
else:
    days_remaining = 7 - (datetime.now() - chatbot.blog_manager.last_update).days
    print(f"Next update in {days_remaining} days")
```

## Deployment Considerations

### Hugging Face Spaces

The system works on HF Spaces with minimal changes:

1. **Persistence**: Blog and cache data stored in `data/` directory
2. **Scheduler**: Can be disabled or run with `gradio.mount_gradio_app()`
3. **Storage**: SQLite database suitable for free tier

### Production Deployment

For high-traffic production:

1. **Use Vector Database**: Replace SQLite with Pinecone/Weaviate for better scaling
2. **Separate Scheduler**: Run scheduler as independent service
3. **CDN for Blog**: Cache blog content in CDN, webhook for updates
4. **Redis Cache**: Add Redis layer for ultra-fast cache hits

## Cost Analysis

### Without Caching (1000 queries/day)

- **API Calls**: 1000 queries × 2500 tokens avg × $0.0006 = **$1.50/day**
- **Monthly**: **$45**

### With Caching (1000 queries/day, 70% hit rate)

- **Embeddings**: 1000 × 100 tokens × $0.00002 = $0.002/day
- **Cache Hits**: 700 queries × $0 = $0
- **Cache Misses**: 300 queries × $0.0015 = $0.45/day
- **Daily Total**: **$0.45/day**
- **Monthly**: **$13.50** (70% savings!)

### At Scale (10,000 queries/day, 80% hit rate)

- **Without cache**: $450/month
- **With cache**: $60/month
- **Savings**: **$390/month**

## Best Practices

### 1. Cache Invalidation

The system automatically invalidates cache when:
- Blog articles are updated (content hash changes)
- Resume/LinkedIn is modified (context hash changes)

Force cache clear:
```python
chatbot.semantic_cache.clear_cache()
```

### 2. Similarity Threshold Tuning

- **0.95-0.98**: Very strict (exact matches only)
- **0.90-0.94**: Balanced (recommended)
- **0.85-0.89**: Lenient (more cache hits, less precise)

Test with your data:
```python
# Test query similarity
q1 = "What companies has Ryan worked for?"
q2 = "Which companies did Ryan work at?"

e1 = cache._generate_embedding(q1)
e2 = cache._generate_embedding(q2)
similarity = cache._cosine_similarity(e1, e2)
print(f"Similarity: {similarity}")  # ~0.94
```

### 3. Blog Update Frequency

Weekly updates balance freshness with API costs:
- **Daily**: Very fresh, higher costs
- **Weekly**: Good balance (recommended)
- **Monthly**: Lower costs, less fresh content

Adjust in scheduler:
```python
# Daily updates
schedule.every().day.at("02:00").do(self.update_blog_content)

# Bi-weekly
schedule.every(14).days.do(self.update_blog_content)
```

### 4. Context Size Management

Monitor token usage:
```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o-mini")
tokens = len(enc.encode(context['blog']))
print(f"Blog context uses {tokens} tokens")
```

If blog content is too large:
- Reduce `max_articles` (currently 10)
- Include summaries only (set `content=""`)
- Use article search to include only relevant posts

## Troubleshooting

### Issue: Cache always misses

**Cause**: Context hash changing between queries

**Solution**: Check context stability
```python
hash1 = chatbot.get_context_hash()
# Make a query
hash2 = chatbot.get_context_hash()
assert hash1 == hash2, "Context is changing!"
```

### Issue: Blog scraper fails

**Cause**: Website structure changed

**Solution**: Update CSS selectors in `blog_scraper.py`:
```python
# Check current structure
response = requests.get("https://ryangriego.com/blog")
soup = BeautifulSoup(response.text, 'html.parser')
print(soup.prettify())  # Inspect structure
```

### Issue: High embedding costs

**Cause**: Too many cache checks

**Solution**:
- Increase `similarity_threshold` to reduce false positives
- Add bloom filter for quick negative matches
- Batch embedding generation

### Issue: Stale blog content

**Cause**: Scheduler not running or update check disabled

**Solution**:
```python
# Force update
chatbot.blog_manager.update_articles(force=True)

# Check status
print(chatbot.blog_manager.last_update)
```

## Future Enhancements

### 1. Webhook-Based Updates

Instead of polling:
```python
@app.post("/webhook/blog-updated")
def blog_updated():
    chatbot.blog_manager.update_articles(force=True)
    chatbot.semantic_cache.clear_cache()  # Invalidate cache
    return {"status": "updated"}
```

### 2. Multi-Level Caching

```
L1: In-memory LRU (instant)
L2: Semantic cache (embedding-based)
L3: Full context cache (hash-based)
```

### 3. Analytics Dashboard

Track:
- Cache hit rates over time
- Most asked questions
- Blog article popularity
- Cost savings metrics

### 4. Smart Context Selection

Instead of including all 10 articles, use embeddings to include only relevant ones:

```python
def get_relevant_articles(query, max_articles=3):
    query_embedding = get_embedding(query)
    article_embeddings = [get_embedding(a.content) for a in articles]
    similarities = [cosine_sim(query_embedding, ae) for ae in article_embeddings]
    top_indices = argsort(similarities)[-max_articles:]
    return [articles[i] for i in top_indices]
```

## Summary

This system provides:

✅ **Automated blog integration** - Weekly updates, no manual work
✅ **Cost optimization** - 70-80% reduction in API costs via semantic caching
✅ **Context awareness** - Chat knows about blog articles and projects
✅ **Cache invalidation** - Automatic when content changes
✅ **Production ready** - Works on HF Spaces and local deployments
✅ **Monitoring** - Built-in statistics and logging

The chatbot now has access to your complete professional brand: resume, LinkedIn, career summary, **and all blog articles**, while intelligently caching responses to minimize costs.
