import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import threading
import webbrowser
import traceback
import logging
import json
from datetime import datetime
import os
from bs4 import BeautifulSoup
import re
import numpy as np
from collections import Counter
import string

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Political bias sources mapping
LEFT_LEANING_SOURCES = [
    "cnn", "msnbc", "nbc", "abc", "cbs", "new york times", "nyt", "washington post", 
    "huffpost", "huffington post", "vox", "slate", "the guardian", "mother jones", 
    "the atlantic", "politico", "buzzfeed", "daily beast", "time magazine"
]

RIGHT_LEANING_SOURCES = [
    "fox news", "breitbart", "the daily caller", "the blaze", "newsmax", "oann", 
    "new york post", "washington times", "washington examiner", "national review", 
    "the federalist", "daily wire", "epoch times", "townhall"
]

CENTRIST_SOURCES = [
    "reuters", "associated press", "ap", "bloomberg", "the hill", "axios", "c-span", 
    "bbc", "financial times", "wall street journal", "wsj", "usa today", "christian science monitor"
]

# API keys
NEWS_API_KEY = "Your_API_key"
GNEWS_API_KEY = "Your_API_key"

# API limits
NEWS_API_LIMIT = 100  # NewsAPI free tier: 100 requests per day
GNEWS_API_LIMIT = 100  # GNews free tier: 100 requests per day

# Available themes
THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "fg": "white",
        "entry_bg": "#333333",
        "entry_fg": "white",
        "button_bg": "#444444",
        "button_fg": "white",
        "results_bg": "#2d2d2d",
        "results_fg": "#e0e0e0",
        "scrollbar_bg": "#444444",
        "scrollbar_fg": "#666666",
        "link_color": "#3a96dd",
        "error_color": "#ff6b6b",
        "warning_color": "#ff6b6b"
    },
    "cyberpunk": {
        "bg": "#0f0f2d",
        "fg": "#00ffff",
        "entry_bg": "#1a1a3a",
        "entry_fg": "#00ffff",
        "button_bg": "#ff00ff",
        "button_fg": "black",
        "results_bg": "#0f0f2d",
        "results_fg": "#00ffff",
        "scrollbar_bg": "#ff00ff",
        "scrollbar_fg": "#00ffff",
        "link_color": "#ff00ff",
        "error_color": "#ff3333",
        "warning_color": "#ff3333"
    },
    "forest": {
        "bg": "#1e3b2c",
        "fg": "#c8e6c9",
        "entry_bg": "#2d4f3c",
        "entry_fg": "#ffffff",
        "button_bg": "#4caf50",
        "button_fg": "white",
        "results_bg": "#1e3b2c",
        "results_fg": "#c8e6c9",
        "scrollbar_bg": "#4caf50",
        "scrollbar_fg": "#81c784",
        "link_color": "#8bc34a",
        "error_color": "#ff7043",
        "warning_color": "#ff7043"
    },
    "midnight": {
        "bg": "#121212",
        "fg": "#bb86fc",
        "entry_bg": "#1f1f1f",
        "entry_fg": "#bb86fc",
        "button_bg": "#6200ee",
        "button_fg": "white",
        "results_bg": "#121212",
        "results_fg": "#e0e0e0",
        "scrollbar_bg": "#6200ee",
        "scrollbar_fg": "#bb86fc",
        "link_color": "#03dac6",
        "error_color": "#cf6679",
        "warning_color": "#cf6679"
    }
}

