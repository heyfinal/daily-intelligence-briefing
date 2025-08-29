"""
Data collection module for AI intelligence briefing
"""
import asyncio
import aiohttp
import json
import feedparser
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin
import time

from config import (
    DATA_SOURCES, CONTENT_CATEGORIES, GITHUB_TOKEN, 
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, RATE_LIMITS
)
from database import DatabaseManager


class DataCollector:
    """Collects data from multiple sources asynchronously"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'AI-Intelligence-Briefing/1.0 (https://github.com/heyfinal)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def collect_all_data(self) -> Dict[str, List[Dict]]:
        """Main entry point to collect all data"""
        print(f"Starting data collection at {datetime.now()}")
        
        tasks = [
            self.collect_github_releases(),
            self.collect_npm_updates(),
            self.collect_pypi_updates(),
            self.collect_rss_feeds(),
            self.collect_reddit_posts(),
            self.collect_hackernews_posts()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_updates = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Error in data collection: {result}")
                continue
            all_updates.extend(result)
        
        # Process and categorize updates
        categorized_updates = self.categorize_updates(all_updates)
        
        # Calculate importance scores
        self.db.calculate_importance_scores()
        
        print(f"Collected {len(all_updates)} updates")
        return categorized_updates
    
    async def collect_github_releases(self) -> List[Dict]:
        """Collect GitHub releases and commits"""
        updates = []
        
        for repo_info in DATA_SOURCES['github_repos']:
            if not self.db.check_rate_limit('github', 
                                          RATE_LIMITS['github']['calls'],
                                          RATE_LIMITS['github']['period']):
                print(f"GitHub rate limit reached, skipping {repo_info['repo']}")
                continue
            
            owner, repo = repo_info['owner'], repo_info['repo']
            cache_key = f"github_{owner}_{repo}_releases"
            
            # Check cache first
            cached_data = self.db.get_cache(cache_key)
            if cached_data:
                updates.extend(cached_data)
                continue
            
            try:
                # Get releases
                releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                headers = {}
                if GITHUB_TOKEN:
                    headers['Authorization'] = f'token {GITHUB_TOKEN}'
                
                async with self.session.get(releases_url, headers=headers) as response:
                    if response.status == 200:
                        releases = await response.json()
                        
                        repo_updates = []
                        for release in releases[:5]:  # Last 5 releases
                            update_data = {
                                'source': 'github',
                                'source_id': f"{owner}/{repo}/releases/{release['id']}",
                                'title': f"{repo}: {release['name'] or release['tag_name']}",
                                'content': release.get('body', ''),
                                'url': release['html_url'],
                                'published_date': datetime.fromisoformat(
                                    release['published_at'].replace('Z', '+00:00')
                                ),
                                'metadata': {
                                    'repo': f"{owner}/{repo}",
                                    'tag': release['tag_name'],
                                    'prerelease': release['prerelease']
                                }
                            }
                            repo_updates.append(update_data)
                            
                            # Add to database
                            self.db.add_update(**update_data)
                        
                        # Cache the results
                        self.db.set_cache(cache_key, repo_updates, 6)
                        updates.extend(repo_updates)
                
                # Also get recent commits
                commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
                async with self.session.get(commits_url, 
                                          headers=headers,
                                          params={'per_page': 10, 'since': 
                                                 (datetime.now() - timedelta(days=7)).isoformat()}) as response:
                    if response.status == 200:
                        commits = await response.json()
                        
                        for commit in commits[:3]:  # Last 3 commits
                            if len(commit['commit']['message']) > 20:  # Skip trivial commits
                                update_data = {
                                    'source': 'github',
                                    'source_id': f"{owner}/{repo}/commit/{commit['sha']}",
                                    'title': f"{repo}: {commit['commit']['message'][:100]}",
                                    'content': commit['commit']['message'],
                                    'url': commit['html_url'],
                                    'published_date': datetime.fromisoformat(
                                        commit['commit']['author']['date'].replace('Z', '+00:00')
                                    ),
                                    'metadata': {
                                        'repo': f"{owner}/{repo}",
                                        'sha': commit['sha'][:8],
                                        'type': 'commit'
                                    }
                                }
                                updates.append(update_data)
                                self.db.add_update(**update_data)
                
            except Exception as e:
                print(f"Error collecting GitHub data for {owner}/{repo}: {e}")
                await asyncio.sleep(1)
        
        return updates
    
    async def collect_npm_updates(self) -> List[Dict]:
        """Collect npm package updates"""
        updates = []
        
        for package in DATA_SOURCES['npm_packages']:
            if not self.db.check_rate_limit('npm', 
                                          RATE_LIMITS['npm']['calls'],
                                          RATE_LIMITS['npm']['period']):
                continue
            
            cache_key = f"npm_{package}"
            cached_data = self.db.get_cache(cache_key)
            if cached_data:
                updates.extend(cached_data)
                continue
            
            try:
                url = f"https://registry.npmjs.org/{package}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Get latest version info
                        latest_version = data['dist-tags']['latest']
                        version_info = data['versions'][latest_version]
                        
                        # Check if this version is recent (last 30 days)
                        time_str = data['time'][latest_version]
                        published_date = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        
                        if (datetime.now().replace(tzinfo=published_date.tzinfo) - published_date).days <= 30:
                            update_data = {
                                'source': 'npm',
                                'source_id': f"{package}@{latest_version}",
                                'title': f"NPM: {package} v{latest_version}",
                                'content': version_info.get('description', ''),
                                'url': f"https://www.npmjs.com/package/{package}",
                                'published_date': published_date,
                                'metadata': {
                                    'package': package,
                                    'version': latest_version,
                                    'type': 'npm_release'
                                }
                            }
                            updates.append(update_data)
                            self.db.add_update(**update_data)
                            self.db.set_cache(cache_key, [update_data], 12)
                
            except Exception as e:
                print(f"Error collecting npm data for {package}: {e}")
                await asyncio.sleep(0.5)
        
        return updates
    
    async def collect_pypi_updates(self) -> List[Dict]:
        """Collect PyPI package updates"""
        updates = []
        
        for package in DATA_SOURCES['pypi_packages']:
            if not self.db.check_rate_limit('pypi', 
                                          RATE_LIMITS['pypi']['calls'],
                                          RATE_LIMITS['pypi']['period']):
                continue
            
            cache_key = f"pypi_{package}"
            cached_data = self.db.get_cache(cache_key)
            if cached_data:
                updates.extend(cached_data)
                continue
            
            try:
                url = f"https://pypi.org/pypi/{package}/json"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Get latest release info
                        releases = data['releases']
                        latest_version = data['info']['version']
                        
                        # Get recent releases (last 30 days)
                        recent_releases = []
                        for version, release_info in releases.items():
                            if release_info:
                                upload_time = release_info[0]['upload_time']
                                published_date = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                                
                                if (datetime.now().replace(tzinfo=published_date.tzinfo) - published_date).days <= 30:
                                    recent_releases.append((version, published_date, release_info))
                        
                        # Process recent releases
                        for version, published_date, release_info in recent_releases[-5:]:  # Last 5
                            update_data = {
                                'source': 'pypi',
                                'source_id': f"{package}=={version}",
                                'title': f"PyPI: {package} v{version}",
                                'content': data['info'].get('summary', ''),
                                'url': f"https://pypi.org/project/{package}/{version}/",
                                'published_date': published_date,
                                'metadata': {
                                    'package': package,
                                    'version': version,
                                    'type': 'pypi_release'
                                }
                            }
                            updates.append(update_data)
                            self.db.add_update(**update_data)
                        
                        if recent_releases:
                            self.db.set_cache(cache_key, updates[-len(recent_releases):], 12)
                
            except Exception as e:
                print(f"Error collecting PyPI data for {package}: {e}")
                await asyncio.sleep(0.5)
        
        return updates
    
    async def collect_rss_feeds(self) -> List[Dict]:
        """Collect RSS feed updates"""
        updates = []
        
        for feed_url in DATA_SOURCES['rss_feeds']:
            cache_key = f"rss_{hash(feed_url)}"
            cached_data = self.db.get_cache(cache_key)
            if cached_data:
                updates.extend(cached_data)
                continue
            
            try:
                async with self.session.get(feed_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse RSS feed
                        feed = feedparser.parse(content)
                        
                        feed_updates = []
                        for entry in feed.entries[:10]:  # Last 10 entries
                            # Parse date
                            published_date = None
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                published_date = datetime(*entry.published_parsed[:6])
                            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                                published_date = datetime(*entry.updated_parsed[:6])
                            
                            if not published_date:
                                published_date = datetime.now() - timedelta(days=1)
                            
                            # Skip old entries (older than 7 days)
                            if (datetime.now() - published_date).days > 7:
                                continue
                            
                            update_data = {
                                'source': 'rss',
                                'source_id': entry.get('id', entry.get('link', '')),
                                'title': entry.get('title', ''),
                                'content': entry.get('summary', entry.get('description', '')),
                                'url': entry.get('link', ''),
                                'published_date': published_date,
                                'metadata': {
                                    'feed_url': feed_url,
                                    'feed_title': feed.feed.get('title', ''),
                                    'type': 'rss_entry'
                                }
                            }
                            feed_updates.append(update_data)
                            self.db.add_update(**update_data)
                        
                        self.db.set_cache(cache_key, feed_updates, 4)
                        updates.extend(feed_updates)
                
            except Exception as e:
                print(f"Error collecting RSS feed {feed_url}: {e}")
                await asyncio.sleep(1)
        
        return updates
    
    async def collect_reddit_posts(self) -> List[Dict]:
        """Collect relevant Reddit posts"""
        updates = []
        
        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            print("Reddit credentials not configured, skipping Reddit collection")
            return updates
        
        # TODO: Implement Reddit API collection
        # This would require OAuth2 setup and proper rate limiting
        # For now, we'll skip this to avoid API complexity
        
        return updates
    
    async def collect_hackernews_posts(self) -> List[Dict]:
        """Collect HackerNews posts with relevant keywords"""
        updates = []
        
        cache_key = "hackernews_posts"
        cached_data = self.db.get_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get top stories
            async with self.session.get("https://hacker-news.firebaseio.com/v0/topstories.json") as response:
                if response.status == 200:
                    story_ids = await response.json()
                    
                    # Check first 100 stories
                    for story_id in story_ids[:100]:
                        try:
                            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                            async with self.session.get(story_url) as story_response:
                                if story_response.status == 200:
                                    story = await story_response.json()
                                    
                                    if not story or story.get('type') != 'story':
                                        continue
                                    
                                    title = story.get('title', '').lower()
                                    
                                    # Check if title contains relevant keywords
                                    relevant = any(keyword.lower() in title 
                                                 for keyword in DATA_SOURCES['hackernews_keywords'])
                                    
                                    if relevant:
                                        published_date = datetime.fromtimestamp(story.get('time', 0))
                                        
                                        # Only include recent posts (last 3 days)
                                        if (datetime.now() - published_date).days <= 3:
                                            update_data = {
                                                'source': 'hackernews',
                                                'source_id': str(story_id),
                                                'title': f"HN: {story.get('title', '')}",
                                                'content': story.get('text', ''),
                                                'url': f"https://news.ycombinator.com/item?id={story_id}",
                                                'published_date': published_date,
                                                'metadata': {
                                                    'score': story.get('score', 0),
                                                    'descendants': story.get('descendants', 0),
                                                    'type': 'hackernews_story'
                                                }
                                            }
                                            updates.append(update_data)
                                            self.db.add_update(**update_data)
                        
                        except Exception as e:
                            print(f"Error processing HN story {story_id}: {e}")
                            continue
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                        if len(updates) >= 20:  # Limit to 20 relevant HN posts
                            break
            
            self.db.set_cache(cache_key, updates, 2)  # Cache for 2 hours
            
        except Exception as e:
            print(f"Error collecting HackerNews data: {e}")
        
        return updates
    
    def categorize_updates(self, updates: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize updates based on content and keywords"""
        categorized = {category: [] for category in CONTENT_CATEGORIES.keys()}
        categorized['other'] = []
        
        for update in updates:
            title_lower = update['title'].lower()
            content_lower = (update.get('content') or '').lower()
            combined_text = f"{title_lower} {content_lower}"
            
            categorized_flag = False
            
            # Check each category
            for category_key, category_info in CONTENT_CATEGORIES.items():
                keywords = category_info['keywords']
                
                if any(keyword.lower() in combined_text for keyword in keywords):
                    update['category'] = category_key
                    categorized[category_key].append(update)
                    categorized_flag = True
                    break
            
            if not categorized_flag:
                update['category'] = 'other'
                categorized['other'].append(update)
        
        return categorized


# Utility functions
async def main():
    """Test the data collector"""
    async with DataCollector() as collector:
        updates = await collector.collect_all_data()
        
        for category, items in updates.items():
            print(f"\n{category.upper()}: {len(items)} items")
            for item in items[:3]:  # Show first 3 items
                print(f"  - {item['title']}")


if __name__ == "__main__":
    asyncio.run(main())