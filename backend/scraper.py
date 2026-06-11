import random
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import Post, SessionLocal, init_db
import nlp_engine

# Realistic simulated post pools
SIMULATED_PROMPTS = [
    # Jalandhar / regional office issues (very realistic for Punjab/Jalandhar context)
    {
        "platform": "twitter",
        "username": "Gurpreet Singh",
        "user_handle": "@gurpreet_jalandhar",
        "content": "Jalandhar PSK is completely booked out. Tried booking a Tatkal slot at 10 AM, but the server crashed in 2 seconds. Extremely frustrating! #JalandharPassport #Tatkal",
        "region": "India",
        "language": "english",
        "likes": 45, "shares": 12, "comments": 8
    },
    {
        "platform": "twitter",
        "username": "Gurpreet Singh",
        "user_handle": "@gurpreet_jalandhar",
        "content": "Jalandhar PSK is completely booked out. Tried booking a Tatkal slot at 10 AM, but the server crashed in 2 seconds. Extremely frustrating! #JalandharPassport #Tatkal", # Exact duplicate for clustering
        "region": "India",
        "language": "english",
        "likes": 2, "shares": 0, "comments": 0
    },
    {
        "platform": "facebook",
        "username": "Amanpreet Kaur",
        "user_handle": "aman.kaur.92",
        "content": "Sharing my experience of passport renewal at Regional Passport Office Jalandhar. The staff was helpful but the queues are long. Make sure to carry original birth certificate and 10th certificate! It took me about 3 hours in total.",
        "region": "India",
        "language": "english",
        "likes": 89, "shares": 15, "comments": 24
    },
    {
        "platform": "instagram",
        "username": "Priya Sharma",
        "user_handle": "@priya_travels",
        "content": "Finally got my passport renewed! ✈️ Destination unknown yet. The process was super smooth with Tatkal - applied on Monday, received it today on Thursday! Highly recommend using Tatkal if you are in a rush. 🛂💼 #travelgram #passport #india #happy",
        "region": "India",
        "language": "english",
        "likes": 230, "shares": 5, "comments": 14
    },
    
    # Government Announcements / News (Clustering Candidates)
    {
        "platform": "linkedin",
        "username": "Zebvo News",
        "user_handle": "zebvo-newswire",
        "content": "MEA Announcement: The Ministry of External Affairs has launched a new DigiLocker integration for passport applications. Applicants can now share their paperless documents securely, cutting verification times by 50% and reducing dependencies on physical verification counters.",
        "region": "Global",
        "language": "english",
        "likes": 420, "shares": 85, "comments": 12
    },
    {
        "platform": "twitter",
        "username": "Global Travel News",
        "user_handle": "@global_travel_news",
        "content": "MEA Announcement: The Ministry of External Affairs has launched a new DigiLocker integration for passport applications. Applicants can now share their paperless documents securely, cutting verification times by 50% and reducing dependencies on physical verification counters.", # Duplicate
        "region": "Global",
        "language": "english",
        "likes": 120, "shares": 35, "comments": 4
    },
    {
        "platform": "facebook",
        "username": "India Passport Services Info",
        "user_handle": "passport.services.info",
        "content": "MEA Announcement: The Ministry of External Affairs has launched a new DigiLocker integration for passport applications. Applicants can now share their paperless documents securely, cutting verification times by 50% and reducing dependencies on physical verification counters.", # Duplicate
        "region": "India",
        "language": "english",
        "likes": 65, "shares": 40, "comments": 18
    },

    # Visa/Travel Issues
    {
        "platform": "twitter",
        "username": "Rajesh Kumar",
        "user_handle": "@rajesh_travels",
        "content": "Applied for a Schengen visa but my passport is stuck at the embassy for over 4 weeks now. Flights are booked for next week. Anyone else facing massive delays with European embassies? #VisaDelay #SchengenVisa",
        "region": "India",
        "language": "english",
        "likes": 56, "shares": 19, "comments": 22
    },
    {
        "platform": "tiktok",
        "username": "Sarah Jenkins",
        "user_handle": "@sarah_hacks",
        "content": "Urgent travel hack! Do NOT travel with a passport that expires in less than 6 months. I got deported from Bali because of this rule! Always check validity before booking. Learn from my mistake 😭 #travelhack #balitrip #passportrules",
        "region": "USA",
        "language": "english",
        "likes": 15400, "shares": 3200, "comments": 450
    },
    {
        "platform": "youtube",
        "username": "Technical Travel",
        "user_handle": "technical_travel_channel",
        "content": "How to Apply for Passport Online 2026 - Step by Step Guide. In this video, we discuss fresh applications, renewals, documents checklist, Tatkal booking rules, and passport office appointments. Watch the full video to avoid common mistakes that lead to police verification rejection.",
        "region": "India",
        "language": "english",
        "likes": 4500, "shares": 1200, "comments": 350
    },

    # Scams/Fraud Alerts
    {
        "platform": "facebook",
        "username": "Jalandhar Alerts",
        "user_handle": "jalandhar.alerts",
        "content": "WARNING: Several fake websites resembling the official Passport Seva portal are charging innocent citizens 3x the normal fee. Please check the URL! The ONLY official government site is passportindia.gov.in. Do not fall for online agent scams!",
        "region": "India",
        "language": "english",
        "likes": 320, "shares": 290, "comments": 42
    },
    {
        "platform": "twitter",
        "username": "Cyber Cop India",
        "user_handle": "@cyber_cop_ind",
        "content": "WARNING: Several fake websites resembling the official Passport Seva portal are charging innocent citizens 3x the normal fee. Please check the URL! The ONLY official government site is passportindia.gov.in. Do not fall for online agent scams!", # Duplicate
        "region": "India",
        "language": "english",
        "likes": 1200, "shares": 850, "comments": 94
    },
    {
        "platform": "linkedin",
        "username": "Amit Mehra",
        "user_handle": "amit-mehra-security",
        "content": "Beware of agents near Passport Offices promising quick appointments for money. A friend paid 5000 INR to an agent in Jalandhar who vanished after taking the passport. Follow the government process, it is safer.",
        "region": "India",
        "language": "english",
        "likes": 180, "shares": 22, "comments": 19
    },

    # Multilingual Posts
    {
        "platform": "twitter",
        "username": "Sonia Verma",
        "user_handle": "@sonia_v",
        "content": "पासपोर्ट रिन्यू कराने का अनुभव बहुत अच्छा रहा। जालंधर कार्यालय में सेवाएं काफी सुधर गई हैं। केवल २ दिन में पुलिस वेरिफिकेशन भी हो गया। धन्यवाद विदेश मंत्रालय!",
        "region": "India",
        "language": "hindi", # Hindi post
        "likes": 34, "shares": 4, "comments": 3
    },
    {
        "platform": "facebook",
        "username": "Jagmeet Singh",
        "user_handle": "jagmeet.singh.pb",
        "content": "ਜਲੰਧਰ ਪਾਸਪੋਰਟ ਦਫ਼ਤਰ ਵਿੱਚ ਅਪੁਆਇੰਟਮੈਂਟ ਲੈਣਾ ਬਹੁਤ ਮੁਸ਼ਕਲ ਹੋ ਗਿਆ ਹੈ। ਸਲਾਟ ਜਲਦੀ ਖਤਮ ਹੋ ਜਾਂਦੇ ਹਨ। ਕੋਈ ਹੱਲ ਦੱਸੋ?",
        "region": "India",
        "language": "punjabi", # Punjabi post
        "likes": 56, "shares": 18, "comments": 42
    },
    {
        "platform": "instagram",
        "username": "Carlos Travel",
        "user_handle": "@carlos_viajes",
        "content": "¡Por fin tengo mi nuevo pasaporte listo para viajar! El trámite de renovación en Madrid fue rápido, solo 15 minutos en la oficina. Próximo destino: Sudamérica. ✈️🌍 #pasaporte #viajes #aventura #españa",
        "region": "Spain",
        "language": "spanish", # Spanish post
        "likes": 189, "shares": 3, "comments": 9
    },
    {
        "platform": "twitter",
        "username": "Yuki Tanaka",
        "user_handle": "@yuki_travel",
        "content": "日本のパスポートが更新されました！世界最強のパスポート、新しいデザインは葛飾北斎の富嶽三十六景が描かれていて本当に美しいです。早く海外旅行に行きたい。✈️🇯🇵 #パスポート #旅行 #日本",
        "region": "Japan",
        "language": "japanese", # Japanese post
        "likes": 540, "shares": 45, "comments": 28
    },

    # Gibberish / Spam Posts (Will be filtered out or flagged as is_gibberish=True)
    {
        "platform": "twitter",
        "username": "SpamBot 4000",
        "user_handle": "@spam_bot_4000",
        "content": "asdfghjklqwertyuiop passport scam 100% free bitcoin click here now!!! www.crypto-scam-link-fake.com/free",
        "region": "Global",
        "language": "english",
        "likes": 0, "shares": 0, "comments": 0
    },
    {
        "platform": "facebook",
        "username": "Keyboard Masher",
        "user_handle": "kb.mash",
        "content": "Passport applications are zxczxczxczxc qweqweqweqwe ghjghjghjghj 123123123!!!!!!!!!",
        "region": "Global",
        "language": "english",
        "likes": 1, "shares": 0, "comments": 0
    },
    {
        "platform": "twitter",
        "username": "Link Spammer",
        "user_handle": "@link_spammer",
        "content": "!!! $$$ %%% passport renewal appointments slots visa tatkal booking agent https://t.co/fake_shortlink",
        "region": "India",
        "language": "english",
        "likes": 0, "shares": 0, "comments": 0
    }
]