class ApiUsageTracker:
    """Track API usage across sessions"""
    
    def __init__(self):
        self.usage_file = "api_usage.json"
        self.usage = self.load_usage()
    
    def load_usage(self):
        """Load usage data from file"""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                logger.error("Failed to load API usage data")
        
        # Default usage data
        return {
            "newsapi": {
                "count": 0,
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            "gnews": {
                "count": 0,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
        }
    
    def save_usage(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f)
        except:
            logger.error("Failed to save API usage data")
    
    def increment_usage(self, api_name):
        """Increment usage count for the specified API"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset counter if it's a new day
        if self.usage[api_name]["date"] != today:
            self.usage[api_name]["count"] = 0
            self.usage[api_name]["date"] = today
        
        # Increment counter
        self.usage[api_name]["count"] += 1
        self.save_usage()
        
        return self.usage[api_name]["count"]
    
    def get_usage(self, api_name):
        """Get current usage count for the specified API"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset counter if it's a new day
        if self.usage[api_name]["date"] != today:
            self.usage[api_name]["count"] = 0
            self.usage[api_name]["date"] = today
            self.save_usage()
        
        return self.usage[api_name]["count"]
    
    def get_remaining(self, api_name):
        """Get remaining requests for the specified API"""
        limit = NEWS_API_LIMIT if api_name == "newsapi" else GNEWS_API_LIMIT
        return limit - self.get_usage(api_name)

class NewsSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("News Search")
        
        # Initialize API usage tracker
        self.api_tracker = ApiUsageTracker()
        
        # No longer using external text summarizer
        
        # Set default theme
        self.current_theme = "dark"
        self.theme_var = tk.StringVar(value=self.current_theme)
        
        # API selection
        self.api_var = tk.StringVar(value="newsapi")
        
        # Initial size - taller to ensure API selection is visible before search
        self.root.geometry("600x100")
        self.root.resizable(True, True)
        
        # Apply theme
        self.apply_theme(self.current_theme)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # API selection frame at the top
        self.api_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.api_frame.pack(fill=tk.X, pady=5)
        
        # API selection label with more emphasis
        api_label = tk.Label(self.api_frame, 
                            text="Select API:", 
                            font=('Arial', 10, 'bold'),
                            bg=THEMES[self.current_theme]["bg"],
                            fg=THEMES[self.current_theme]["fg"])
        api_label.pack(side=tk.LEFT, padx=5)
        
        # API selection radio buttons
        self.newsapi_radio = tk.Radiobutton(self.api_frame, 
                                           text="NewsAPI", 
                                           variable=self.api_var, 
                                           value="newsapi",
                                           bg=THEMES[self.current_theme]["bg"], 
                                           fg=THEMES[self.current_theme]["fg"], 
                                           selectcolor=THEMES[self.current_theme]["entry_bg"], 
                                           activebackground=THEMES[self.current_theme]["bg"],
                                           command=self.update_usage_display)
        self.newsapi_radio.pack(side=tk.LEFT, padx=5)
        
        self.gnews_radio = tk.Radiobutton(self.api_frame, 
                                         text="GNews", 
                                         variable=self.api_var, 
                                         value="gnews",
                                         bg=THEMES[self.current_theme]["bg"], 
                                         fg=THEMES[self.current_theme]["fg"], 
                                         selectcolor=THEMES[self.current_theme]["entry_bg"], 
                                         activebackground=THEMES[self.current_theme]["bg"],
                                         command=self.update_usage_display)
        self.gnews_radio.pack(side=tk.LEFT, padx=5)
        
        self.firefox_radio = tk.Radiobutton(self.api_frame, 
                                          text="Firefox", 
                                          variable=self.api_var, 
                                          value="firefox",
                                          bg=THEMES[self.current_theme]["bg"], 
                                          fg=THEMES[self.current_theme]["fg"], 
                                          selectcolor=THEMES[self.current_theme]["entry_bg"], 
                                          activebackground=THEMES[self.current_theme]["bg"],
                                          command=self.update_usage_display)
        self.firefox_radio.pack(side=tk.LEFT, padx=5)
        
        # API usage display
        self.usage_var = tk.StringVar()
        self.usage_label = tk.Label(self.api_frame,
                                   textvariable=self.usage_var,
                                   bg=THEMES[self.current_theme]["bg"],
                                   fg=THEMES[self.current_theme]["fg"])
        self.usage_label.pack(side=tk.LEFT, padx=5)
        
        # Update usage display
        self.update_usage_display()
        
        # Create search frame
        self.search_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.search_frame.pack(fill=tk.X, pady=5)
        
        # Search entry with theme
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_frame, 
                                    textvariable=self.search_var, 
                                    font=('Arial', 12), 
                                    width=30,
                                    bg=THEMES[self.current_theme]["entry_bg"],
                                    fg=THEMES[self.current_theme]["entry_fg"],
                                    insertbackground=THEMES[self.current_theme]["fg"])
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", self.search)
        
        # Search button with magnifier icon
        self.search_button = tk.Button(self.search_frame, 
                                      text="🔍", 
                                      font=('Arial', 10),
                                      bg=THEMES[self.current_theme]["button_bg"],
                                      fg=THEMES[self.current_theme]["button_fg"],
                                      activebackground=THEMES[self.current_theme]["button_bg"],
                                      activeforeground=THEMES[self.current_theme]["button_fg"],
                                      command=self.search)
        self.search_button.pack(side=tk.RIGHT, padx=5)
        
        # Results area (initially hidden)
        self.results_frame = ttk.Frame(self.main_frame, style='TFrame')
        
        # Results text widget (initially not packed)
        self.results_text = scrolledtext.ScrolledText(self.results_frame, 
                                                     wrap=tk.WORD, 
                                                     font=('Arial', 10),
                                                     bg=THEMES[self.current_theme]["results_bg"],
                                                     fg=THEMES[self.current_theme]["results_fg"],
                                                     insertbackground=THEMES[self.current_theme]["fg"])
        
        # Configure scrollbar colors
        self.customize_scrollbar(self.results_text)
        
        # Configure tags for the text widget
        self.results_text.tag_configure("title", font=('Arial', 12, 'bold'), foreground=THEMES[self.current_theme]["fg"])
        self.results_text.tag_configure("link", foreground=THEMES[self.current_theme]["link_color"], underline=1)
        self.results_text.tag_configure("summary", font=('Arial', 10), foreground=THEMES[self.current_theme]["fg"])
        self.results_text.tag_configure("bullet", font=('Arial', 10, 'bold'), foreground=THEMES[self.current_theme]["fg"])
        self.results_text.tag_configure("rating", font=('Arial', 9, 'italic'), foreground=THEMES[self.current_theme]["fg"])
        self.results_text.tag_configure("error", font=('Arial', 10), foreground=THEMES[self.current_theme]["error_color"])
        self.results_text.tag_configure("left_bias", font=('Arial', 9, 'italic'), foreground="#3a96dd")  # Blue for left
        self.results_text.tag_configure("right_bias", font=('Arial', 9, 'italic'), foreground="#ff6b6b")  # Red for right
        self.results_text.tag_configure("center_bias", font=('Arial', 9, 'italic'), foreground="#4caf50")  # Green for center
        self.results_text.tag_configure("enhanced", font=('Arial', 10, 'italic'), foreground=THEMES[self.current_theme]["fg"])
        
        # Status bar (initially hidden)
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = tk.Label(self.root, 
                                  textvariable=self.status_var, 
                                  relief=tk.SUNKEN, 
                                  anchor=tk.W,
                                  bg=THEMES[self.current_theme]["entry_bg"],
                                  fg=THEMES[self.current_theme]["fg"])
        
        # Store clickable links
        self.links = []
        
        from open_link import open_link
        self.results_text.tag_bind("link", "<Button-1>", open_link)
        self.results_text.tag_bind("link", "<Enter>", lambda e: self.results_text.config(cursor="hand2"))
        self.results_text.tag_bind("link", "<Leave>", lambda e: self.results_text.config(cursor=""))
        
        # Flag to track if the UI is expanded
        self.is_expanded = False
        
        # Theme selection
        theme_label = tk.Label(self.api_frame, 
                              text="Theme:", 
                              bg=THEMES[self.current_theme]["bg"],
                              fg=THEMES[self.current_theme]["fg"])
        theme_label.pack(side=tk.LEFT, padx=(15, 5))
        
        # Theme dropdown
        self.theme_menu = ttk.Combobox(self.api_frame, 
                                      textvariable=self.theme_var,
                                      values=list(THEMES.keys()),
                                      width=10,
                                      state="readonly")
        self.theme_menu.pack(side=tk.LEFT, padx=5)
        self.theme_menu.bind("<<ComboboxSelected>>", self.change_theme)
    
    def update_results(self, message):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, message, "error")
        self.status_var.set("Ready")
    
    def determine_political_bias(self, source_name, content=None):
        """Determine the political bias of a news source or content"""
        if not source_name and not content:
            return "Not applicable"
            
        # First check source name
        if source_name:
            source_lower = source_name.lower()
            
            # Check for exact matches first
            for source in LEFT_LEANING_SOURCES:
                if source == source_lower:
                    return "Mostly left leaning"
                    
            for source in RIGHT_LEANING_SOURCES:
                if source == source_lower:
                    return "Mostly right leaning"
                    
            for source in CENTRIST_SOURCES:
                if source == source_lower:
                    return "Mostly central"
            
            # Check for partial matches
            for source in LEFT_LEANING_SOURCES:
                if source in source_lower or source_lower in source:
                    return "Slightly left leaning"
                    
            for source in RIGHT_LEANING_SOURCES:
                if source in source_lower or source_lower in source:
                    return "Slightly right leaning"
                    
            for source in CENTRIST_SOURCES:
                if source in source_lower or source_lower in source:
                    return "Mostly central"
        
        # If we couldn't determine bias from source, analyze content if available
        if content:
            content_lower = content.lower()
            
            # Count occurrences of politically charged terms
            left_count = 0
            right_count = 0
            
            for term in LEFT_LEANING_TERMS:
                if term in content_lower:
                    left_count += 1
                    
            for term in RIGHT_LEANING_TERMS:
                if term in content_lower:
                    right_count += 1
            
            # Determine bias based on term frequency
            if left_count > right_count:
                if left_count >= right_count + 3:
                    return "Mostly left leaning"
                else:
                    return "Slightly left leaning"
            elif right_count > left_count:
                if right_count >= left_count + 3:
                    return "Mostly right leaning"
                else:
                    return "Slightly right leaning"
            elif left_count > 0 or right_count > 0:
                return "Mostly central"
                
        return "Not applicable"

    def update_usage_display(self):
        """Update the API usage display"""
        api_name = self.api_var.get()
        
        if api_name == "firefox":
            # Firefox scraping doesn't have a usage limit
            self.usage_var.set("No API limit")
            self.usage_label.config(fg=THEMES[self.current_theme]["fg"])
            return
            
        usage = self.api_tracker.get_usage(api_name)
        limit = NEWS_API_LIMIT if api_name == "newsapi" else GNEWS_API_LIMIT
        remaining = limit - usage
        
        # Format the usage text
        usage_text = f"Usage: {usage}/{limit} ({remaining} left)"
        
        # Update the label text
        self.usage_var.set(usage_text)
        
        # Change color if running low
        if remaining <= 15:
            self.usage_label.config(fg=THEMES[self.current_theme]["warning_color"])
        else:
            self.usage_label.config(fg=THEMES[self.current_theme]["fg"])
    
    def customize_scrollbar(self, widget):
        """Customize scrollbar colors for the widget"""
        # This works on Windows and some Linux systems
        try:
            # Configure vertical scrollbar
            widget.vbar.config(
                troughcolor=THEMES[self.current_theme]["bg"],
                background=THEMES[self.current_theme]["scrollbar_bg"],
                activebackground=THEMES[self.current_theme]["scrollbar_fg"]
            )
        except:
            # If customization fails, just continue
            pass
    
    def apply_theme(self, theme_name):
        """Apply the selected theme to all UI elements"""
        if theme_name not in THEMES:
            theme_name = "dark"
        
        self.current_theme = theme_name
        theme = THEMES[theme_name]
        
        # Configure root window
        self.root.configure(bg=theme["bg"])
        
        # Configure ttk style
        style = ttk.Style()
        style.theme_use('clam')  # Use a theme that can be customized
        style.configure('TFrame', background=theme["bg"])
        style.configure('TButton', background=theme["button_bg"], foreground=theme["button_fg"])
        style.configure('TLabel', background=theme["bg"], foreground=theme["fg"])
        style.configure('Search.TButton', font=('Arial', 10), background=theme["button_bg"])
        style.configure('TCombobox', fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"])
        
        # Update existing widgets if they exist
        if hasattr(self, 'search_entry'):
            self.search_entry.config(
                bg=theme["entry_bg"],
                fg=theme["entry_fg"],
                insertbackground=theme["fg"]
            )
            
            self.search_button.config(
                bg=theme["button_bg"],
                fg=theme["button_fg"],
                activebackground=theme["button_bg"],
                activeforeground=theme["button_fg"]
            )
            
            self.results_text.config(
                bg=theme["results_bg"],
                fg=theme["results_fg"]
            )
            
            self.customize_scrollbar(self.results_text)
            
            # Update text tags
            self.results_text.tag_configure("title", foreground=theme["fg"])
            self.results_text.tag_configure("link", foreground=theme["link_color"])
            self.results_text.tag_configure("summary", foreground=theme["fg"])
            self.results_text.tag_configure("bullet", foreground=theme["fg"])
            self.results_text.tag_configure("rating", foreground=theme["fg"])
            self.results_text.tag_configure("error", foreground=theme["error_color"])
            
            # Update status bar
            self.status_bar.config(
                bg=theme["entry_bg"],
                fg=theme["fg"]
            )
            
            # Update API frame widgets
            for widget in self.api_frame.winfo_children():
                if isinstance(widget, tk.Label) or isinstance(widget, tk.Radiobutton):
                    widget.config(
                        bg=theme["bg"],
                        fg=theme["fg"]
                    )
                    if isinstance(widget, tk.Radiobutton):
                        widget.config(
                            selectcolor=theme["entry_bg"],
                            activebackground=theme["bg"]
                        )
            
            # Update usage label color if needed
            api_name = self.api_var.get()
            remaining = self.api_tracker.get_remaining(api_name)
            if remaining <= 15:
                self.usage_label.config(fg=theme["warning_color"])
    
    def change_theme(self, event=None):
        """Change the application theme"""
        new_theme = self.theme_var.get()
        self.apply_theme(new_theme)
    
    def expand_ui(self):
        """Expand the UI to show results area"""
        if not self.is_expanded:
            self.root.geometry("600x500")
            self.results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.results_text.pack(fill=tk.BOTH, expand=True)
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            self.is_expanded = True
    
    def search(self, event=None):
        query = self.search_var.get().strip()
        if not query:
            return
        
        # Expand UI if not already expanded
        self.expand_ui()
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.links = []
        self.status_var.set("Searching for: " + query)
        
        # Start search in a separate thread to keep UI responsive
        threading.Thread(target=self.perform_search, args=(query,), daemon=True).start()
    
    def is_advertisement(self, article):
        """Check if an article is likely an advertisement"""
        # Check title and snippet for ad indicators
        text_to_check = (article.get('title', '') + ' ' + article.get('snippet', '') + ' ' + 
                            article.get('source', '')).lower()
        
        # Check for ad indicators
        for indicator in AD_INDICATORS:
            if indicator.lower() in text_to_check:
                return True
                
        # Check for suspicious URLs
        link = article.get('link', '').lower()
        if link and ('product' in link or 'shop' in link or 'buy' in link or 'offer' in link or 
                    'deal' in link or 'sale' in link or 'discount' in link):
            return True
            
        return False

    def enhance_top_articles(self, articles):
        """Fetch additional content for top articles to enhance the summary"""
        enhanced_articles = []
        
        for article in articles:
            try:
                # Skip if article is an advertisement
                if self.is_advertisement(article):
                    logger.debug(f"Skipping advertisement: {article.get('title')}")
                    continue
                    
                # Create a copy of the article to avoid modifying the original
                enhanced_article = article.copy()
                
                # Only try to enhance if we have a valid URL
                if enhanced_article.get('link') and enhanced_article['link'].startswith('http'):
                    # Fetch the article content
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    response = requests.get(enhanced_article['link'], headers=headers, timeout=3)
                    
                    if response.status_code == 200:
                        # Parse the HTML
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Try to extract the main content
                        # First, look for article tags
                        article_content = soup.find('article')
                        
                        # If no article tag, try common content containers
                        if not article_content:
                            article_content = soup.find('div', class_=['content', 'article-content', 'story-content', 'entry-content', 'post-content'])
                        
                        if article_content:
                            # Extract paragraphs
                            paragraphs = article_content.find_all('p')
                            
                            # Get the first few paragraphs
                            content = ""
                            full_content = ""
                            for p in paragraphs[:5]:  # First 5 paragraphs for full analysis
                                text = p.get_text().strip()
                                full_content += text + " "
                                if len(content) < 200:  # Only add to visible content if under limit
                                    content += text + " "
                            
                            # Check if the full content suggests this is an ad
                            if any(indicator.lower() in full_content.lower() for indicator in AD_INDICATORS):
                                logger.debug(f"Skipping advertisement detected from content: {enhanced_article.get('title')}")
                                continue
                            
                            # Truncate visible content to a reasonable length
                            if content:
                                content = content[:200] + "..." if len(content) > 200 else content
                                enhanced_article['enhanced_content'] = content
                                
                                # If political bias is "Not applicable", try to determine from content
                                if enhanced_article.get('political_bias') == "Not applicable" and full_content:
                                    new_bias = self.determine_political_bias(None, full_content)
                                    if new_bias != "Not applicable":
                                        enhanced_article['political_bias'] = new_bias + " (content analysis)"
                
                enhanced_articles.append(enhanced_article)
                
            except Exception as e:
                # If enhancement fails, just use the original article
                logger.error(f"Error enhancing article: {e}")
                enhanced_articles.append(article)
                
        return enhanced_articles
    
    def generate_summary(self, query, articles):
        """Generate a brief summary of the news results as a bulleted list"""
        if not articles:
            return "No relevant information found."
        
        # Create a simple bulleted list summary
        summary = f"Top stories about '{query}':\n\n"
        
        # Try to fetch additional content for top articles
        enhanced_articles = self.enhance_top_articles(articles[:3])
        
        # Extract key information from each article
        for i, article in enumerate(enhanced_articles):  # Limit to top 5 articles
            # Get the source and date
            source_info = f"{article['source']}"
            if article['time']:
                source_info += f" ({article['time']})"
                
            # Get the title or a snippet
            headline = article['title']
            
            # Add relevance stars
            stars = "★" * article['rating'] + "☆" * (5 - article['rating'])
            
            # Get political bias
            political_bias = article.get('political_bias', 'Not applicable')
            
            # Add to summary with bullet point, relevance rating and political bias
            summary += f"• {headline}\n  {source_info} • Relevance: {stars} • Bias: {political_bias}\n"
            
            # Add enhanced content if available
            if article.get('enhanced_content'):
                summary += f"  Key points: {article['enhanced_content']}\n"
            
            summary += "\n"
            
            # Stop after 5 articles to keep it concise
            if i >= 4:
                break
        
        return summary
    
    def display_results(self, query, articles):
        if not articles:
            self.update_results("No relevant news found.")
            return

        self.results_text.insert(tk.END, f"Search Results for: {query}\n\n", "title")

        # Display a summary first
        self.results_text.insert(tk.END, "QUICK SUMMARY (Sorted by Relevance):\n", "title")
        summary = self.generate_summary(query, articles)
        self.results_text.insert(tk.END, f"{summary}\n", "summary")

        # Display individual articles
        self.results_text.insert(tk.END, "FULL ARTICLE DETAILS (Sorted by Relevance):\n\n", "title")

        for i, article in enumerate(articles):
            # Insert title as a clickable link
            self.results_text.insert(tk.END, f"{i+1}. {article['title']}\n", "title")
            
            # Insert source and time
            source_time = f"{article['source']}"
            if article['time']:
                source_time += f" • {article['time']}"
            self.results_text.insert(tk.END, f"{source_time}\n", "summary")
            
            # Insert snippet
            if article['snippet']:
                self.results_text.insert(tk.END, f"{article['snippet']}\n", "summary")
            
            # Insert link
            link_start = self.results_text.index(tk.INSERT)
            self.results_text.insert(tk.END, "Read more", "link")
            link_end = self.results_text.index(tk.INSERT)
            self.links.append((link_start, link_end, article['link']))
            
            # Insert rating
            stars = "★" * article['rating'] + "☆" * (5 - article['rating'])
            self.results_text.insert(tk.END, f" • Relevance: {stars}", "rating")
            
            # Insert political bias
            political_bias = article.get('political_bias', 'Not applicable')
            self.results_text.insert(tk.END, f" • Political Bias: {political_bias}\n\n", "rating")

        self.status_var.set(f"Found {len(articles)} news articles about {query}")

    def perform_search(self, query):
        try:
            api_choice = self.api_var.get()
            
            if api_choice == "newsapi":
                articles = self.search_newsapi(query)
            elif api_choice == "gnews":
                articles = self.search_gnews(query)
            else:  # firefox
                articles = self.search_firefox(query)
            
            # Filter out advertisements
            original_count = len(articles)
            articles = [article for article in articles if not self.is_advertisement(article)]
            filtered_count = original_count - len(articles)
            
            if filtered_count > 0:
                logger.debug(f"Filtered out {filtered_count} advertisements")
            
            # Sort articles by relevance score (rating) in descending order
            if articles:
                articles.sort(key=lambda x: x['rating'], reverse=True)
            
            # Update usage display
            self.root.after(0, self.update_usage_display)
            
            if articles:
                # Update status to show we're enhancing articles
                status_msg = f"Found {len(articles)} articles"
                if filtered_count > 0:
                    status_msg += f" (filtered {filtered_count} ads)"
                status_msg += ", enhancing summaries..."
                self.root.after(0, lambda: self.status_var.set(status_msg))
                
                # Update the UI with results
                self.root.after(0, lambda: self.display_results(query, articles))
            else:
                self.root.after(0, lambda: self.update_results(
                    f"No news found for '{query}'. Try a different search term or API source."
                ))
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            logger.error(traceback.format_exc())
            self.root.after(0, lambda: self.update_results(
                f"Error searching: {str(e)}\n\n" +
                "See console for detailed error information."
            ))
    
    def search_newsapi(self, query):
        """Search using NewsAPI.org"""
        # Increment usage counter
        self.api_tracker.increment_usage("newsapi")
        
        # Add exclusions for ads using NOT operator
        url = f"https://newsapi.org/v2/everything?q={query} NOT advertisement NOT sponsored NOT promotion&sortBy=publishedAt&language=en&pageSize=10"
        headers = {"X-Api-Key": NEWS_API_KEY}
        
        logger.debug(f"Searching NewsAPI with query: {query}")
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return self.create_mock_results(query, f"API Error: {data.get('message', 'Unknown error')}")
        
        articles = []
        for item in data.get("articles", []):
            # Parse the date if available
            published_date = ""
            if item.get("publishedAt"):
                try:
                    date_obj = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                    published_date = date_obj.strftime("%b %d, %Y")
                except:
                    published_date = item["publishedAt"]
            
            source_name = item.get("source", {}).get("name", "Unknown Source")
            snippet = item.get("description", "")
            
            # Try to determine bias from source first, then from content if needed
            political_bias = self.determine_political_bias(source_name, snippet)
            
            articles.append({
                "title": item.get("title", "No title"),
                "link": item.get("url", ""),
                "source": source_name,
                "time": published_date,
                "snippet": snippet,
                "rating": self.calculate_rating(item),
                "image": item.get("urlToImage", ""),
                "political_bias": political_bias
            })
        
        return articles
    
    def search_gnews(self, query):
        """Search using GNews API"""
        # Increment usage counter
        self.api_tracker.increment_usage("gnews")
        
        # Add exclusions for ads
        url = f"https://gnews.io/api/v4/search?q={query} -advertisement -sponsored -promotion&lang=en&max=10&apikey={GNEWS_API_KEY}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if "articles" not in data:
                logger.error(f"GNews API error: {data.get('errors', ['Unknown error'])}")
                return self.create_mock_results(query, f"API Error: {data.get('errors', ['Unknown error'])}")
            
            articles = []
            for item in data.get("articles", []):
                # Parse the date if available
                published_date = ""
                if item.get("publishedAt"):
                    try:
                        date_obj = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                        published_date = date_obj.strftime("%b %d, %Y")
                    except:
                        published_date = item["publishedAt"]
                
                source_name = item.get("source", {}).get("name", "Unknown Source")
                snippet = item.get("description", "")
                
                # Try to determine bias from source first, then from content if needed
                political_bias = self.determine_political_bias(source_name, snippet)
                
                articles.append({
                    "title": item.get("title", "No title"),
                    "link": item.get("url", ""),
                    "source": source_name,
                    "time": published_date,
                    "snippet": snippet,
                    "rating": 3,  # Default rating for GNews
                    "image": item.get("image", ""),
                    "political_bias": political_bias
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"GNews API error: {e}")
            return self.create_mock_results(query, f"API Error: {str(e)}")
            
    def search_firefox(self, query):
        """Search using Firefox with web scraping"""
        try:
            # Format query for Firefox search - add "-ad -advertisement -sponsored" to exclude ads
            search_url = f"https://news.search.yahoo.com/search?p={query}+-ad+-advertisement+-sponsored"
            
            # Use Firefox user agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
            
            logger.debug(f"Searching Yahoo News with query: {query}")
            response = requests.get(search_url, headers=headers)
            
            # Save HTML to file for debugging
            with open("firefox_debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            if response.status_code != 200:
                logger.error(f"Yahoo News search error: Status code {response.status_code}")
                return []
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract news articles
            articles = []
            
            # Find news article containers
            news_items = soup.select('div.NewsArticle')
            
            if not news_items:
                # Try alternative selectors if the primary one doesn't work
                news_items = soup.select('li.js-stream-content')
            
            if not news_items:
                # Another fallback
                news_items = soup.select('div.algo.news')
            
            logger.debug(f"Found {len(news_items)} news items")
            
            for i, item in enumerate(news_items[:10]):  # Limit to 10 results
                try:
                    # Extract title and link
                    title_elem = item.select_one('h4') or item.select_one('h3') or item.select_one('.title')
                    link_elem = item.select_one('a')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link = link_elem.get('href', '')
                    
                    # Extract source and time
                    source_elem = item.select_one('.s-source') or item.select_one('.provider')
                    time_elem = item.select_one('.s-time') or item.select_one('.datetime')
                    
                    source = source_elem.text.strip() if source_elem else "Unknown Source"
                    time = time_elem.text.strip() if time_elem else ""
                    
                    # Extract snippet
                    snippet_elem = item.select_one('.s-desc') or item.select_one('.abstract')
                    snippet = snippet_elem.text.strip() if snippet_elem else ""
                    
                    # Calculate rating (1-5)
                    rating = 3  # Default rating
                    if len(snippet) > 150:
                        rating += 1
                    if title.lower().find(query.lower()) >= 0:
                        rating += 1
                    rating = min(5, max(1, rating))
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': source,
                        'time': time,
                        'snippet': snippet,
                        'rating': rating,
                        'image': "",
                        'political_bias': self.determine_political_bias(source, snippet)
                    })
                    
                    logger.debug(f"Extracted article: {title}")
                    
                except Exception as e:
                    logger.error(f"Error extracting article {i}: {e}")
            
            # If Yahoo News didn't work, try Bing News as fallback
            if not articles:
                logger.debug("Yahoo News extraction failed, trying Bing News")
                articles = self.search_bing_news(query)
            
            return articles
            
        except Exception as e:
            logger.error(f"Firefox search error: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def search_bing_news(self, query):
        """Search using Bing News as a fallback for Firefox option"""
        try:
            # Add exclusions for ads
            search_url = f"https://www.bing.com/news/search?q={query}+-advertisement+-sponsored+-promotion"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
            
            response = requests.get(search_url, headers=headers)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            news_items = soup.select('.news-card')
            
            for item in news_items[:10]:
                try:
                    title_elem = item.select_one('a.title')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    
                    source_elem = item.select_one('.source')
                    time_elem = item.select_one('.time')
                    
                    source = source_elem.text.strip() if source_elem else "Unknown Source"
                    time = time_elem.text.strip() if time_elem else ""
                    
                    snippet_elem = item.select_one('.snippet')
                    snippet = snippet_elem.text.strip() if snippet_elem else ""
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'source': source,
                        'time': time,
                        'snippet': snippet,
                        'rating': 3,
                        'image': "",
                        'political_bias': self.determine_political_bias(source, snippet)
                    })
                    
                except Exception:
                    continue
            
            return articles
            
        except Exception:
            return []
    
    def calculate_rating(self, article):
        """Calculate a relevance rating for an article (1-5 stars)"""
        rating = 3  # Default rating
        
        # Adjust based on content length
        if article.get("description"):
            desc_len = len(article["description"])
            if desc_len > 200:
                rating += 1
            elif desc_len < 50:
                rating -= 1
        
        # Adjust based on source
        if article.get("source", {}).get("name") in ["BBC News", "CNN", "The New York Times", "Reuters", "Associated Press"]:
            rating += 1
        
        # Ensure rating is between 1-5
        return max(1, min(5, rating))
        
