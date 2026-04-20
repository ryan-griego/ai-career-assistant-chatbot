"""
Interactive demo to test blog integration and semantic caching
Run this to see the system working in real-time!
"""

import os
import sys
from dotenv import load_dotenv
import gradio as gr
from datetime import datetime

# Load environment
load_dotenv()

# Import the chatbot
from career_chatbot import CareerChatbot
from models import ChatbotConfig

# Global chatbot instance
chatbot = None
request_count = {"api_calls": 0, "cache_hits": 0, "total_queries": 0}


def initialize_chatbot():
    """Initialize the chatbot with blog and cache"""
    global chatbot

    print("\n" + "="*60)
    print("🚀 INITIALIZING AI CAREER ASSISTANT")
    print("="*60)

    config = ChatbotConfig(
        name="Ryan Griego",
        github_username=os.getenv("GITHUB_USERNAME", "ryan-griego")
    )

    chatbot = CareerChatbot(config)

    print("\n✅ Chatbot initialized!")
    print(f"📚 Blog articles loaded: {len(chatbot.blog_manager.get_all_articles())}")

    # Show blog articles
    articles = chatbot.blog_manager.get_all_articles()
    if articles:
        print("\n📰 Available blog articles:")
        for i, article in enumerate(articles[:5], 1):
            print(f"   {i}. {article.title} ({article.date})")
            print(f"      Content length: {len(article.content)} chars")
        if len(articles) > 5:
            print(f"   ... and {len(articles) - 5} more")

    # Show cache stats
    stats = chatbot.semantic_cache.get_cache_stats()
    print(f"\n💾 Cache statistics:")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate']}")

    return chatbot


def chat_with_monitoring(message, history):
    """Chat function with request monitoring"""
    global chatbot, request_count

    if chatbot is None:
        return "Please wait, initializing chatbot..."

    # Increment total queries
    request_count["total_queries"] += 1
    query_num = request_count["total_queries"]

    # Check if this will be a cache hit (before making the call)
    context_hash = chatbot.get_context_hash()
    cached_result = chatbot.semantic_cache.get_cached_response(message, context_hash)

    print("\n" + "="*60)
    print(f"📝 Query #{query_num}: {message[:50]}...")
    print("="*60)

    if cached_result:
        # Cache hit!
        request_count["cache_hits"] += 1
        response, similarity = cached_result

        print(f"✅ CACHE HIT! (Similarity: {similarity:.4f})")
        print(f"💰 Saved an API call! (~$0.001 saved)")
        print(f"📊 Cache hit rate: {request_count['cache_hits']}/{request_count['total_queries']} ({request_count['cache_hits']/request_count['total_queries']*100:.1f}%)")

        # Add monitoring footer to response
        footer = f"\n\n---\n🎯 **Cache Hit!** (Similarity: {similarity:.2%})\n💰 Saved ~$0.001 (no API call made)\n📊 Session: {request_count['cache_hits']} cache hits / {request_count['total_queries']} queries ({request_count['cache_hits']/request_count['total_queries']*100:.1f}% hit rate)"

        return response + footer
    else:
        # Cache miss - will make API call
        request_count["api_calls"] += 1

        print(f"❌ CACHE MISS - Making OpenAI API call...")
        print(f"💸 Cost: ~$0.001 for this query")

        # Make the actual call
        response = chatbot.chat(message, history)

        print(f"✅ Response generated and cached")
        print(f"📊 Cache hit rate: {request_count['cache_hits']}/{request_count['total_queries']} ({request_count['cache_hits']/request_count['total_queries']*100:.1f}%)")

        # Add monitoring footer to response
        footer = f"\n\n---\n🔄 **New Response** (cached for future)\n💸 Cost: ~$0.001 (OpenAI API call)\n📊 Session: {request_count['cache_hits']} cache hits / {request_count['total_queries']} queries ({request_count['cache_hits']/request_count['total_queries']*100:.1f}% hit rate)"

        return response + footer


def get_statistics():
    """Get current statistics"""
    global chatbot, request_count

    if chatbot is None:
        return "Chatbot not initialized"

    # Blog stats
    articles = chatbot.blog_manager.get_all_articles()
    total_content_length = sum(len(a.content) for a in articles)

    blog_stats = f"""
## 📰 Blog Statistics

- **Total Articles**: {len(articles)}
- **Total Content**: {total_content_length:,} characters
- **Last Update**: {chatbot.blog_manager.last_update.strftime('%Y-%m-%d %H:%M:%S') if chatbot.blog_manager.last_update else 'Never'}
- **Context Hash**: `{chatbot.get_context_hash()[:16]}...`

### Articles:
"""

    for i, article in enumerate(articles, 1):
        blog_stats += f"\n{i}. **{article.title}**\n"
        blog_stats += f"   - Date: {article.date}\n"
        blog_stats += f"   - Tags: {', '.join(article.tags)}\n"
        blog_stats += f"   - Content: {len(article.content):,} characters\n"

    # Cache stats
    cache_stats_data = chatbot.semantic_cache.get_cache_stats()

    cache_stats = f"""
## 💾 Cache Statistics

- **Total Cached Entries**: {cache_stats_data['total_entries']}
- **Total Accesses**: {cache_stats_data['total_accesses']}
- **Reused Entries**: {cache_stats_data['reused_entries']}
- **Average Reuse**: {cache_stats_data['avg_reuse']}
- **Cache Hit Rate**: {cache_stats_data['cache_hit_rate']}

## 📊 Current Session

- **Total Queries**: {request_count['total_queries']}
- **Cache Hits**: {request_count['cache_hits']} ✅
- **API Calls**: {request_count['api_calls']} 💸
- **Hit Rate**: {(request_count['cache_hits']/request_count['total_queries']*100) if request_count['total_queries'] > 0 else 0:.1f}%

### Cost Savings This Session

- **Without Cache**: ${request_count['total_queries'] * 0.001:.3f}
- **With Cache**: ${request_count['api_calls'] * 0.001:.3f}
- **Saved**: ${request_count['cache_hits'] * 0.001:.3f} ({(request_count['cache_hits']/request_count['total_queries']*100) if request_count['total_queries'] > 0 else 0:.1f}% reduction)
"""

    return blog_stats + "\n" + cache_stats


