"""
HTML report generator for daily intelligence briefing
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from jinja2 import Template, Environment, FileSystemLoader

from config import REPORTS_DIR, REPORT_CONFIG, CONTENT_CATEGORIES, BASE_DIR
from database import DatabaseManager


class HTMLGenerator:
    """Generates professional newspaper-style HTML reports"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.template_dir = BASE_DIR / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Create templates if they don't exist
        self._ensure_templates()
    
    def _ensure_templates(self):
        """Create HTML templates if they don't exist"""
        main_template_path = self.template_dir / "main.html"
        
        if not main_template_path.exists():
            self._create_main_template()
        
        css_path = self.template_dir / "styles.css"
        if not css_path.exists():
            self._create_css_file()
    
    def _create_main_template(self):
        """Create the main HTML template"""
        template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.title }} - {{ report_date.strftime('%B %d, %Y') }}</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Sans+Pro:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script>
        // Dark mode toggle
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('dark-mode', isDark);
            document.getElementById('theme-toggle').textContent = isDark ? '☀️' : '🌙';
        }
        
        // Load saved theme
        document.addEventListener('DOMContentLoaded', function() {
            const savedTheme = localStorage.getItem('dark-mode');
            if (savedTheme === 'true') {
                document.body.classList.add('dark-mode');
                document.getElementById('theme-toggle').textContent = '☀️';
            }
        });
    </script>
</head>
<body>
    <header class="header">
        <div class="header-top">
            <div class="date-time">{{ report_date.strftime('%A, %B %d, %Y') }}</div>
            <button id="theme-toggle" class="theme-toggle" onclick="toggleDarkMode()">🌙</button>
        </div>
        <div class="masthead">
            <h1 class="title">{{ config.title }}</h1>
            <div class="subtitle">{{ config.subtitle }}</div>
        </div>
        <div class="summary-bar">
            <span class="update-count">{{ total_updates }} New Updates Today</span>
            <span class="categories-count">{{ categories|length }} Categories</span>
            <span class="generated-time">Generated at {{ generated_at.strftime('%I:%M %p') }}</span>
        </div>
    </header>

    <main class="main-content">
        {% if categories %}
            <div class="top-stories">
                <h2 class="section-title">Today's Headlines</h2>
                <div class="headlines-grid">
                    {% for category_key, updates in categories.items() %}
                        {% if updates and category_key != 'other' %}
                            {% for update in updates[:2] %}
                                <article class="headline-card priority-{{ update.importance_score|int }}">
                                    <div class="category-tag">{{ category_info[category_key].title }}</div>
                                    <h3 class="headline-title">
                                        <a href="{{ update.url }}" target="_blank" rel="noopener">{{ update.title }}</a>
                                    </h3>
                                    <div class="headline-meta">
                                        <span class="source">{{ update.source|upper }}</span>
                                        <span class="time">{{ update.published_date.strftime('%I:%M %p') }}</span>
                                        {% if update.importance_score >= 8 %}
                                            <span class="breaking">BREAKING</span>
                                        {% endif %}
                                    </div>
                                    {% if update.content %}
                                        <p class="headline-summary">{{ update.content[:200] }}...</p>
                                    {% endif %}
                                </article>
                            {% endfor %}
                        {% endif %}
                    {% endfor %}
                </div>
            </div>

            {% for category_key, updates in categories.items() %}
                {% if updates and category_key != 'other' %}
                    <section class="category-section">
                        <div class="section-header">
                            <h2 class="section-title">{{ category_info[category_key].title }}</h2>
                            <span class="section-count">{{ updates|length }} updates</span>
                        </div>
                        
                        <div class="articles-grid">
                            {% for update in updates %}
                                <article class="article-card priority-{{ update.importance_score|int }}">
                                    <div class="article-header">
                                        <h3 class="article-title">
                                            <a href="{{ update.url }}" target="_blank" rel="noopener">
                                                {{ update.title }}
                                            </a>
                                        </h3>
                                        <div class="article-meta">
                                            <span class="source">{{ update.source|upper }}</span>
                                            <span class="time">{{ update.published_date.strftime('%m/%d %I:%M%p') }}</span>
                                            <span class="score">Score: {{ update.importance_score|round(1) }}</span>
                                        </div>
                                    </div>
                                    
                                    {% if update.content %}
                                        <div class="article-content">
                                            <p>{{ update.content[:300] }}{% if update.content|length > 300 %}...{% endif %}</p>
                                        </div>
                                    {% endif %}
                                    
                                    {% if update.metadata %}
                                        <div class="article-tags">
                                            {% set metadata = update.metadata|from_json %}
                                            {% if metadata.version %}
                                                <span class="tag">v{{ metadata.version }}</span>
                                            {% endif %}
                                            {% if metadata.repo %}
                                                <span class="tag">{{ metadata.repo }}</span>
                                            {% endif %}
                                            {% if metadata.type %}
                                                <span class="tag">{{ metadata.type }}</span>
                                            {% endif %}
                                        </div>
                                    {% endif %}
                                </article>
                            {% endfor %}
                        </div>
                    </section>
                {% endif %}
            {% endfor %}

            {% if categories.other %}
                <section class="category-section other-section">
                    <div class="section-header">
                        <h2 class="section-title">Other Updates</h2>
                        <span class="section-count">{{ categories.other|length }} updates</span>
                    </div>
                    
                    <div class="other-updates">
                        {% for update in categories.other %}
                            <div class="other-update">
                                <a href="{{ update.url }}" target="_blank" rel="noopener" class="other-link">
                                    {{ update.title }}
                                </a>
                                <span class="other-meta">{{ update.source|upper }} - {{ update.published_date.strftime('%m/%d') }}</span>
                            </div>
                        {% endfor %}
                    </div>
                </section>
            {% endif %}
        {% else %}
            <div class="no-updates">
                <h2>No New Updates Today</h2>
                <p>No significant updates were found in the monitored sources. Check back tomorrow!</p>
            </div>
        {% endif %}
    </main>

    <footer class="footer">
        <div class="footer-content">
            <p>&copy; {{ report_date.year }} AI Intelligence Briefing System</p>
            <p>Generated automatically at {{ generated_at.strftime('%I:%M %p') }} | Next update tomorrow at 5:00 AM</p>
        </div>
    </footer>