# Define emotional language indicators
LEFT_LEANING_TERMS = [
    "progressive", "liberal", "equality", "reform", "social justice", "climate crisis", 
    "systemic", "marginalized", "diversity", "inclusive", "privilege", "rights", 
    "undocumented", "gun control", "universal healthcare", "green new deal"
]

RIGHT_LEANING_TERMS = [
    "conservative", "traditional", "freedom", "patriot", "taxpayer", "illegal alien", 
    "border security", "law and order", "family values", "religious liberty", 
    "second amendment", "pro-life", "socialism", "radical", "woke", "cancel culture"
]

# Ad detection patterns
AD_INDICATORS = [
    "sponsored", "advertisement", "promoted", "buy now", "limited time offer", 
    "discount", "sale", "% off", "click here", "shop now", "subscribe now",
    "special offer", "promotion", "deal", "best price", "free shipping"
]

def create_mock_results(self, query, message=None):
    """Create mock results when API is not available"""
    mock_message = message or "API key required. This is mock data."
    
    return [
        {
            'title': f"Latest updates on {query}",
            'link': f"https://news.google.com/search?q={query}",
            'source': "News Source",
            'time': "Today",
            'snippet': f"{mock_message} Click to search for '{query}' on Google News.",
            'rating': 3,
            'image': "",
            'political_bias': "Not applicable"
        },
        {
            'title': f"How to get real news data for {query}",
            'link': "https://newsapi.org/register",
            'source': "NewsAPI.org",
            'time': "",
            'snippet': "Register for a free NewsAPI.org account to get real news data. The free tier allows 100 requests per day.",
            'rating': 4,
            'image': "",
            'political_bias': "Not applicable"
        }
    ]

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = NewsSearchApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