def get_sample_queries():
    """Get sample queries to test"""
    return """
## 🧪 Test Queries

### Blog-Related Queries:
1. "What blog posts have you written?"
2. "Tell me about your AI projects"
3. "What technologies have you worked with?"
4. "Describe your blog about RAG applications"
5. "What have you written about fine-tuning models?"

### Similar Queries (Test Cache Matching):
Ask these in sequence to see cache hits:

**First:** "What companies has Ryan worked for?"
**Then:** "Which companies did Ryan work at?" ← Should be cache hit!
**Then:** "Where has Ryan been employed?" ← Should be cache hit!

**First:** "What is Ryan's educational background?"
**Then:** "Where did Ryan go to school?" ← Should be cache hit!

### Professional Queries:
1. "What is Ryan's work experience?"
2. "What programming languages does Ryan know?"
3. "Tell me about Ryan's GitHub projects"

## 💡 Tips:
- Ask the same question twice → 2nd time should be instant cache hit
- Rephrase questions → See if cache finds similarity (92%+ threshold)
- Mix blog + resume questions → See integrated knowledge
- Watch the console for cache hit/miss messages
"""


def clear_session_stats():
    """Reset session statistics"""
    global request_count
    request_count = {"api_calls": 0, "cache_hits": 0, "total_queries": 0}
    return "✅ Session statistics cleared!"


# Initialize chatbot on startup
print("Initializing chatbot...")
initialize_chatbot()

# Create Gradio interface
with gr.Blocks(title="Blog & Cache Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🤖 AI Career Assistant - Blog & Cache Demo

    Test the new blog integration and semantic caching features!

    **Features being tested:**
    - 📰 Blog article integration (full content in context)
    - 💾 Semantic caching (similar queries matched)
    - 💰 Cost tracking (API calls vs cache hits)
    """)

    with gr.Tabs():
        with gr.Tab("💬 Chat"):
            gr.Markdown("### Ask questions about Ryan's blog, work experience, or skills")

            chatbot_ui = gr.ChatInterface(
                fn=chat_with_monitoring,
                type="messages",
                examples=[
                    "What blog posts have you written?",
                    "Tell me about your AI projects",
                    "What companies has Ryan worked for?",
                    "Describe your blog about building AI tools",
                    "What technologies have you used in your projects?",
                ],
                cache_examples=False,
            )

        with gr.Tab("📊 Statistics"):
            gr.Markdown("### View blog articles and cache performance")

            stats_output = gr.Markdown()

            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh Stats", variant="primary")
                clear_btn = gr.Button("🗑️ Clear Session Stats", variant="secondary")

            clear_output = gr.Textbox(label="Status", visible=False)

            refresh_btn.click(fn=get_statistics, outputs=stats_output)
            clear_btn.click(fn=clear_session_stats, outputs=clear_output)

            # Auto-refresh on load
            demo.load(fn=get_statistics, outputs=stats_output)

        with gr.Tab("🧪 Test Guide"):
            gr.Markdown(get_sample_queries())

    gr.Markdown("""
    ---
    ### 📝 How to Use This Demo:

    1. **Test Blog Integration**: Ask about blog posts (e.g., "What blog posts have you written?")
    2. **Test Cache**: Ask similar questions twice and watch for cache hits
    3. **Monitor Costs**: Check Statistics tab to see savings
    4. **Watch Console**: Real-time cache hit/miss notifications in terminal

    ### 🎯 What to Look For:

    - ✅ **Cache Hit**: Response is instant, costs ~$0.00002 (embedding only)
    - 🔄 **Cache Miss**: Takes 2-3 seconds, costs ~$0.001 (full API call)
    - 📊 **Hit Rate**: Should improve as you ask similar questions

    ### 💡 Pro Tip:

    Open your terminal to see detailed logging:
    - `✅ CACHE HIT!` = Saved money!
    - `❌ CACHE MISS` = Making API call
    - Similarity scores shown for cache hits
    """)

# Launch the demo
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌐 LAUNCHING GRADIO DEMO")
    print("="*60)
    print("\nDemo will open in your browser...")
    print("Watch this console for cache hit/miss notifications!")
    print("\n" + "="*60 + "\n")

    demo.launch(server_name="127.0.0.1", server_port=7860)