</body>
</html>'''
        
        with open(self.template_dir / "main.html", "w") as f:
            f.write(template_content)
    
    def _create_css_file(self):
        """Create the CSS stylesheet"""
        css_content = '''/* AI Intelligence Briefing Styles */

:root {
    --primary-color: #1a1a1a;
    --secondary-color: #333;
    --accent-color: #2563eb;
    --text-color: #333;
    --text-light: #666;
    --background: #ffffff;
    --surface: #f8fafc;
    --border: #e2e8f0;
    --shadow: rgba(0, 0, 0, 0.1);
    
    --font-serif: 'Playfair Display', Georgia, serif;
    --font-sans: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, sans-serif;
}

.dark-mode {
    --primary-color: #ffffff;
    --secondary-color: #e5e7eb;
    --accent-color: #3b82f6;
    --text-color: #f3f4f6;
    --text-light: #d1d5db;
    --background: #111827;
    --surface: #1f2937;
    --border: #374151;
    --shadow: rgba(0, 0, 0, 0.3);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: var(--font-sans);
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background);
    transition: background-color 0.3s, color 0.3s;
}

/* Header Styles */
.header {
    background: var(--surface);
    border-bottom: 3px solid var(--accent-color);
    padding: 1rem 2rem;
    margin-bottom: 2rem;
}

.header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: var(--text-light);
}

.theme-toggle {
    background: none;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    padding: 0.5rem;
    cursor: pointer;
    font-size: 1rem;
    background-color: var(--surface);
    color: var(--text-color);
    transition: all 0.3s;
}

.theme-toggle:hover {
    background-color: var(--accent-color);
    color: white;
}

.masthead {
    text-align: center;
    margin-bottom: 1rem;
}

.title {
    font-family: var(--font-serif);
    font-size: 3rem;
    font-weight: 900;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: -1px;
    margin-bottom: 0.5rem;
}

.subtitle {
    font-size: 1.1rem;
    color: var(--text-light);
    font-style: italic;
}

.summary-bar {
    display: flex;
    justify-content: center;
    gap: 2rem;
    padding: 1rem;
    background: var(--accent-color);
    color: white;
    border-radius: 0.5rem;
    font-weight: 600;
}

/* Main Content */
.main-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

