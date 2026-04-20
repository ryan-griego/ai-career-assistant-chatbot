# Quick Start: Blog Integration & Semantic Caching

## What's New?

Your AI Career Assistant now automatically:
1. **Scrapes your blog** weekly for new articles
2. **Includes blog content** in chat context
3. **Caches responses** to save 70-80% on OpenAI costs

## Installation

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

New packages:
- `beautifulsoup4` - Web scraping
- `numpy` - Vector operations for embeddings
- `schedule` - Background task scheduling

### 2. Run Tests

Test that everything works:

```bash
python test_blog_cache.py
```

This will:
- ✅ Scrape your blog at https://ryangriego.com/blog
- ✅ Store articles in `data/blog_articles.json`
- ✅ Test semantic cache with sample queries
- ✅ Show cache statistics

### 3. Run the Chatbot

```bash
python career_chatbot.py
```

On startup, it will:
- 📡 Check for blog updates (weekly automatic checks)
- 💾 Initialize semantic cache
- 📚 Load blog articles into context
- ✅ Ready to chat!

## How It Works

### Blog Integration

```
┌──────────────────────────────────────────────────────┐
│           Weekly (Every Sunday 2 AM)                 │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│  1. Scrape https://ryangriego.com/blog               │
│  2. Detect new/updated/unchanged articles            │
│  3. Save to data/blog_articles.json                  │
│  4. Update context hash                              │
└──────────────────────────────────────────────────────┘
```

Your blog articles are now part of the AI's knowledge!

**Ask about your blog:**
- "What blog posts have I written?"
- "Tell me about my AI projects"
- "What technologies have I written about?"

### Semantic Caching

```
┌──────────────────────────────────────────────────────┐
│  User Query: "What companies has Ryan worked for?"   │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│  Generate Embedding (text-embedding-3-small)         │
│  Cost: $0.00002 per query                            │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│  Search Cache for Similar Queries                    │
│  Using Cosine Similarity (>92% threshold)            │
└───────────────────┬──────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼ Cache Hit             ▼ Cache Miss
┌──────────────────┐    ┌──────────────────────────┐
│ Return Cached    │    │ Generate Response        │
│ Response         │    │ Cost: ~$0.001            │
│ Cost: $0.00002   │    │                          │
│ (99% savings!)   │    │ Cache for Next Time      │
└──────────────────┘    └──────────────────────────┘
```

### Similar Queries Matched by Cache

These queries would all match (>92% similarity):
- "What companies has Ryan worked for?"
- "Which companies did Ryan work at?"
- "Where has Ryan been employed?"
- "Tell me about Ryan's work history"

## Configuration

### Change Blog URL

Edit `career_chatbot.py`:

```python
self.blog_manager = BlogManager(
    storage_path="data/blog_articles.json",
    blog_url="https://YOUR-BLOG-URL.com/blog"  # Change this
)
```

### Adjust Cache Similarity

More strict (fewer cache hits, more accurate):
```python
self.semantic_cache = SemanticCache(
    similarity_threshold=0.95,  # Was 0.92
    ...
)
```

More lenient (more cache hits, less strict):
```python
self.semantic_cache = SemanticCache(
    similarity_threshold=0.88,  # Was 0.92
    ...
)
```

### Change Update Schedule

Edit `models/scheduler.py`:

```python
# Daily updates (instead of weekly)
schedule.every().day.at("02:00").do(self.update_blog_content)

# Bi-weekly updates
schedule.every(14).days.do(self.update_blog_content)
```

## Monitoring

### View Cache Statistics

```python
from career_chatbot import CareerChatbot
from models import ChatbotConfig

chatbot = CareerChatbot(ChatbotConfig(name="Ryan Griego"))

stats = chatbot.semantic_cache.get_cache_stats()
print(stats)
```

Output:
```python
{
    'total_entries': 150,         # Total cached queries
    'total_accesses': 450,        # Total times cache was checked
    'reused_entries': 120,        # Queries that were reused
    'avg_reuse': 3.75,           # Average reuses per entry
    'cache_hit_rate': '80.0%'    # How often cache returns results
}
```

### Force Blog Update

```python
stats = chatbot.blog_manager.update_articles(force=True)
print(stats)
# {'new': 2, 'updated': 1, 'unchanged': 5}
```

### Clear Cache

```python
chatbot.semantic_cache.clear_cache()
```

## Cost Savings Example

### Without Caching (1,000 queries/day)

```
1,000 queries × 2,500 tokens avg × $0.0006 = $1.50/day
                                    Monthly: $45
```

### With Caching (1,000 queries/day, 70% hit rate)

```
Embeddings: 1,000 × 100 tokens × $0.00002 = $0.002/day
Cache Hits: 700 queries × $0 = $0
Cache Misses: 300 queries × $0.0015 = $0.45/day

Total: $0.45/day
Monthly: $13.50 (70% savings!)
```

### At Scale (10,000 queries/day, 80% hit rate)

```
Without cache: $450/month
With cache: $60/month
Savings: $390/month (87% reduction!)
```

## File Structure

```
data/
├── blog_articles.json       # Cached blog articles
│   └── {
│         "articles": [...],
│         "last_update": "2025-10-22T..."
│       }
│
└── semantic_cache.db        # SQLite cache database
    └── Tables:
        └── response_cache
            ├── query (text)
            ├── query_embedding (blob)
            ├── response (text)
            ├── context_hash (text)
            └── access statistics
```

## Troubleshooting

### Blog Scraper Fails

**Problem**: Can't fetch blog articles

**Check**:
1. Is the blog URL correct?
2. Is the website accessible?
3. Has the HTML structure changed?

**Test manually**:
```bash
python -m models.blog_scraper
```

### Cache Not Working

**Problem**: No cache hits

**Check**:
1. Is the similarity threshold too high?
2. Are queries too different?
3. Is context changing between queries?

**Debug**:
```python
# Test similarity between queries
from models.semantic_cache import SemanticCache

cache = SemanticCache()
e1 = cache._generate_embedding("query 1")
e2 = cache._generate_embedding("query 2")
similarity = cache._cosine_similarity(e1, e2)
print(f"Similarity: {similarity}")
```

### High API Costs

**Problem**: Costs not decreasing

**Check cache stats**:
```python
stats = chatbot.semantic_cache.get_cache_stats()
print(f"Hit rate: {stats['cache_hit_rate']}")
```

If hit rate is low (<50%):
- Lower similarity threshold
- Check if context is stable
- Verify queries are being cached

## Next Steps

1. ✅ **Test the system** - Run `python test_blog_cache.py`
2. 📊 **Monitor costs** - Check OpenAI dashboard after a week
3. 🎯 **Tune threshold** - Adjust based on cache hit rate
4. 📰 **Write more blog posts** - They'll automatically appear in chat!

## Documentation

- **Full Documentation**: [docs/blog-and-cache-system.md](docs/blog-and-cache-system.md)
- **Prompt Architecture**: [docs/prompt-refactoring-plan.md](docs/prompt-refactoring-plan.md)
- **Main README**: [README.md](README.md)

## Support

Having issues? Check:
1. OpenAI API key is valid
2. Dependencies are installed
3. `data/` directory exists
4. Blog URL is accessible

Run the test suite to diagnose:
```bash
python test_blog_cache.py
```

Happy chatting! 🚀
