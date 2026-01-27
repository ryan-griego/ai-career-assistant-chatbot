"""Blog content manager with weekly updates"""

import json
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from .blog_scraper import BlogScraper, BlogArticle


class BlogManager:
    """Manages blog content with periodic updates"""

    def __init__(self,
                 storage_path: str = "data/blog_articles.json",
                 blog_url: str = "https://ryangriego.com/blog"):
        """
        Initialize blog manager

        Args:
            storage_path: Path to store blog articles JSON
            blog_url: URL of the blog to scrape
        """
        self.storage_path = Path(storage_path)
        self.blog_url = blog_url
        self.scraper = BlogScraper(blog_url)
        self.articles: List[BlogArticle] = []
        self.last_update: Optional[datetime] = None

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing articles
        self._load_articles()

    def _load_articles(self):
        """Load articles from storage"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                    self.articles = [
                        BlogArticle(**article_data)
                        for article_data in data.get('articles', [])
                    ]

                    last_update_str = data.get('last_update')
                    if last_update_str:
                        self.last_update = datetime.fromisoformat(last_update_str)

                    print(f"📚 Loaded {len(self.articles)} blog articles from storage")

            except Exception as e:
                print(f"Error loading articles: {e}")
                self.articles = []

    def _save_articles(self):
        """Save articles to storage"""
        try:
            data = {
                'articles': [article.to_dict() for article in self.articles],
                'last_update': datetime.now().isoformat()
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

            self.last_update = datetime.now()
            print(f"💾 Saved {len(self.articles)} articles to storage")

        except Exception as e:
            print(f"Error saving articles: {e}")

    def should_update(self) -> bool:
        """Check if it's time to update (weekly)"""
        if not self.last_update:
            return True

        days_since_update = (datetime.now() - self.last_update).days
        return days_since_update >= 7

    def update_articles(self, force: bool = False) -> Dict[str, int]:
        """
        Scrape blog for new/updated articles

        Args:
            force: Force update even if not due

        Returns:
            Dictionary with update statistics
        """
        if not force and not self.should_update():
            days_remaining = 7 - (datetime.now() - self.last_update).days
            print(f"⏳ Next update in {days_remaining} days")
            return {'status': 'skipped', 'new': 0, 'updated': 0, 'unchanged': len(self.articles)}

        print("🔄 Updating blog articles...")

        # Scrape current articles
        new_articles = self.scraper.scrape_all_articles_with_content()

        stats = {'new': 0, 'updated': 0, 'unchanged': 0}

        # Build lookup of existing articles by URL
        existing_by_url = {article.url: article for article in self.articles}

        updated_articles = []

        for article in new_articles:
            if article.url in existing_by_url:
                existing = existing_by_url[article.url]

                # Check if content changed
                if article.content_hash != existing.content_hash:
                    updated_articles.append(article)
                    stats['updated'] += 1
                    print(f"  ✏️  Updated: {article.title}")
                else:
                    updated_articles.append(existing)
                    stats['unchanged'] += 1
            else:
                # New article
                updated_articles.append(article)
                stats['new'] += 1
                print(f"  ✨ New: {article.title}")

        self.articles = updated_articles
        self._save_articles()

        print(f"✅ Update complete: {stats['new']} new, {stats['updated']} updated, {stats['unchanged']} unchanged")

        return stats

    def get_all_articles(self) -> List[BlogArticle]:
        """Get all articles"""
        return self.articles

    def get_articles_as_context(self, max_articles: Optional[int] = None) -> str:
        """
        Format articles for inclusion in chat context

        Args:
            max_articles: Maximum number of articles to include (most recent first)

        Returns:
            Formatted string with all articles
        """
        articles_to_include = self.articles

        if max_articles:
            # Sort by date (most recent first) and limit
            articles_to_include = sorted(
                self.articles,
                key=lambda a: a.date,
                reverse=True
            )[:max_articles]

        if not articles_to_include:
            return "\n## Blog Articles\n\nNo blog articles available.\n"

        context = "\n## Blog Articles from ryangriego.com/blog\n"
        context += f"*{len(articles_to_include)} articles total*\n\n"

        for article in articles_to_include:
            context += article.to_context_string()
            context += "\n---\n"

        return context

    def get_context_hash(self) -> str:
        """
        Generate hash of current blog content for cache invalidation

        When blog content changes, this hash changes, invalidating old cached responses
        """
        content_str = "".join([article.content_hash for article in self.articles])
        return hashlib.md5(content_str.encode()).hexdigest()

    def search_articles(self, query: str) -> List[BlogArticle]:
        """
        Search articles by keyword

        Args:
            query: Search query

        Returns:
            List of matching articles
        """
        query_lower = query.lower()
        matches = []

        for article in self.articles:
            if (query_lower in article.title.lower() or
                query_lower in article.summary.lower() or
                query_lower in article.content.lower() or
                any(query_lower in tag.lower() for tag in article.tags)):
                matches.append(article)

        return matches


def test_blog_manager():
    """Test blog manager functionality"""
    manager = BlogManager(
        storage_path="data/test_blog_articles.json",
        blog_url="https://ryangriego.com/blog"
    )

    # Force update
    stats = manager.update_articles(force=True)
    print(f"\n📊 Update Stats: {stats}")

    # Get context
    context = manager.get_articles_as_context(max_articles=3)
    print(f"\n📄 Context (first 500 chars):\n{context[:500]}...")

    # Test search
    matches = manager.search_articles("AI")
    print(f"\n🔍 Found {len(matches)} articles about 'AI'")
    for article in matches[:3]:
        print(f"  - {article.title}")


if __name__ == "__main__":
    test_blog_manager()
