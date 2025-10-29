# bot/news_sentiment.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
import json
from dataclasses import dataclass
import numpy as np
from textblob import TextBlob
import feedparser
import requests
import calendar
import time

@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    content: str
    source: str
    published_at: datetime
    sentiment_score: float
    relevance_score: float
    impact_score: float
    symbols_mentioned: List[str]
    categories: List[str]

@dataclass
class SentimentAnalysis:
    """Sentiment analysis result"""
    overall_sentiment: float  # -1 to 1 scale
    sentiment_label: str  # 'bearish', 'neutral', 'bullish'
    confidence: float  # 0 to 1
    news_volume: int
    relevant_articles: List[NewsArticle]
    impact_assessment: str
    should_trade: bool

class EnhancedNewsSentimentAnalyzer:
    """Advanced news sentiment analysis for crypto trading"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Set logging level to WARNING to hide news output
        logging.getLogger('NewsSentimentAnalyzer').setLevel(logging.WARNING)

        self.logger = logging.getLogger('NewsSentimentAnalyzer')
        self.config = config or {}
        
        # News sources configuration
        self.news_sources = {
            'crypto_specific': [
                'https://cointelegraph.com/rss',
                'https://coindesk.com/arc/outboundfeeds/rss/',
                'https://cryptopotato.com/feed/',
                'https://cryptonews.com/news/feed/',
                'https://ambcrypto.com/feed/'
            ],
            'financial_general': [
                'https://feeds.finance.yahoo.com/rss/2.0/headline',
                'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'https://feeds.reuters.com/reuters/businessNews'
            ],
            'reddit': [
                'https://www.reddit.com/r/CryptoCurrency.rss',
                'https://www.reddit.com/r/Bitcoin.rss',
                'https://www.reddit.com/r/ethereum.rss'
            ]
        }
        
        # Sentiment keywords and weights
        self.sentiment_keywords = {
            'extremely_bullish': {
                'keywords': ['moon', 'bull run', 'massive gains', 'explosive growth', 'breakthrough', 
                           'revolutionary', 'game changer', 'unprecedented', 'surge', 'skyrocket'],
                'weight': 1.0
            },
            'bullish': {
                'keywords': ['bullish', 'positive', 'growth', 'rise', 'increase', 'gains', 'pump',
                           'adoption', 'partnership', 'upgrade', 'improvement', 'optimistic', 'rally'],
                'weight': 0.7
            },
            'neutral': {
                'keywords': ['stable', 'steady', 'consolidation', 'sideways', 'unchanged', 'flat'],
                'weight': 0.0
            },
            'bearish': {
                'keywords': ['bearish', 'negative', 'decline', 'fall', 'drop', 'crash', 'dump',
                           'correction', 'pullback', 'weakness', 'concern', 'risk', 'uncertainty'],
                'weight': -0.7
            },
            'extremely_bearish': {
                'keywords': ['crash', 'collapse', 'plummet', 'disaster', 'panic', 'catastrophe',
                           'devastating', 'major losses', 'bloodbath', 'nightmare'],
                'weight': -1.0
            }
        }
        
        # Market impact indicators
        self.impact_indicators = {
            'high_impact': ['regulation', 'ban', 'adoption', 'institutional', 'etf', 'sec', 'fed',
                          'government', 'central bank', 'major hack', 'exchange hack'],
            'medium_impact': ['partnership', 'upgrade', 'fork', 'listing', 'delisting', 'whale movement',
                            'developer activity', 'funding'],
            'low_impact': ['price analysis', 'technical analysis', 'opinion', 'prediction', 'rumor']
        }
        
        # Symbol mappings for better matching
        self.symbol_mappings = {
            'bitcoin': ['BTC', 'BTCUSD', 'BTCUSDT'],
            'ethereum': ['ETH', 'ETHUSD', 'ETHUSDT'],
            'binance coin': ['BNB', 'BNBUSD', 'BNBUSDT'],
            'dogecoin': ['DOGE', 'DOGEUSD', 'DOGEUSDT'],
            'cardano': ['ADA'],
            'solana': ['SOL'],
            'polkadot': ['DOT'],
            'chainlink': ['LINK']
        }
        
        # Cache for news articles
        self.news_cache = {}
        self.cache_duration = timedelta(minutes=15)

    async def analyze_market_sentiment(self, 
                                     symbols: List[str], 
                                     hours_back: int = 24,
                                     min_relevance: float = 0.3) -> Dict[str, SentimentAnalysis]:
        """
        Analyze sentiment for multiple trading symbols
        
        Args:
            symbols: List of trading symbols to analyze
            hours_back: Hours of news to analyze
            min_relevance: Minimum relevance score for articles
            
        Returns:
            Dictionary mapping symbols to sentiment analysis
        """
        
        try:
            # Fetch recent news
            news_articles = await self._fetch_recent_news(hours_back)
            
            results = {}
            
            for symbol in symbols:
                # Filter relevant articles for this symbol
                relevant_articles = self._filter_relevant_articles(news_articles, symbol, min_relevance)
                
                # Analyze sentiment
                sentiment_analysis = self._analyze_articles_sentiment(relevant_articles, symbol)
                
                results[symbol] = sentiment_analysis
            
            return results
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            # Return neutral sentiment for all symbols
            return {symbol: self._get_neutral_sentiment() for symbol in symbols}

    async def _fetch_recent_news(self, hours_back: int) -> List[NewsArticle]:
        """Fetch recent news from all configured sources"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        all_articles = []
        
        # Check cache first
        cache_key = f"news_{hours_back}h"
        if cache_key in self.news_cache:
            cached_time, cached_articles = self.news_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_articles
        
        # Fetch from RSS feeds
        for source_type, urls in self.news_sources.items():
            for url in urls:
                try:
                    articles = await self._fetch_rss_feed(url, cutoff_time, source_type)
                    all_articles.extend(articles)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to fetch from {url}: {e}")
                    continue
        
        # Cache results
        self.news_cache[cache_key] = (datetime.now(), all_articles)
        
        self.logger.info(f"Fetched {len(all_articles)} news articles from last {hours_back} hours")
        return all_articles

    async def _fetch_rss_feed(self, 
                            url: str, 
                            cutoff_time: datetime, 
                            source_type: str) -> List[NewsArticle]:
        """Fetch and parse RSS feed"""
        
        try:
            # Use feedparser for RSS feeds
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries:
                try:
                    self.logger.debug(f"Processing entry: {entry}")
                    # Parse publication date
                    pub_date = None
                    try:
                        # Handle both dictionary-like and object-like entries
                        published_parsed = None
                        # Try to get published_parsed from dictionary or object
                        if isinstance(entry, dict):
                            published_parsed = entry.get('published_parsed')
                            self.logger.debug(f"Got published_parsed from dict: {published_parsed}")
                        else:
                            published_parsed = getattr(entry, 'published_parsed', None)
                            self.logger.debug(f"Got published_parsed from object: {published_parsed}")
                        
                        if published_parsed:
                            pub_date = self._parse_date(published_parsed)
                            self.logger.debug(f"Parsed date: {pub_date}")
                        
                        # If that didn't work, try updated_parsed
                        if pub_date is None:
                            updated_parsed = None
                            # Try to get updated_parsed from dictionary or object
                            if isinstance(entry, dict):
                                updated_parsed = entry.get('updated_parsed')
                                self.logger.debug(f"Got updated_parsed from dict: {updated_parsed}")
                            else:
                                updated_parsed = getattr(entry, 'updated_parsed', None)
                                self.logger.debug(f"Got updated_parsed from object: {updated_parsed}")
                            
                            if updated_parsed:
                                pub_date = self._parse_date(updated_parsed)
                                self.logger.debug(f"Parsed date from updated: {pub_date}")
                                
                    except (TypeError, ValueError, Exception) as date_error:
                        self.logger.debug(f"Date parsing error: {date_error}")
                        pub_date = None
                    
                    # If we still don't have a date, use current time
                    if pub_date is None:
                        pub_date = datetime.now()
                        self.logger.debug(f"Using current time: {pub_date}")
                    
                    # Skip old articles - but only if we're actually filtering by date
                    # For tests, we want to include all articles unless they're explicitly old
                    self.logger.debug(f"Comparing dates - pub_date: {pub_date}, cutoff_time: {cutoff_time}")
                    if pub_date < cutoff_time:
                        self.logger.debug("Skipping old article")
                        continue
                    
                    # Extract content
                    # Handle both dictionary-like and object-like entries
                    title = ''
                    content = ''
                    if isinstance(entry, dict):
                        title = str(entry.get('title', ''))
                        content = str(entry.get('summary', entry.get('description', '')))
                    else:
                        title = str(getattr(entry, 'title', ''))
                        content = str(getattr(entry, 'summary', getattr(entry, 'description', '')))
                    
                    self.logger.debug(f"Title: {title}, Content: {content}")
                    
                    # Clean HTML tags
                    content = re.sub(r'<[^>]+>', '', content)
                    
                    # Get source name
                    source_name = url
                    if isinstance(feed, dict) and 'feed' in feed:
                        feed_feed = feed.get('feed')
                        if isinstance(feed_feed, dict) and 'title' in feed_feed:
                            source_name = str(feed_feed.get('title', url))
                    else:
                        feed_feed = getattr(feed, 'feed', None)
                        if feed_feed and hasattr(feed_feed, 'title'):
                            source_name = str(getattr(feed_feed, 'title', url))
                    
                    # Create article object
                    article = NewsArticle(
                        title=title,
                        content=content,
                        source=source_name,
                        published_at=pub_date,
                        sentiment_score=0.0,  # Will be calculated later
                        relevance_score=0.0,  # Will be calculated later
                        impact_score=0.0,     # Will be calculated later
                        symbols_mentioned=[],  # Will be populated later
                        categories=[source_type]
                    )
                    
                    articles.append(article)
                    self.logger.debug(f"Added article: {article}")
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing article: {e}")
                    continue
            
            self.logger.debug(f"Returning {len(articles)} articles")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching RSS feed {url}: {e}")
            return []

    def _parse_date(self, date_obj) -> Optional[datetime]:
        """Parse various date formats into datetime object"""
        try:
            self.logger.debug(f"_parse_date called with: {date_obj} (type: {type(date_obj)})")
            
            if date_obj is None:
                self.logger.debug("date_obj is None")
                return None
                
            # Handle struct_time
            if isinstance(date_obj, time.struct_time):
                self.logger.debug(f"Parsing struct_time: {date_obj}")
                result = datetime(*date_obj[:6])
                self.logger.debug(f"Parsed struct_time result: {result}")
                return result
            
            # Handle tuple/list
            if isinstance(date_obj, (tuple, list)) and len(date_obj) >= 6:
                self.logger.debug(f"Parsing tuple/list: {date_obj}")
                # Convert to proper tuple of integers
                time_elements = []
                for item in date_obj[:6]:
                    if isinstance(item, (int, float)):
                        time_elements.append(int(item))
                    else:
                        try:
                            time_elements.append(int(str(item)))
                        except (ValueError, TypeError):
                            time_elements.append(0)
                result = datetime(*time_elements)
                self.logger.debug(f"Parsed tuple/list result: {result}")
                return result
            
            # Handle other formats that can be converted with calendar.timegm
            # Only proceed if it's a valid type for calendar.timegm
            if isinstance(date_obj, (tuple, list)) and len(date_obj) >= 6:
                try:
                    self.logger.debug(f"Parsing with calendar.timegm: {date_obj}")
                    # Convert to proper tuple of integers for calendar.timegm
                    time_elements = []
                    for item in date_obj[:6]:
                        if isinstance(item, (int, float)):
                            time_elements.append(int(item))
                        else:
                            try:
                                time_elements.append(int(str(item)))
                            except (ValueError, TypeError):
                                time_elements.append(0)
                    timestamp = calendar.timegm(tuple(time_elements))
                    result = datetime.fromtimestamp(timestamp)
                    self.logger.debug(f"Parsed calendar.timegm result: {result}")
                    return result
                except Exception as timegm_error:
                    self.logger.debug(f"calendar.timegm parsing failed: {timegm_error}")
                    pass
                
            self.logger.debug(f"Date parsing failed for: {date_obj}")
            return None
        except Exception as e:
            self.logger.debug(f"Date parsing failed with exception: {e}")
            return None

    def _filter_relevant_articles(self, 
                                articles: List[NewsArticle], 
                                symbol: str, 
                                min_relevance: float) -> List[NewsArticle]:
        """Filter articles relevant to a specific symbol"""
        
        relevant_articles = []
        
        for article in articles:
            # Only calculate relevance score if not already set
            if article.relevance_score == 0.0:
                relevance_score = self._calculate_relevance_score(article, symbol)
                article.relevance_score = relevance_score
            else:
                relevance_score = article.relevance_score
            
            if relevance_score >= min_relevance:
                # Only extract symbols if not already set
                if not article.symbols_mentioned:
                    article.symbols_mentioned = self._extract_mentioned_symbols(article.title + " " + article.content)
                relevant_articles.append(article)
        
        # Sort by relevance score
        relevant_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return relevant_articles

    def _calculate_relevance_score(self, article: NewsArticle, symbol: str) -> float:
        """Calculate how relevant an article is to a trading symbol"""
        
        text = (article.title + " " + article.content).lower()
        relevance_score = 0.0
        
        # Direct symbol mention
        if symbol.lower() in text:
            relevance_score += 0.8
        
        # Symbol without pair (e.g., 'BTC' from 'BTC/USD')
        base_symbol = symbol.split('/')[0].lower()
        if base_symbol in text:
            relevance_score += 0.6
        
        # Coin name mention
        for coin_name, symbols in self.symbol_mappings.items():
            if coin_name in text and any(s.lower() == base_symbol for s in symbols):
                relevance_score += 0.7
                break
        
        # General crypto relevance
        crypto_terms = ['crypto', 'cryptocurrency', 'blockchain', 'bitcoin', 'altcoin', 'defi']
        for term in crypto_terms:
            if term in text:
                relevance_score += 0.2
                break
        
        # Title gets higher weight
        title_relevance = 0.0
        if base_symbol in article.title.lower():
            title_relevance += 0.5
        
        return min(relevance_score + title_relevance, 1.0)

    def _extract_mentioned_symbols(self, text: str) -> List[str]:
        """Extract crypto symbols mentioned in text"""
        
        symbols_found = []
        text_lower = text.lower()
        
        for coin_name, symbols in self.symbol_mappings.items():
            if coin_name in text_lower:
                symbols_found.extend(symbols)
        
        # Look for direct symbol mentions
        symbol_pattern = r'\b(BTC|ETH|BNB|ADA|DOT|LINK|SOL|DOGE|USDT|USDC)\b'
        found_symbols = re.findall(symbol_pattern, text.upper())
        symbols_found.extend(found_symbols)
        
        return list(set(symbols_found))

    def _analyze_articles_sentiment(self, 
                                  articles: List[NewsArticle], 
                                  symbol: str) -> SentimentAnalysis:
        """Analyze sentiment from a collection of articles"""
        
        if not articles:
            return self._get_neutral_sentiment()
        
        sentiment_scores = []
        impact_scores = []
        
        for article in articles:
            # Calculate sentiment using multiple methods
            textblob_sentiment = self._get_textblob_sentiment(article.title + " " + article.content)
            keyword_sentiment = self._get_keyword_sentiment(article.title + " " + article.content)
            
            # Combine sentiments (weighted average)
            combined_sentiment = (textblob_sentiment * 0.4) + (keyword_sentiment * 0.6)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(article.title + " " + article.content)
            
            # Weight by relevance and recency
            time_weight = self._calculate_time_weight(article.published_at)
            relevance_weight = article.relevance_score
            
            final_weight = time_weight * relevance_weight * (1 + impact_score)
            
            sentiment_scores.append(combined_sentiment * final_weight)
            impact_scores.append(impact_score)
            
            # Store calculated scores
            article.sentiment_score = combined_sentiment
            article.impact_score = impact_score
        
        # Calculate overall sentiment
        if sentiment_scores:
            overall_sentiment = np.average(sentiment_scores)
            confidence = self._calculate_confidence(sentiment_scores, len(articles))
        else:
            overall_sentiment = 0.0
            confidence = 0.0
        
        # Determine sentiment label
        if overall_sentiment > 0.3:
            sentiment_label = 'bullish'
        elif overall_sentiment < -0.3:
            sentiment_label = 'bearish'
        else:
            sentiment_label = 'neutral'
        
        # Calculate average impact
        avg_impact = np.mean(impact_scores) if impact_scores else 0.0
        
        # Determine impact assessment
        if avg_impact > 0.7:
            impact_assessment = 'high'
        elif avg_impact > 0.4:
            impact_assessment = 'medium'
        else:
            impact_assessment = 'low'
        
        # Trading recommendation
        should_trade = self._should_trade_based_on_sentiment(
            float(overall_sentiment), float(confidence), float(avg_impact), len(articles)
        )
        
        return SentimentAnalysis(
            overall_sentiment=float(overall_sentiment),
            sentiment_label=sentiment_label,
            confidence=confidence,
            news_volume=len(articles),
            relevant_articles=articles[:10],  # Top 10 most relevant
            impact_assessment=impact_assessment,
            should_trade=should_trade
        )

    def _get_textblob_sentiment(self, text: str) -> float:
        """Get sentiment using TextBlob"""
        try:
            blob = TextBlob(text)
            # TextBlob returns polarity from -1 to 1
            return float(blob.sentiment.polarity)  # type: ignore
        except Exception as e:
            self.logger.debug(f"TextBlob sentiment analysis failed: {e}")
            return 0.0

    def _get_keyword_sentiment(self, text: str) -> float:
        """Get sentiment based on keyword matching"""
        
        text_lower = text.lower()
        sentiment_score = 0.0
        total_weight = 0.0
        
        for sentiment_type, data in self.sentiment_keywords.items():
            keywords = data['keywords']
            weight = data['weight']
            
            for keyword in keywords:
                if keyword in text_lower:
                    # Count occurrences for emphasis
                    count = text_lower.count(keyword)
                    sentiment_score += weight * count
                    total_weight += abs(weight) * count
        
        # Normalize by total weight
        if total_weight > 0:
            return np.clip(sentiment_score / total_weight, -1.0, 1.0)
        else:
            return 0.0

    def _calculate_impact_score(self, text: str) -> float:
        """Calculate potential market impact of news"""
        
        text_lower = text.lower()
        impact_score = 0.0
        
        # High impact indicators - count up to 2
        high_count = 0
        for indicator in self.impact_indicators['high_impact']:
            if indicator in text_lower:
                high_count += 1
                if high_count <= 2:  # Allow up to 2 high impact indicators
                    impact_score += 0.4  # 0.4 each, up to 0.8 total
        
        # Medium impact indicators - count up to 2
        medium_count = 0
        for indicator in self.impact_indicators['medium_impact']:
            if indicator in text_lower:
                medium_count += 1
                if medium_count <= 2:  # Limit to 2 for medium impact
                    impact_score += 0.15
        
        # Low impact indicators - count up to 2
        low_count = 0
        for indicator in self.impact_indicators['low_impact']:
            if indicator in text_lower:
                low_count += 1
                if low_count <= 2:  # Limit to 2 for low impact
                    impact_score += 0.05
        
        return min(impact_score, 1.0)

    def _calculate_time_weight(self, pub_date: datetime) -> float:
        """Calculate time-based weight (newer news is more important)"""
        
        hours_ago = (datetime.now() - pub_date).total_seconds() / 3600
        
        if hours_ago <= 1:
            return 1.0
        elif hours_ago <= 6:
            return 0.8
        elif hours_ago <= 12:
            return 0.6
        elif hours_ago <= 24:
            return 0.4
        else:
            return 0.2

    def _calculate_confidence(self, sentiment_scores: List[float], article_count: int) -> float:
        """Calculate confidence in sentiment analysis"""
        
        if not sentiment_scores:
            return 0.0
        
        # Base confidence on agreement between articles
        sentiment_std = np.std(sentiment_scores)
        agreement_confidence = max(0.0, 1.0 - float(sentiment_std))
        
        # Volume confidence (more articles = higher confidence, up to a point)
        volume_confidence = min(article_count / 10, 1.0)
        
        # Combined confidence
        overall_confidence = (agreement_confidence * 0.7) + (volume_confidence * 0.3)
        
        return overall_confidence

    def _should_trade_based_on_sentiment(self, 
                                       sentiment: float,
                                       confidence: float,
                                       impact: float,
                                       article_count: int) -> bool:
        """Determine if trading should proceed based on sentiment analysis"""
        
        # Don't trade on neutral sentiment
        if abs(sentiment) < 0.2:
            return True  # Neutral news doesn't block trading
        
        # Strong negative sentiment with high confidence blocks trading
        if sentiment < -0.5 and confidence > 0.7 and impact > 0.5:
            return False
        
        # Very high impact negative news blocks trading regardless
        if sentiment < -0.3 and impact > 0.8:
            return False
        
        # Low confidence sentiment analysis shouldn't block trading
        if confidence < 0.3:
            return True
        
        # Otherwise allow trading
        return True

    def _get_neutral_sentiment(self) -> SentimentAnalysis:
        """Return neutral sentiment analysis"""
        return SentimentAnalysis(
            overall_sentiment=0.0,
            sentiment_label='neutral',
            confidence=0.5,
            news_volume=0,
            relevant_articles=[],
            impact_assessment='low',
            should_trade=True
        )

    def get_sentiment_summary(self, 
                            sentiment_results: Dict[str, SentimentAnalysis]) -> Dict[str, Any]:
        """Get summary of sentiment analysis results"""
        
        summary = {
            'overall_market_sentiment': 0.0,
            'high_confidence_signals': [],
            'trading_blockers': [],
            'bullish_symbols': [],
            'bearish_symbols': [],
            'neutral_symbols': [],
            'total_news_volume': 0
        }
        
        sentiments = []
        
        for symbol, analysis in sentiment_results.items():
            sentiments.append(analysis.overall_sentiment)
            summary['total_news_volume'] += analysis.news_volume
            
            # Categorize symbols
            if analysis.sentiment_label == 'bullish':
                summary['bullish_symbols'].append(symbol)
            elif analysis.sentiment_label == 'bearish':
                summary['bearish_symbols'].append(symbol)
            else:
                summary['neutral_symbols'].append(symbol)
            
            # High confidence signals
            if analysis.confidence > 0.7 and abs(analysis.overall_sentiment) > 0.4:
                summary['high_confidence_signals'].append({
                    'symbol': symbol,
                    'sentiment': analysis.sentiment_label,
                    'confidence': analysis.confidence,
                    'impact': analysis.impact_assessment
                })
            
            # Trading blockers
            if not analysis.should_trade:
                summary['trading_blockers'].append({
                    'symbol': symbol,
                    'reason': f"{analysis.sentiment_label} sentiment with {analysis.impact_assessment} impact"
                })
        
        # Overall market sentiment
        if sentiments:
            summary['overall_market_sentiment'] = np.mean(sentiments)
        
        return summary