"""Background scheduler for periodic blog updates"""

import schedule
import time
import logging
from datetime import datetime
from typing import Optional
from .blog_manager import BlogManager
from .semantic_cache import SemanticCache

logger = logging.getLogger(__name__)


class BlogUpdateScheduler:
    """Scheduler for periodic blog content updates"""

    def __init__(self,
                 blog_manager: BlogManager,
                 semantic_cache: Optional[SemanticCache] = None):
        """
        Initialize scheduler

        Args:
            blog_manager: BlogManager instance to update
            semantic_cache: Optional SemanticCache to clean old entries
        """
        self.blog_manager = blog_manager
        self.semantic_cache = semantic_cache
        self.is_running = False

    def update_blog_content(self):
        """Scheduled task to update blog content"""
        try:
            logger.info("⏰ Scheduled blog update started")
            stats = self.blog_manager.update_articles(force=False)
            logger.info(f"✅ Scheduled blog update completed: {stats}")

            # If new articles were added or updated, log it
            if stats.get('new', 0) > 0 or stats.get('updated', 0) > 0:
                logger.info(f"📰 Blog content changed: {stats['new']} new, {stats['updated']} updated")

        except Exception as e:
            logger.error(f"❌ Scheduled blog update failed: {e}")

    def clean_cache(self):
        """Scheduled task to clean old cache entries"""
        if self.semantic_cache:
            try:
                logger.info("🧹 Scheduled cache cleanup started")
                self.semantic_cache.clean_old_entries()
                logger.info("✅ Cache cleanup completed")
            except Exception as e:
                logger.error(f"❌ Cache cleanup failed: {e}")

    def schedule_tasks(self):
        """Set up scheduled tasks"""
        # Update blog every Sunday at 2 AM
        schedule.every().sunday.at("02:00").do(self.update_blog_content)

        # Clean cache every day at 3 AM
        if self.semantic_cache:
            schedule.every().day.at("03:00").do(self.clean_cache)

        logger.info("📅 Scheduled tasks configured:")
        logger.info("  - Blog updates: Every Sunday at 2:00 AM")
        if self.semantic_cache:
            logger.info("  - Cache cleanup: Daily at 3:00 AM")

    def run(self):
        """Run the scheduler (blocking)"""
        self.schedule_tasks()
        self.is_running = True

        logger.info("🚀 Scheduler started")

        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("⏹️  Scheduler stopped by user")
            self.is_running = False

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("⏹️  Scheduler stopping...")


def test_scheduler():
    """Test scheduler with immediate execution"""
    from .blog_manager import BlogManager
    from .semantic_cache import SemanticCache
    from openai import OpenAI
    import os
    from dotenv import load_dotenv

    load_dotenv()

    blog_manager = BlogManager(
        storage_path="data/test_blog_articles.json",
        blog_url="https://ryangriego.com/blog"
    )

    cache = SemanticCache(
        db_path="data/test_cache.db",
        openai_client=OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    )

    scheduler = BlogUpdateScheduler(blog_manager, cache)

    # Run tasks immediately for testing
    print("\n🧪 Testing blog update task...")
    scheduler.update_blog_content()

    print("\n🧪 Testing cache cleanup task...")
    scheduler.clean_cache()

    print("\n✅ Test completed")


if __name__ == "__main__":
    test_scheduler()
