"""Blog scraper for ryangriego.com/blog"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
import json


class BlogArticle:
    """Represents a blog article"""

    def __init__(self, title: str, date: str, tags: List[str], summary: str, url: str, content: str = "", content_hash: str = None):
        self.title = title
        self.date = date
        self.tags = tags
        self.summary = summary
        self.url = url
        self.content = content
        # Use provided hash or generate new one
        self.content_hash = content_hash if content_hash else self._generate_hash()

    def _generate_hash(self) -> str:
        """Generate a hash of the article content for change detection"""
        content_str = f"{self.title}{self.date}{self.summary}{self.content}"
        return hashlib.md5(content_str.encode()).hexdigest()

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'title': self.title,
            'date': self.date,
            'tags': self.tags,
            'summary': self.summary,
            'url': self.url,
            'content': self.content,
            'content_hash': self.content_hash
        }

    def to_context_string(self) -> str:
        """Format article for inclusion in chat context"""
        return f"""
## Blog Article: {self.title}
**Published:** {self.date}
**Tags:** {', '.join(self.tags)}
**Summary:** {self.summary}
**URL:** {self.url}

{self.content if self.content else self.summary}
"""


class BlogScraper:
    """Scrapes blog articles from ryangriego.com/blog"""

    def __init__(self, blog_url: str = "https://ryangriego.com/blog"):
        self.blog_url = blog_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def scrape_blog_index(self) -> List[BlogArticle]:
        """Scrape the main blog page for article summaries"""
        all_articles = []

        # Scrape all pages (pagination)
        page_num = 1
        max_pages = 10  # Safety limit

        while page_num <= max_pages:
            try:
                # Construct URL for current page
                if page_num == 1:
                    url = self.blog_url
                else:
                    # Handle pagination URLs like /blog/posts/page/2/
                    url = f"{self.blog_url}/posts/page/{page_num}/"

                print(f"  📄 Scraping page {page_num}: {url}")
                response = self.session.get(url, timeout=10)

                # If we get 404, we've reached the end
                if response.status_code == 404:
                    print(f"  ✅ Reached last page (page {page_num-1})")
                    break

                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all blog post preview sections
                # Based on the structure: published date, title, tags, summary, "Read more" link
                post_sections = soup.find_all('li')  # Each post appears to be in a list item

                articles_on_page = 0

                for post in post_sections:
                    try:
                        # Extract publication date
                        date_text = post.find(text=lambda t: t and 'Published on' in t)
                        if not date_text:
                            continue

                        # Get the next sibling which should contain the date
                        date_elem = post.find('br')
                        if date_elem and date_elem.next_sibling:
                            date = date_elem.next_sibling.strip()
                        else:
                            date = "Unknown"

                        # Extract title (h2 heading)
                        title_elem = post.find('h2')
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)

                        # Extract tags (they appear to be plain text after the title)
                        tags_text = post.get_text()
                        # Extract tags between title and summary
                        tags = []
                        tag_indicators = ['AI', 'Python', 'Next.js', 'OpenAI', 'Gradio', 'LLM',
                                         'Function-Calling', 'Pushover', 'Vector-Database',
                                         'Modal', 'HuggingFace', 'Chroma', 'LangChain', 'RAG',
                                         'docker', 'cloud', 'next-js', 'tailwind', 'typescript',
                                         'MongoDB', 'Tailwind-CSS', 'Authentication', 'reflection',
                                         'writing', 'feature', 'raspberry-pi', 'LLMs']
                        for tag in tag_indicators:
                            if tag in tags_text:
                                tags.append(tag)

                        # Extract summary (paragraph after tags)
                        summary_elem = post.find('p') or post.find(text=True)
                        summary = ""
                        if summary_elem:
                            # Get the text after the tags
                            summary = str(summary_elem).strip() if isinstance(summary_elem, str) else summary_elem.get_text(strip=True)

                        # Extract URL from "Read more" link or from title link
                        link_elem = post.find('a', href=True)
                        article_url = ""
                        if link_elem and link_elem.get('href'):
                            article_url = link_elem['href']
                            if not article_url.startswith('http'):
                                article_url = f"https://ryangriego.com{article_url}"

                        # Skip if we already have this article (duplicate check by URL)
                        if any(a.url == article_url for a in all_articles):
                            continue

                        article = BlogArticle(
                            title=title,
                            date=date,
                            tags=tags,
                            summary=summary,
                            url=article_url
                        )
                        all_articles.append(article)
                        articles_on_page += 1

                    except Exception as e:
                        print(f"  ⚠️ Error parsing article: {e}")
                        continue

                if articles_on_page == 0:
                    # No articles found on this page, we're done
                    print(f"  ✅ No more articles found")
                    break

                print(f"  ✅ Found {articles_on_page} articles on page {page_num}")
                page_num += 1

            except requests.RequestException as e:
                print(f"  ❌ Error fetching page {page_num}: {e}")
                break

        print(f"\n📚 Total articles scraped: {len(all_articles)}")
        return all_articles

    def scrape_full_article(self, article_url: str) -> Optional[str]:
        """Scrape the full content of a specific article"""
        try:
            response = self.session.get(article_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the main article content
            # This will depend on the structure of your blog post pages
            article_content = soup.find('article') or soup.find('main')

            if article_content:
                # Extract text, preserving some structure
                paragraphs = article_content.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol', 'pre', 'code'])
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
                return content

            return None

        except requests.RequestException as e:
            print(f"Error fetching article {article_url}: {e}")
            return None

    def scrape_all_articles_with_content(self) -> List[BlogArticle]:
        """Scrape all articles including full content"""
        articles = self.scrape_blog_index()

        for article in articles:
            if article.url:
                print(f"Fetching full content for: {article.title}")
                full_content = self.scrape_full_article(article.url)
                if full_content:
                    article.content = full_content
                    # Update hash with new content
                    article.content_hash = article._generate_hash()

        return articles


def test_scraper():
    """Test the blog scraper"""
    scraper = BlogScraper()
    articles = scraper.scrape_blog_index()

    print(f"Found {len(articles)} articles:")
    for article in articles:
        print(f"\n- {article.title}")
        print(f"  Date: {article.date}")
        print(f"  Tags: {', '.join(article.tags)}")
        print(f"  URL: {article.url}")
        print(f"  Summary: {article.summary[:100]}...")


if __name__ == "__main__":
    test_scraper()
