# 🔍 News Search Application

A Python desktop application for searching and analyzing news articles from multiple sources with political bias detection.

## 🌟 Features

- **Multiple News Sources**: Search using NewsAPI, GNews API, or web scraping (Firefox mode)
- **Political Bias Detection**: Analyzes news sources and content to determine political leaning
- **Ad Filtering**: Automatically detects and filters out advertisements
- **Article Enhancement**: Fetches additional content to provide better summaries
- **Customizable Themes**: Choose from Dark, Cyberpunk, Forest, and Midnight themes
- **API Usage Tracking**: Monitors API usage to prevent exceeding daily limits

## 🚀 Getting Started

### Prerequisites
- Python 3.6+
- Required packages: tkinter, requests, beautifulsoup4, numpy

### API Setup
1. **NewsAPI**:
   - Visit [NewsAPI.org](https://newsapi.org/)
   - Click "Get API Key" and create a free account
   - After registration, copy your API key from the dashboard

2. **GNews API**:
   - Go to [GNews API](https://gnews.io/)
   - Sign up for a free account
   - Once registered, find your API key in your account dashboard

3. **API Configuration**:
   - The application will prompt you to enter your API keys on first run
   - Alternatively, you can use Firefox mode which doesn't require API keys

### Installation
1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python news_search.py
   ```

## 🔧 Usage

1. Select your preferred API source (NewsAPI, GNews, or Firefox)
2. Enter your search query in the search box
3. Press Enter or click the search button
4. View search results with summaries, political bias indicators, and relevance ratings
5. Click "Read more" links to open articles in your default browser

## 🎨 Themes

The application includes four themes:
- **Dark**: Classic dark mode
- **Cyberpunk**: Futuristic blue and pink
- **Forest**: Natural green tones
- **Midnight**: Purple and teal accents

## 📊 Political Bias Detection

The application analyzes news sources and content to determine political bias:
- Left-leaning sources and terminology are highlighted in blue
- Right-leaning sources and terminology are highlighted in red
- Centrist sources are highlighted in green

## 🔄 API Usage

- NewsAPI: Limited to 100 requests per day
- GNews API: Limited to 100 requests per day
- Firefox mode: Uses web scraping with no API limits

## 🛠️ Future Improvements

- Add more news sources and APIs
- Implement more advanced political bias detection algorithms
- Improve article summarization techniques
- Add user-configurable API keys
- Fine-tune article and summary algorithms for better accuracy
- Enhance ad detection capabilities

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [NewsAPI](https://newsapi.org/) for providing news data
- [GNews API](https://gnews.io/) for additional news sources