/* Top Stories */
.top-stories {
    margin-bottom: 3rem;
}

.section-title {
    font-family: var(--font-serif);
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
    border-bottom: 2px solid var(--accent-color);
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
}

.headlines-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.headline-card {
    background: var(--surface);
    border-radius: 0.5rem;
    padding: 1.5rem;
    box-shadow: 0 2px 10px var(--shadow);
    border-left: 4px solid var(--accent-color);
    transition: transform 0.3s, box-shadow 0.3s;
}

.headline-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px var(--shadow);
}

.headline-card.priority-10,
.headline-card.priority-9 {
    border-left-color: #dc2626;
    background: linear-gradient(135deg, var(--surface) 0%, rgba(220, 38, 38, 0.05) 100%);
}

.headline-card.priority-8,
.headline-card.priority-7 {
    border-left-color: #ea580c;
    background: linear-gradient(135deg, var(--surface) 0%, rgba(234, 88, 12, 0.05) 100%);
}

.category-tag {
    display: inline-block;
    background: var(--accent-color);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.headline-title {
    font-family: var(--font-serif);
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    line-height: 1.3;
}

.headline-title a {
    color: var(--primary-color);
    text-decoration: none;
    transition: color 0.3s;
}

.headline-title a:hover {
    color: var(--accent-color);
}

.headline-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 0.85rem;
    color: var(--text-light);
}

.breaking {
    background: #dc2626;
    color: white;
    padding: 0.15rem 0.5rem;
    border-radius: 0.25rem;
    font-weight: 700;
    font-size: 0.7rem;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.headline-summary {
    color: var(--text-light);
    font-size: 0.9rem;
    line-height: 1.5;
}

/* Category Sections */
.category-section {
    margin-bottom: 3rem;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.section-count {
    background: var(--surface);
    color: var(--text-light);
    padding: 0.5rem 1rem;
    border-radius: 1rem;
    font-size: 0.85rem;
    border: 1px solid var(--border);
}

.articles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
}

.article-card {
    background: var(--surface);
    border-radius: 0.5rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px var(--shadow);
    border: 1px solid var(--border);
    transition: all 0.3s;
}

.article-card:hover {
    box-shadow: 0 4px 15px var(--shadow);
    transform: translateY(-1px);
}

.article-header {
    margin-bottom: 1rem;
}

.article-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    line-height: 1.4;
}

.article-title a {
    color: var(--text-color);
    text-decoration: none;
    transition: color 0.3s;
}

.article-title a:hover {
    color: var(--accent-color);
}

.article-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.8rem;
    color: var(--text-light);
}

.article-content {
    margin-bottom: 1rem;
    color: var(--text-light);
    font-size: 0.9rem;
    line-height: 1.5;
}

.article-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.tag {
    background: var(--accent-color);
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.7rem;
    font-weight: 500;
}

/* Other Updates */
.other-section {
    border-top: 2px solid var(--border);
    padding-top: 2rem;
}

.other-updates {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 0.75rem;
}

.other-update {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--surface);
    border-radius: 0.25rem;
    border: 1px solid var(--border);
    transition: background-color 0.3s;
}

.other-update:hover {
    background: var(--accent-color);
    color: white;
}

.other-link {
    color: var(--text-color);
    text-decoration: none;
    font-weight: 500;
    flex: 1;
    margin-right: 1rem;
    transition: color 0.3s;
}

.other-update:hover .other-link,
.other-update:hover .other-meta {
    color: white;
}

.other-meta {
    font-size: 0.8rem;
    color: var(--text-light);
    flex-shrink: 0;
}

/* No Updates */
.no-updates {
    text-align: center;
    padding: 4rem 2rem;
    background: var(--surface);
    border-radius: 0.5rem;
    margin: 2rem 0;
}

.no-updates h2 {
    font-family: var(--font-serif);
    font-size: 2rem;
    margin-bottom: 1rem;
    color: var(--text-light);
}

/* Footer */
.footer {
    margin-top: 4rem;
    padding: 2rem;
    background: var(--surface);
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--text-light);
    font-size: 0.9rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .header {
        padding: 1rem;
    }
    
    .title {
        font-size: 2rem;
    }
    
    .main-content {
        padding: 0 1rem;
    }
    
    .headlines-grid,
    .articles-grid {
        grid-template-columns: 1fr;
    }
    
    .summary-bar {
        flex-direction: column;
        gap: 0.5rem;
        text-align: center;
    }
    
    .section-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
    
    .other-update {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
}