def scrape_reddit() -> list:
    """
    Scrapes real-time posts from Reddit using public search JSON endpoints.
    Fetches posts mentioning 'passport' created recently.
    """
    posts = []
    # Search for "passport" sorting by newest
    url = "https://www.reddit.com/search.json?q=passport&sort=new&limit=25"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            children = data.get("data", {}).get("children", [])
            for child in children:
                post_data = child.get("data", {})
                title = post_data.get("title", "")
                selftext = post_data.get("selftext", "")
                content = f"{title}\n{selftext}".strip()
                
                # Check for 24-hour limit
                created_utc = post_data.get("created_utc", 0)
                timestamp = datetime.utcfromtimestamp(created_utc)
                if datetime.utcnow() - timestamp > timedelta(hours=24):
                    continue
                    
                post_id = f"reddit_{post_data.get('id')}"
                username = post_data.get("author", "anonymous")
                user_handle = f"/u/{username}"
                likes = post_data.get("ups", 0)
                comments = post_data.get("num_comments", 0)
                
                posts.append({
                    "platform": "reddit",
                    "post_id": post_id,
                    "username": username,
                    "user_handle": user_handle,
                    "content": content,
                    "timestamp": timestamp,
                    "language": "english", # Reddit search query is English
                    "region": "Global",
                    "likes": likes,
                    "shares": 0,
                    "comments": comments
                })
        else:
            print(f"Reddit scraper HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"Reddit scraper Exception: {e}")
        
    return posts

def generate_simulated_posts(count: int = 15) -> list:
    """Generates a list of simulated posts with random times within the last 24 hours."""
    posts = []
    # Mix and match from SIMULATED_PROMPTS
    samples = random.sample(SIMULATED_PROMPTS, min(count, len(SIMULATED_PROMPTS)))
    
    for i, sample in enumerate(samples):
        # Generate random timestamp in the last 24 hours
        minutes_ago = random.randint(10, 1440)
        timestamp = datetime.utcnow() - timedelta(minutes=minutes_ago)
        
        post_id = f"sim_{sample['platform']}_{int(time.time())}_{i}"
        
        posts.append({
            "platform": sample["platform"],
            "post_id": post_id,
            "username": sample["username"],
            "user_handle": sample["user_handle"],
            "content": sample["content"],
            "timestamp": timestamp,
            "language": sample["language"],
            "region": sample["region"],
            "likes": sample["likes"],
            "shares": sample["shares"],
            "comments": sample["comments"]
        })
        
    return posts

def process_and_save_posts(db: Session, raw_posts: list):
    """
    Applies the NLP engine processing pipeline to raw posts, clusters them,
    and saves them to the SQLite database.
    """
    processed_posts = []
    
    # Step 1: Pre-process each post individually
    for p in raw_posts:
        # Check if already exists in DB to prevent duplicates
        existing = db.query(Post).filter(Post.post_id == p["post_id"]).first()
        if existing:
            continue
            
        # Gibberish filtering
        is_spambot = nlp_engine.is_gibberish(p["content"])
        
        # If it is gibberish, we flag it. (The user wants it either deleted or filtered out.
        # Storing it with an is_gibberish=True flag is excellent, as it allows us to audit/show spam filters!)
        # Let's run other NLP only if it's NOT gibberish
        if not is_spambot:
            # If the post is in Hindi, Punjabi, or Spanish, we translate it to English first for NLP!
            content_for_nlp = p["content"]
            if p["language"] != "english":
                try:
                    content_for_nlp = nlp_engine.translate_text(p["content"], "english")
                except Exception:
                    pass
            
            category = nlp_engine.classify_category(content_for_nlp)
            sentiment = nlp_engine.analyze_sentiment(content_for_nlp)
            summary = nlp_engine.generate_summary(content_for_nlp)
        else:
            category = "Spam/Gibberish"
            sentiment = "Neutral"
            summary = "Gibberish content filtered."

        # Setup base dictionary
        db_post = Post(
            platform=p["platform"],
            post_id=p["post_id"],
            username=p["username"],
            user_handle=p["user_handle"],
            content=p["content"],
            timestamp=p["timestamp"],
            language=p["language"],
            region=p["region"],
            likes=p["likes"],
            shares=p["shares"],
            comments=p["comments"],
            sentiment=sentiment,
            category=category,
            summary=summary,
            is_gibberish=is_spambot,
            translations_json="{}" # Empty initially, lazy-loaded/filled upon request
        )
        processed_posts.append(db_post)
        
    if not processed_posts:
        # Re-run clustering on all active non-gibberish database posts from the last 24 hours
        # This keeps the cluster associations fresh when new posts arrive!
        run_clustering_on_db(db)
        return
        
    # Bulk save new posts
    db.add_all(processed_posts)
    db.commit()
    
    # Run clustering on all posts from the last 24 hours
    run_clustering_on_db(db)

def run_clustering_on_db(db: Session):
    """Fetches all non-gibberish posts from the last 24 hours and updates their cluster IDs."""
    time_limit = datetime.utcnow() - timedelta(hours=24)
    active_posts = db.query(Post).filter(
        Post.timestamp >= time_limit,
        Post.is_gibberish == False
    ).all()
    
    if len(active_posts) < 2:
        return
        
    # Format active posts into dictionaries for the NLP clusterer
    posts_data = []
    for p in active_posts:
        # We cluster based on the English version of the text if it is translated!
        # If language is not English, let's look up translated content or use original
        # For clustering, translating to English makes cross-lingual duplicates group together! This is incredibly smart!
        content_to_use = p.content
        if p.language != "english":
            import json
            trans_dict = json.loads(p.translations_json or "{}")
            if "english" in trans_dict:
                content_to_use = trans_dict["english"]
            else:
                try:
                    # Translate on the fly for clustering comparison
                    translated = nlp_engine.translate_text(p.content, "english")
                    trans_dict["english"] = translated
                    p.translations_json = json.dumps(trans_dict)
                    content_to_use = translated
                except Exception:
                    pass
                    
        posts_data.append({
            "id": p.id,
            "content": content_to_use
        })
        
    # Cluster posts
    clustered = nlp_engine.cluster_posts(posts_data, similarity_threshold=0.68)
    
    # Update cluster IDs in database
    for item in clustered:
        db_p = db.query(Post).filter(Post.id == item["id"]).first()
        if db_p:
            db_p.cluster_id = item["cluster_id"]
            
    db.commit()

def run_scraper_cycle():
    """Triggers one complete scraping and processing cycle."""
    db = SessionLocal()
    try:
        print("Scraper cycle triggered...")
        # 1. Fetch from Reddit
        reddit_posts = scrape_reddit()
        print(f"Scraped {len(reddit_posts)} real posts from Reddit.")
        
        # 2. Fetch from Simulated Engine
        simulated_posts = generate_simulated_posts(count=15)
        print(f"Generated {len(simulated_posts)} simulated posts.")
        
        # 3. Combine and process
        all_posts = reddit_posts + simulated_posts
        process_and_save_posts(db, all_posts)
        print("Scraper cycle completed.")
    except Exception as e:
        print(f"Error in scraper cycle: {e}")
    finally:
        db.close()
