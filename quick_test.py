"""Quick command-line test of blog and cache features"""

import os
from dotenv import load_dotenv
from career_chatbot import CareerChatbot
from models import ChatbotConfig

load_dotenv()

def test_blog_and_cache():
    """Interactive test of blog integration and caching"""

    print("\n" + "="*70)
    print("🧪 QUICK TEST: Blog Integration & Semantic Caching")
    print("="*70)

    # Initialize chatbot
    print("\n1️⃣  Initializing chatbot...")
    config = ChatbotConfig(
        name="Ryan Griego",
        github_username=os.getenv("GITHUB_USERNAME", "ryan-griego")
    )
    chatbot = CareerChatbot(config)

    # Check blog articles
    print("\n2️⃣  Checking blog articles...")
    articles = chatbot.blog_manager.get_all_articles()
    print(f"   ✅ Found {len(articles)} blog articles")

    if articles:
        print("\n   📰 Articles loaded:")
        for i, article in enumerate(articles[:3], 1):
            print(f"      {i}. {article.title}")
            print(f"         Date: {article.date}")
            print(f"         Content: {len(article.content):,} characters")

    # Test cache
    print("\n3️⃣  Testing semantic cache...")
    cache_stats = chatbot.semantic_cache.get_cache_stats()
    print(f"   💾 Cache entries: {cache_stats['total_entries']}")
    print(f"   📊 Hit rate: {cache_stats['cache_hit_rate']}")

    # Interactive queries
    print("\n4️⃣  Interactive Testing")
    print("="*70)
    print("\n🎯 Let's test with real queries!\n")

    test_queries = [
        ("What blog posts have you written?", "Test blog integration"),
        ("What blog posts have you written?", "Test cache (same query)"),
        ("Tell me about your blog articles", "Test cache (similar query)"),
    ]

    for i, (query, description) in enumerate(test_queries, 1):
        print(f"\n{'─'*70}")
        print(f"Query {i}: {description}")
        print(f"{'─'*70}")
        print(f"❓ Question: \"{query}\"\n")

        # Check if it will be cached
        context_hash = chatbot.get_context_hash()
        cached = chatbot.semantic_cache.get_cached_response(query, context_hash)

        if cached:
            response, similarity = cached
            print(f"✅ CACHE HIT! (Similarity: {similarity:.4f})")
            print(f"💰 Saved ~$0.001 (no OpenAI call)")
            print(f"\n📝 Response: {response[:200]}...")
        else:
            print(f"🔄 CACHE MISS - Making OpenAI API call...")
            print(f"💸 Cost: ~$0.001")

            response = chatbot.chat(query, [])
            print(f"\n📝 Response: {response[:200]}...")
            print(f"\n✅ Cached for future queries")

        input("\nPress Enter to continue...")

    # Manual testing
    print(f"\n{'='*70}")
    print("💬 Now try your own queries!")
    print("="*70)
    print("\nType your questions (or 'stats' for statistics, 'quit' to exit):\n")

    query_count = {"total": 0, "cache_hits": 0, "api_calls": 0}

    while True:
        try:
            user_input = input("\n❓ You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == 'stats':
                print(f"\n📊 Session Statistics:")
                print(f"   Total queries: {query_count['total']}")
                print(f"   Cache hits: {query_count['cache_hits']} ✅")
                print(f"   API calls: {query_count['api_calls']} 💸")
                if query_count['total'] > 0:
                    hit_rate = query_count['cache_hits'] / query_count['total'] * 100
                    print(f"   Hit rate: {hit_rate:.1f}%")
                    saved = query_count['cache_hits'] * 0.001
                    cost = query_count['api_calls'] * 0.001
                    print(f"   Cost: ${cost:.4f}")
                    print(f"   Saved: ${saved:.4f}")
                continue

            query_count['total'] += 1

            # Check cache
            context_hash = chatbot.get_context_hash()
            cached = chatbot.semantic_cache.get_cached_response(user_input, context_hash)

            if cached:
                query_count['cache_hits'] += 1
                response, similarity = cached
                print(f"\n✅ [CACHE HIT - Similarity: {similarity:.4f}]")
                print(f"💰 Saved ~$0.001\n")
                print(f"🤖 AI: {response}")
            else:
                query_count['api_calls'] += 1
                print(f"\n🔄 [CACHE MISS - Making API call...]")
                print(f"💸 Cost: ~$0.001\n")

                response = chatbot.chat(user_input, [])
                print(f"🤖 AI: {response}")
                print(f"\n✅ Response cached for future queries")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

    # Final stats
    if query_count['total'] > 0:
        print(f"\n{'='*70}")
        print("📊 FINAL SESSION STATISTICS")
        print("="*70)
        print(f"Total queries: {query_count['total']}")
        print(f"Cache hits: {query_count['cache_hits']} ✅")
        print(f"API calls: {query_count['api_calls']} 💸")
        hit_rate = query_count['cache_hits'] / query_count['total'] * 100
        print(f"Hit rate: {hit_rate:.1f}%")
        print(f"\n💰 Cost Analysis:")
        print(f"   Without cache: ${query_count['total'] * 0.001:.4f}")
        print(f"   With cache: ${query_count['api_calls'] * 0.001:.4f}")
        print(f"   Saved: ${query_count['cache_hits'] * 0.001:.4f} ({hit_rate:.1f}% reduction)")
        print("="*70 + "\n")


if __name__ == "__main__":
    test_blog_and_cache()
