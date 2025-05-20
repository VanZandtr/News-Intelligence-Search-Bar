import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
from collections import Counter
import string
import logging
import re
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

logger = logging.getLogger(__name__)

class TextSummarizer:
    """Simple extractive text summarization"""
    
    def __init__(self):
        # Add error handling for stopwords initialization
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        self.punctuation = set(string.punctuation)
    
    def preprocess_text(self, text):
        """Clean and tokenize text"""
        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = ''.join([c for c in text if c not in self.punctuation])
        
        # Tokenize into sentences with error handling
        try:
            sentences = sent_tokenize(text)
        except LookupError:
            nltk.download('punkt', quiet=True)
            sentences = sent_tokenize(text)
        
        return sentences
    
    def sentence_similarity(self, sent1, sent2):
        """Calculate similarity between two sentences"""
        # Convert sentences to word lists and remove stop words
        words1 = [w for w in sent1.split() if w not in self.stop_words]
        words2 = [w for w in sent2.split() if w not in self.stop_words]
        
        # Create word frequency vectors
        all_words = list(set(words1 + words2))
        vector1 = [0] * len(all_words)
        vector2 = [0] * len(all_words)
        
        # Fill vectors
        for w in words1:
            if w in all_words:
                vector1[all_words.index(w)] += 1
                
        for w in words2:
            if w in all_words:
                vector2[all_words.index(w)] += 1
        
        # Handle empty vectors
        if sum(vector1) == 0 or sum(vector2) == 0:
            return 0.0
        
        # Calculate cosine similarity
        return 1 - cosine_distance(vector1, vector2)
    
    def build_similarity_matrix(self, sentences):
        """Build similarity matrix for all sentences"""
        # Create empty similarity matrix
        similarity_matrix = np.zeros((len(sentences), len(sentences)))
        
        # Fill similarity matrix
        for i in range(len(sentences)):
            for j in range(len(sentences)):
                if i != j:
                    similarity_matrix[i][j] = self.sentence_similarity(
                        sentences[i], sentences[j])
        
        return similarity_matrix
    
    def generate_summary(self, text, num_sentences=3, max_words=100):
        """Generate summary by extracting most important sentences with length control
        
        Args:
            text: The text to summarize
            num_sentences: Maximum number of sentences to include
            max_words: Maximum number of words in the summary
        """
        if not text or len(text) < 100:  # Don't summarize very short texts
            return text
            
        # Preprocess text
        sentences = self.preprocess_text(text)
        
        # If there are fewer sentences than requested, return the original text
        if len(sentences) <= num_sentences:
            return text
            
        # Build similarity matrix
        similarity_matrix = self.build_similarity_matrix(sentences)
        
        # Calculate sentence scores using PageRank-like algorithm
        sentence_scores = np.array([sum(row) for row in similarity_matrix])
        
        # Enhance scoring with position and length factors
        for i, score in enumerate(sentence_scores):
            # Boost importance of early sentences (introduction)
            position_factor = 1.0 if i < len(sentences) // 4 else 0.8
            
            # Penalize very short or very long sentences
            words_count = len(sentences[i].split())
            if words_count < 5:
                length_factor = 0.7  # Penalize very short sentences
            elif words_count > 30:
                length_factor = 0.8  # Penalize very long sentences
            else:
                length_factor = 1.0
                
            # Apply factors
            sentence_scores[i] = score * position_factor * length_factor
        
        # Get indices of top sentences
        ranked_indices = np.argsort(sentence_scores)[::-1]
        
        # Extract original sentences
        try:
            original_sentences = sent_tokenize(text)
        except LookupError:
            nltk.download('punkt', quiet=True)
            original_sentences = sent_tokenize(text)
        
        # Build summary with word count constraint
        summary_sentences = []
        word_count = 0
        
        for idx in ranked_indices:
            if len(summary_sentences) >= num_sentences:
                break
                
            # Skip sentences that are too similar to already selected ones
            if self._is_redundant(original_sentences[idx], summary_sentences):
                continue
                
            sentence = original_sentences[idx]
            sentence_word_count = len(sentence.split())
            
            # Check if adding this sentence would exceed the word limit
            if word_count + sentence_word_count > max_words:
                # If we haven't added any sentences yet, add this one anyway
                if not summary_sentences:
                    summary_sentences.append(sentence)
                break
                
            summary_sentences.append(sentence)
            word_count += sentence_word_count
        
        # Sort sentences by their original order for better readability
        summary_indices = [original_sentences.index(sent) for sent in summary_sentences]
        summary_sentences = [s for _, s in sorted(zip(summary_indices, summary_sentences))]
        
        # Compress sentences to make them cleaner
        compressed_sentences = [self._compress_sentence(s) for s in summary_sentences]
        
        return ' '.join(compressed_sentences)
    
    def _is_redundant(self, new_sentence, selected_sentences, similarity_threshold=0.5):
        """Check if a sentence is too similar to any already selected sentences"""
        if not selected_sentences:
            return False
            
        for selected in selected_sentences:
            similarity = self.sentence_similarity(new_sentence, selected)
            if similarity > similarity_threshold:
                return True
                
        return False
        
    def _compress_sentence(self, sentence):
        """Compress a sentence by removing less important parts"""
        words = sentence.split()
        
        # Don't compress very short sentences
        if len(words) < 10:
            return sentence
            
        # Remove certain phrases and words that are often redundant
        redundant_phrases = [
            "in other words", "as a matter of fact", "at the present time",
            "due to the fact that", "for the purpose of", "in order to",
            "in the event that", "it should be noted that", "the fact that"
        ]
        
        for phrase in redundant_phrases:
            sentence = sentence.replace(phrase, "")
            
        # Remove parenthetical expressions (text in parentheses)
        sentence = re.sub(r'\([^)]*\)', '', sentence)
        
        # Clean up any double spaces
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        
        return sentence
    
    def extract_keywords(self, text, num_keywords=5):
        """Extract key terms from text"""
        # Clean text and tokenize
        text = text.lower()
        text = ''.join([c for c in text if c not in self.punctuation])
        words = text.split()
        
        # Remove stop words
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Count word frequencies
        word_freq = Counter(words)
        
        # Get most common words
        keywords = [word for word, _ in word_freq.most_common(num_keywords)]
        
        return keywords
    
    def summarize_articles(self, articles, query, max_length=500):
        """Create a comprehensive summary from multiple articles"""
        try:
            # Combine all article content
            all_text = ""
            for article in articles[:5]:  # Use top 5 articles for summary
                title = article.get('title', '')
                snippet = article.get('snippet', '')
                all_text += f"{title}. {snippet} "
            
            # Generate summary
            if len(all_text) > 100:
                # Use improved summary with word limit
                summary = self.generate_summary(all_text, num_sentences=5, max_words=80)
                
                # Extract keywords
                keywords = self.extract_keywords(all_text)
                
                # Format the summary concisely
                formatted_summary = f"Key developments on '{query}':\n\n"
                
                # Add the summary
                formatted_summary += f"{summary}\n\n"
                
                # Add key terms (limit to fewer terms)
                if keywords:
                    formatted_summary += f"Key terms: {', '.join(keywords[:3])}\n"
                
                return formatted_summary
            else:
                return f"Not enough content to generate a meaningful summary about '{query}'."
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fall back to a simple summary when errors occur
            return self.generate_simple_summary(articles, query)
    
    def generate_simple_summary(self, articles, query):
        """Generate a simple summary when NLP methods fail"""
        try:
            summary = f"Recent news about '{query}' includes:\n\n"
            
            # Extract a few bullet points from article titles
            for i, article in enumerate(articles[:3]):
                title = article.get('title', '')
                source = article.get('source', 'Unknown Source')
                
                if title:
                    summary += f"• {title} ({source})\n"
            
            return summary
        except Exception:
            return f"Found multiple news articles about '{query}'. Please check the details below."