/* Print Styles */
@media print {
    .theme-toggle {
        display: none;
    }
    
    .article-card,
    .headline-card {
        break-inside: avoid;
        box-shadow: none;
        border: 1px solid #ccc;
    }
}'''
        
        with open(self.template_dir / "styles.css", "w") as f:
            f.write(css_content)
    
    def generate_report(self, report_date: datetime = None) -> str:
        """Generate HTML report for the given date"""
        if report_date is None:
            report_date = datetime.now().date()
        
        print(f"Generating HTML report for {report_date}")
        
        # Get new updates since last report
        new_updates = self.db.get_new_updates()
        
        # Categorize updates
        categorized_updates = self._categorize_updates(new_updates)
        
        # Filter and limit updates per category
        for category in categorized_updates:
            # Sort by importance and date (handle timezone issues)
            def safe_sort_key(x):
                importance = x.get('importance_score', 0)
                pub_date = x.get('published_date', datetime.min)
                
                # Convert to timezone-naive datetime for comparison
                if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo is not None:
                    pub_date = pub_date.replace(tzinfo=None)
                
                return (importance, pub_date)
            
            categorized_updates[category].sort(key=safe_sort_key, reverse=True)
            
            # Limit to max items per category
            max_items = REPORT_CONFIG['max_items_per_category']
            categorized_updates[category] = categorized_updates[category][:max_items]
        
        # Prepare template context
        context = {
            'config': REPORT_CONFIG,
            'report_date': report_date if isinstance(report_date, datetime) else datetime.combine(report_date, datetime.min.time()),
            'generated_at': datetime.now(),
            'categories': categorized_updates,
            'category_info': CONTENT_CATEGORIES,
            'total_updates': len(new_updates),
            'from_json': self._from_json_filter
        }
        
        # Load and render template
        template = self.env.get_template('main.html')
        
        # Add custom filter
        self.env.filters['from_json'] = self._from_json_filter
        
        html_content = template.render(**context)
        
        # Save report
        report_filename = f"ai_briefing_{report_date.strftime('%Y%m%d')}.html"
        report_path = REPORTS_DIR / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Copy CSS to report directory
        css_source = self.template_dir / "styles.css"
        css_dest = REPORTS_DIR / "styles.css"
        
        if css_source.exists():
            import shutil
            shutil.copy2(css_source, css_dest)
        
        # Record report in database
        self.db.add_report(
            datetime.combine(report_date, datetime.min.time()) if not isinstance(report_date, datetime) else report_date,
            str(report_path),
            len(new_updates),
            {'categories': len([cat for cat, items in categorized_updates.items() if items])}
        )
        
        print(f"Report generated: {report_path}")
        return str(report_path)
    
    def _categorize_updates(self, updates: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize updates based on content"""
        categorized = {category: [] for category in CONTENT_CATEGORIES.keys()}
        categorized['other'] = []
        
        for update in updates:
            # Parse metadata if it's a JSON string
            if isinstance(update.get('metadata'), str):
                try:
                    import json
                    update['metadata'] = json.loads(update['metadata'])
                except:
                    pass
            
            # Ensure published_date is a datetime object
            if isinstance(update.get('published_date'), str):
                try:
                    from datetime import datetime
                    pub_date = datetime.fromisoformat(update['published_date'])
                    # Convert to timezone-naive for consistency
                    if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo is not None:
                        pub_date = pub_date.replace(tzinfo=None)
                    update['published_date'] = pub_date
                except:
                    update['published_date'] = datetime.now()
            elif not update.get('published_date'):
                update['published_date'] = datetime.now()
            else:
                # Ensure existing datetime is timezone-naive
                pub_date = update['published_date']
                if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo is not None:
                    update['published_date'] = pub_date.replace(tzinfo=None)
            
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
    
    def _from_json_filter(self, value):
        """Jinja2 filter to parse JSON strings"""
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except:
                return {}
        return value if isinstance(value, dict) else {}


# Test function
def main():
    """Test the HTML generator"""
    generator = HTMLGenerator()
    report_path = generator.generate_report()
    print(f"Test report generated at: {report_path}")


if __name__ == "__main__":
    main()