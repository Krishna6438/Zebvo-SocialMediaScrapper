import re
import math
import collections
from typing import List, Dict, Any, Tuple
from deep_translator import GoogleTranslator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np

# Download NLTK resources with a robust fallback
import nltk
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception:
        pass

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords', quiet=True)
    except Exception:
        pass

from nltk.corpus import stopwords

# Language mapping for translation
LANGUAGES = {
    "english": "en",
    "hindi": "hi",
    "punjabi": "pa",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "arabic": "ar",
    "chinese": "zh-CN",
    "russian": "ru",
    "japanese": "ja"
}

# Categories and keywords for rule-based classification
CATEGORIES = {
    "Application": [
        "apply", "application", "form", "documents", "birth certificate", "fees", "checklist", 
        "how to apply", "photo requirements", "signature", "minor passport", "fresh passport", 
        "documents required", "annexure", "identity certificate", "verification roll"
    ],
    "Renewal": [
        "renew", "renewal", "expired", "reissue", "expired passport", "change address", "validity", 
        "10 years", "damage passport", "lost passport", "renewing", "exhausted pages"
    ],
    "Appointments": [
        "slot", "slots", "appointment", "booking", "calendar", "rescheduling", "dates", "psk", "popsk", 
        "jalandhar psk", "no slots", "booked out", "opening time", "appointment date", "reschedule"
    ],
    "Tatkal": [
        "tatkaal", "tatkal", "urgent", "emergency", "fast track", "out-of-turn", "dispatch time", 
        "tatkal fees", "urgent passport", "tatkal application"
    ],
    "Visa": [
        "visa", "stamp", "travel visa", "schengen", "us visa", "visa fee", "tourist visa", 
        "student visa", "work permit", "interview", "stamping", "h1b", "visitor visa"
    ],
    "Travel Issues": [
        "airport", "customs", "immigration", "boarding", "flight", "border", "banned", "travel advisory", 
        "deport", "entry denied", "boarding pass", "transit", "airline", "security check", "stuck"
    ],
    "Government Announcements": [
        "mea", "ministry", "minister", "official announcement", "press release", "passport office notification", 
        "rule change", "government circular", "fee hike", "digital locker", "digilocker", "passport seva", 
        "external affairs", "government portal", "helpline"
    ],
    "Scams/Fraud": [
        "fake website", "agent scam", "fraud", "extra money", "bribe", "phishing", "scammer", "duplicate site", 
        "warning", "stay safe", "fake agent", "charging extra", "scammed", "touts", "alert"
    ],
    "News": [
        "reported", "newswire", "journalism", "official report", "newspaper", "press", "coverage", 
        "update", "daily news", "tribune", "times of india", "hindustan times", "sources say"
    ],
    "Personal Experiences": [
        "my passport", "got my", "received today", "happy", "journey", "finally", "took only", 
        "experience", "sharing my", "story", "helpful staff", "bad service", "my experience", 
        "staff behaviour", "waiting time", "i applied"
    ]
}

# Positive and Negative lexicons for Sentiment Analysis
POSITIVE_WORDS = {
    "good", "great", "excellent", "happy", "fast", "smooth", "helpful", "friendly", "satisfied",
    "awesome", "love", "thanks", "thank", "appreciated", "easy", "quickly", "efficient", "perfect",
    "resolved", "success", "successful", "care", "polite", "glad", "best", "convenient", "wonderful"
}

NEGATIVE_WORDS = {
    "bad", "terrible", "worst", "slow", "delayed", "delay", "waiting", "wait", "painful", "frustrating",
    "frustrated", "scam", "fraud", "fake", "angry", "rude", "poor", "hate", "useless", "broken",
    "error", "failed", "fail", "rejected", "rejection", "stuck", "horrible", "annoying", "unhelpful",
    "bribe", "extra money", "charging", "scammed", "expensive", "waste", "problem", "issue", "difficult"
}

