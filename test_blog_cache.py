"""Test script for blog scraping and semantic caching"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.blog_scraper import BlogScraper
from models.blog_manager import BlogManager
from models.semantic_cache import SemanticCache

load_dotenv()


def test_blog_scraper():
    """Test blog scraping functionality"""
    print("\n" + "="*60)
    print("TEST 1: Blog Scraper")
    print("="*60)

    scraper = BlogScraper("https://ryangriego.com/blog")

    print("\n📡 Fetching blog articles...")
    articles = scraper.scrape_blog_index()

    print(f"\n✅ Found {len(articles)} articles:")
    for i, article in enumerate(articles[:5], 1):  # Show first 5
        print(f"\n{i}. {article.title}")
        print(f"   Date: {article.date}")
        print(f"   Tags: {', '.join(article.tags)}")
        print(f"   URL: {article.url}")
        print(f"   Summary: {article.summary[:100]}...")

    # Test full article scraping
    if articles:
        print(f"\n📄 Fetching full content for first article...")
        first_article = articles[0]
        content = scraper.scrape_full_article(first_article.url)
        if content:
            print(f"✅ Content length: {len(content)} characters")
            print(f"   Preview: {content[:200]}...")
        else:
            print("❌ Failed to fetch full content")


def test_blog_manager():
    """Test blog manager functionality"""
    print("\n" + "="*60)
    print("TEST 2: Blog Manager")
    print("="*60)

    manager = BlogManager(
        storage_path="data/test_blog_articles.json",
        blog_url="https://ryangriego.com/blog"
    )

    print("\n🔄 Updating blog articles (with full content)...")
    stats = manager.update_articles(force=True)

    print(f"\n📊 Update Statistics:")
    print(f"   New articles: {stats.get('new', 0)}")
    print(f"   Updated articles: {stats.get('updated', 0)}")
    print(f"   Unchanged articles: {stats.get('unchanged', 0)}")

    print(f"\n📚 Total articles in storage: {len(manager.get_all_articles())}")

    # Test context generation
    context = manager.get_articles_as_context(max_articles=3)
    print(f"\n📝 Context length (3 articles): {len(context)} characters")
    print(f"   Preview: {context[:300]}...")

    # Test search
    print("\n🔍 Searching for 'AI' articles...")
    matches = manager.search_articles("AI")
    print(f"   Found {len(matches)} matches:")
    for match in matches[:3]:
        print(f"   - {match.title}")


def test_semantic_cache():
    """Test semantic caching functionality"""
    print("\n" + "="*60)
    print("TEST 3: Semantic Cache")
    print("="*60)

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    cache = SemanticCache(
        db_path="data/test_semantic_cache.db",
        similarity_threshold=0.90,
        cache_ttl_days=30,
        openai_client=client
    )

    context_hash = "test_context_v1"

    # Test caching
    print("\n💾 Caching test response...")
    test_query = "What companies has Ryan worked for?"
    test_response = "Ryan has worked for several technology companies including startups and established firms."

    cache.cache_response(test_query, test_response, context_hash)
    print("✅ Response cached")

    # Test retrieval with similar queries
    test_queries = [
        ("What companies has Ryan worked for?", "Exact match"),
        ("Which companies did Ryan work at?", "Similar phrasing"),
        ("Where has Ryan been employed?", "Different wording"),
        ("What is Ryan's educational background?", "Different topic"),
    ]

    print("\n🔍 Testing cache retrieval with similar queries:")
    for query, description in test_queries:
        print(f"\n   Query: '{query}'")
        print(f"   Type: {description}")

        result = cache.get_cached_response(query, context_hash)
        if result:
            response, similarity = result
            print(f"   ✅ Cache HIT - Similarity: {similarity:.4f}")
            if similarity < 0.95:
                print(f"   📝 Response: {response[:80]}...")
        else:
            print(f"   ❌ Cache MISS")

    # Show cache statistics
    print("\n📊 Cache Statistics:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


def test_integration():
    """Test integrated system"""
    print("\n" + "="*60)
    print("TEST 4: Integration Test")
    print("="*60)

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Set up blog manager
    blog_manager = BlogManager(
        storage_path="data/test_blog_articles.json",
        blog_url="https://ryangriego.com/blog"
    )

    # Set up cache
    cache = SemanticCache(
        db_path="data/test_semantic_cache.db",
        similarity_threshold=0.92,
        openai_client=client
    )

    print("\n📚 Loading blog articles...")
    blog_manager.update_articles(force=False)  # Use cached if available

    articles = blog_manager.get_all_articles()
    print(f"✅ Loaded {len(articles)} articles")

    context = blog_manager.get_articles_as_context(max_articles=5)
    context_hash = blog_manager.get_context_hash()

    print(f"\n🔒 Context hash: {context_hash}")
    print(f"📏 Context size: {len(context)} characters")

    # Simulate queries
    print("\n💬 Simulating chat queries...")
    queries = [
        "What blog posts has Ryan written about AI?",
        "Tell me about Ryan's blog articles",
    ]

    for query in queries:
        print(f"\n   Query: '{query}'")

        # Check cache
        cached = cache.get_cached_response(query, context_hash)
        if cached:
            response, similarity = cached
            print(f"   ✅ Returned cached response (similarity: {similarity:.4f})")
        else:
            # Simulate response
            response = f"Based on the blog context: {len(articles)} articles available"
            cache.cache_response(query, response, context_hash)
            print(f"   💾 Generated and cached new response")

    print("\n✅ Integration test completed")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BLOG & CACHE SYSTEM TEST SUITE")
    print("="*60)

    try:
        test_blog_scraper()
    except Exception as e:
        print(f"\n❌ Blog scraper test failed: {e}")

    try:
        test_blog_manager()
    except Exception as e:
        print(f"\n❌ Blog manager test failed: {e}")

    try:
        test_semantic_cache()
    except Exception as e:
        print(f"\n❌ Semantic cache test failed: {e}")

    try:
        test_integration()
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")

    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