def clean_text(text: str) -> str:
    """Basic text cleanup."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\.\S+', '', text) # remove URLs
    text = re.sub(r'[^a-zA-Z\s]', '', text) # remove non-alphabetic characters
    text = re.sub(r'\s+', ' ', text).strip() # remove extra whitespace
    return text

def is_gibberish(text: str) -> bool:
    """
    Detects if a post is spam, bot activity, or gibberish.
    Uses character repetition, vowel ratios, and word patterns.
    """
    if not text or len(text.strip()) < 8:
        return True
    
    # 1. Check for extreme character repetition (e.g. "aaaaa" or "asdfasdf")
    cleaned = clean_text(text)
    if not cleaned:
        return True
    
    # Check max consecutive identical characters
    max_consec = 1
    current_consec = 1
    for i in range(1, len(cleaned)):
        if cleaned[i] == cleaned[i-1]:
            current_consec += 1
            max_consec = max(max_consec, current_consec)
        else:
            current_consec = 1
    if max_consec > 5:
        return True
        
    # 2. Vowel ratio check (only for primarily English/Latin texts)
    # Check if text contains latin characters
    if re.search(r'[a-zA-Z]', text):
        vowels = len(re.findall(r'[aeiouAEIOU]', cleaned))
        total_letters = len(re.findall(r'[a-zA-Z]', cleaned))
        if total_letters > 0:
            vowel_ratio = vowels / total_letters
            # English usually has 30-50% vowels. Less than 10% or more than 80% is likely gibberish
            if vowel_ratio < 0.10 or vowel_ratio > 0.80:
                return True
                
    # 3. Word length and token checks
    words = cleaned.split()
    if not words:
        return True
        
    # Average word length: English average is ~5. Exceptionally long words or all very short words is suspicious
    avg_word_length = sum(len(w) for w in words) / len(words)
    if avg_word_length > 18 or avg_word_length < 2.5:
        return True
        
    # Check if a single word is exceptionally long (e.g., keyboard smash without spaces: "asdfghjklqwertyuiop")
    max_word_length = max(len(w) for w in words)
    if max_word_length > 25:
        return True
        
    # 4. Check for high density of special characters/numbers
    total_chars = len(text)
    special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', text))
    if total_chars > 0 and (special_chars / total_chars) > 0.45:
        return True
        
    # 5. Check if it's purely repetitive spam words
    word_counts = collections.Counter(words)
    if len(words) > 5:
        most_common_word, count = word_counts.most_common(1)[0]
        # If a single word makes up more than 50% of the text, it's likely spam
        if count / len(words) > 0.55:
            return True
            
    return False

def translate_text(text: str, target_lang: str) -> str:
    """Translates text into the target language using deep-translator."""
    if not text:
        return ""
    target_code = LANGUAGES.get(target_lang.lower())
    if not target_code:
        raise ValueError(f"Unsupported language: {target_lang}")
        
    if target_code == "en" and re.match(r'^[\x00-\x7F]+$', text):
        # Already English, no translation needed
        return text
        
    try:
        translated = GoogleTranslator(source='auto', target=target_code).translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def analyze_sentiment(text: str) -> str:
    """
    Performs lexicon-based sentiment analysis on the text.
    Returns: 'Positive', 'Neutral', or 'Negative'.
    """
    cleaned = clean_text(text)
    words = cleaned.split()
    
    pos_count = 0
    neg_count = 0
    
    for word in words:
        if word in POSITIVE_WORDS:
            pos_count += 1
        elif word in NEGATIVE_WORDS:
            neg_count += 1
            
    # Calculate score
    total = pos_count + neg_count
    if total == 0:
        return "Neutral"
        
    score = (pos_count - neg_count) / total
    
    if score > 0.15:
        return "Positive"
    elif score < -0.15:
        return "Negative"
    else:
        return "Neutral"

def classify_category(text: str) -> str:
    """
    Classifies the text into one of the 10 topical categories using keyword scoring.
    """
    cleaned = clean_text(text)
    scores = {category: 0 for category in CATEGORIES}
    
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            # Check for exact word/phrase boundary matching
            pattern = rf'\b{re.escape(kw)}\b'
            matches = len(re.findall(pattern, cleaned))
            scores[category] += matches * 2 # Standard matches
            
            # Check for partial matches in words (e.g. "renew" in "renewing")
            if matches == 0 and kw in cleaned:
                scores[category] += 1
                
    # Find category with maximum score
    max_score = -1
    best_category = None
    for category, score in scores.items():
        if score > max_score:
            max_score = score
            best_category = category
            
    # If no score, determine based on personal pronouns vs general text
    if max_score <= 0:
        first_person = len(re.findall(r'\b(i|my|me|we|us|our)\b', cleaned))
        if first_person > 0:
            return "Personal Experiences"
        else:
            return "News"
            
    return best_category

def generate_summary(text: str) -> str:
    """
    Generates a concise ~30-word summary using extractive Luhn-style frequency scoring.
    """
    if not text:
        return ""
        
    # Split text into sentences (handles basic punctuation splits)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 1 or len(text.split()) <= 35:
        return text
        
    # Clean text to calculate word frequencies
    cleaned = clean_text(text)
    words = cleaned.split()
    
    # Filter out English stopwords if nltk is loaded, else use inline list
    try:
        stop_words = set(stopwords.words('english'))
    except Exception:
        stop_words = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "for", "in", "on", "at", "by", "with", "this", "that", "it"}
        
    filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
    
    if not filtered_words:
        return sentences[0]
        
    word_freq = collections.Counter(filtered_words)
    max_freq = max(word_freq.values())
    
    # Normalize frequencies
    for word in word_freq:
        word_freq[word] = word_freq[word] / max_freq
        
    # Score sentences based on word frequencies
    sentence_scores = []
    for i, sent in enumerate(sentences):
        sent_cleaned = clean_text(sent)
        sent_words = sent_cleaned.split()
        if not sent_words:
            sentence_scores.append((0, i))
            continue
            
        score = sum(word_freq.get(w, 0) for w in sent_words)
        # Normalize score by sentence length (so long sentences don't dominate excessively)
        score = score / math.sqrt(len(sent_words)) if len(sent_words) > 0 else 0
        sentence_scores.append((score, i))
        
    # Sort sentences by score descending
    sentence_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Select top sentences until target word limit (~30 words) is met
    selected_indices = []
    current_word_count = 0
    
    # Always include the highest scoring sentence
    if sentence_scores:
        best_score, best_idx = sentence_scores[0]
        selected_indices.append(best_idx)
        current_word_count += len(sentences[best_idx].split())
        
        # Add next highest scoring sentences if they keep us near target limit
        for score, idx in sentence_scores[1:]:
            sent_len = len(sentences[idx].split())
            if current_word_count + sent_len <= 45:
                selected_indices.append(idx)
                current_word_count += sent_len
            elif current_word_count < 20: # Make sure summary isn't too short
                selected_indices.append(idx)
                current_word_count += sent_len
                break
            else:
                break
                
    # Sort selected sentences back to original text order
    selected_indices.sort()
    summary_sentences = [sentences[idx] for idx in selected_indices]
    summary = " ".join(summary_sentences)
    
    # Trim to ~30-35 words elegantly
    summary_words = summary.split()
    if len(summary_words) > 35:
        summary = " ".join(summary_words[:35]) + "..."
        
    return summary

def cluster_posts(posts: List[Dict[str, Any]], similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
    """
    Clusters the posts using TF-IDF and DBSCAN.
    Updates each post with a `cluster_id` (integer or None).
    """
    if not posts:
        return posts
        
    # Extract cleaned contents
    contents = [clean_text(post.get("content", "")) for post in posts]
    
    # If there are fewer than 2 posts, clustering is not applicable
    if len(posts) < 2:
        for post in posts:
            post["cluster_id"] = None
        return posts
        
    try:
        # Convert to TF-IDF matrix
        # Use sublinear TF scaling, character + word ngrams to be robust against slight changes
        vectorizer = TfidfVectorizer(
            min_df=1,
            stop_words='english',
            sublinear_tf=True,
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform(contents)
        
        # Calculate Cosine Distance matrix (Distance = 1 - Cosine Similarity)
        # Cosine distance will range from 0 (identical) to 1 (completely different)
        # DBSCAN expects a distance metric
        from sklearn.metrics.pairwise import cosine_distances
        dist_matrix = cosine_distances(tfidf_matrix)
        
        # eps parameter: maximum distance between two samples for one to be considered as in the neighborhood of the other.
        # Since eps is distance, eps = 1 - similarity_threshold.
        # Standard similarity_threshold = 0.7, so eps = 0.3. Let's make it eps = 0.35 to be slightly more flexible.
        eps = 1.0 - similarity_threshold
        
        # Run DBSCAN
        db = DBSCAN(eps=eps, min_samples=2, metric='precomputed')
        labels = db.fit_predict(dist_matrix)
        
        # Assign cluster ids
        for i, post in enumerate(posts):
            label = int(labels[i])
            # DBSCAN assigns -1 to noise (unclustered posts)
            if label == -1:
                post["cluster_id"] = None
            else:
                post["cluster_id"] = label + 1 # Convert to 1-based index for display
                
    except Exception as e:
        print(f"Clustering error: {e}")
        for post in posts:
            post["cluster_id"] = None
            
    return posts
