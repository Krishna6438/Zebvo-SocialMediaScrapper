import io
import time
import threading
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from database import init_db, get_db, SessionLocal, Post
import nlp_engine
import scraper

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    init_db()
    
    # Pre-populate if empty
    db = SessionLocal()
    try:
        if db.query(Post).count() == 0:
            print("Database is empty. Running initial scraping cycle...")
            scraper.run_scraper_cycle()
    finally:
        db.close()
        
    # Start periodic scraper in background thread (every 10 minutes)
    def periodic_scraper():
        while True:
            time.sleep(600)
            try:
                scraper.run_scraper_cycle()
            except Exception as e:
                print(f"Error in background periodic scraper: {e}")
                
    t = threading.Thread(target=periodic_scraper, daemon=True)
    t.start()
    yield

app = FastAPI(
    title="Zebvo Passport Dashboard API",
    description="Backend API for filtering, translating, and analyzing passport-related social media posts.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import RedirectResponse

@app.get("/")
def redirect_to_frontend():
    """Redirects root requests on port 8000 to the React dashboard at port 5173."""
    return RedirectResponse(url="http://localhost:5173")

def get_filtered_posts_query(
    db: Session,
    platform: Optional[str] = None,
    region: Optional[str] = None,
    language: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    cluster_id: Optional[int] = None,
    is_gibberish: bool = False
):
    """Applies common filters and returns a SQLAlchemy query object."""
    # Only get posts from the last 24 hours
    time_limit = datetime.utcnow() - timedelta(hours=24)
    query = db.query(Post).filter(Post.timestamp >= time_limit)
    
    # Apply filtering options
    query = query.filter(Post.is_gibberish == is_gibberish)
    
    if platform:
        query = query.filter(Post.platform == platform.lower())
    if region:
        query = query.filter(Post.region == region)
    if language:
        query = query.filter(Post.language == language.lower())
    if category:
        query = query.filter(Post.category == category)
    if sentiment:
        query = query.filter(Post.sentiment == sentiment)
    if cluster_id is not None:
        query = query.filter(Post.cluster_id == cluster_id)
        
    # Full-text search across original text, summary, and cached translations
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            Post.content.ilike(search_filter) |
            Post.summary.ilike(search_filter) |
            Post.translations_json.ilike(search_filter)
        )
        
    return query

@app.get("/api/posts")
def get_posts(
    platform: Optional[str] = None,
    region: Optional[str] = None,
    language: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    cluster_id: Optional[int] = None,
    is_gibberish: bool = False,
    sort_by: str = "time", # time or engagement
    sort_order: str = "desc", # desc or asc
    db: Session = Depends(get_db)
):
    """Retrieves posts based on filter parameters, sorted accordingly."""
    query = get_filtered_posts_query(
        db, platform, region, language, category, sentiment, search, cluster_id, is_gibberish
    )
    
    # Determine sorting columns
    if sort_by == "engagement":
        sort_col = (Post.likes + Post.shares + Post.comments)
    else:
        sort_col = Post.timestamp
        
    # Apply sorting order
    if sort_order == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))
        
    posts = query.all()
    return [p.to_dict() for p in posts]

@app.get("/api/posts/{post_id}/translate")
def translate_post(post_id: int, lang: str, db: Session = Depends(get_db)):
    """Translates a specific post's content and returns it. Caches translation in DB."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    lang = lang.lower()
    if lang not in nlp_engine.LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
        
    # Load existing translations
    translations = json.loads(post.translations_json or "{}")
    
    # Return from cache if already translated
    if lang in translations:
        return {"translated_text": translations[lang]}
        
    # If translating a non-English post to a non-English target, we translate the original content.
    # deep-translator handles auto source language detection nicely.
    try:
        translated_text = nlp_engine.translate_text(post.content, lang)
        
        # Save back to cache
        translations[lang] = translated_text
        post.translations_json = json.dumps(translations)
        db.commit()
        
        return {"translated_text": translated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/api/scrape/trigger")
def trigger_scrape(db: Session = Depends(get_db)):
    """Manually triggers the scraping cycle and returns the count of posts."""
    scraper.run_scraper_cycle()
    time_limit = datetime.utcnow() - timedelta(hours=24)
    total_posts = db.query(Post).filter(Post.timestamp >= time_limit, Post.is_gibberish == False).count()
    return {"message": "Scraping completed successfully", "active_posts_count": total_posts}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Returns aggregated stats for active dashboard graphs."""
    time_limit = datetime.utcnow() - timedelta(hours=24)
    active_filter = (Post.timestamp >= time_limit) & (Post.is_gibberish == False)
    
    # Platform counts
    platform_stats = db.query(Post.platform, func.count(Post.id)).filter(active_filter).group_by(Post.platform).all()
    platforms = {p: count for p, count in platform_stats}
    
    # Category counts
    category_stats = db.query(Post.category, func.count(Post.id)).filter(active_filter).group_by(Post.category).all()
    categories = {c: count for c, count in category_stats}
    
    # Sentiment counts
    sentiment_stats = db.query(Post.sentiment, func.count(Post.id)).filter(active_filter).group_by(Post.sentiment).all()
    sentiments = {s: count for s, count in sentiment_stats}
    
    # Total posts vs Gibberish filtered
    total_posts = db.query(Post).filter(Post.timestamp >= time_limit).count()
    gibberish_count = db.query(Post).filter(Post.timestamp >= time_limit, Post.is_gibberish == True).count()
    
    return {
        "platforms": platforms,
        "categories": categories,
        "sentiments": sentiments,
        "total_active": total_posts - gibberish_count,
        "gibberish_filtered": gibberish_count
    }

@app.get("/api/export/csv")
def export_csv(
    platform: Optional[str] = None,
    region: Optional[str] = None,
    language: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    cluster_id: Optional[int] = None,
    is_gibberish: bool = False,
    db: Session = Depends(get_db)
):
    """Exports filtered posts to a CSV file."""
    import pandas as pd
    query = get_filtered_posts_query(
        db, platform, region, language, category, sentiment, search, cluster_id, is_gibberish
    )
    posts = query.all()
    
    # Convert to DataFrame
    data = []
    for p in posts:
        data.append({
            "ID": p.id,
            "Platform": p.platform.upper(),
            "Handle": p.user_handle,
            "Username": p.username,
            "Timestamp": p.timestamp.strftime("%Y-%m-%d %H:%M:%S") if p.timestamp else "",
            "Region": p.region,
            "Language": p.language,
            "Category": p.category,
            "Sentiment": p.sentiment,
            "Likes": p.likes,
            "Shares": p.shares,
            "Comments": p.comments,
            "Content": p.content,
            "Summary": p.summary
        })
        
    df = pd.DataFrame(data)
    
    # Create dynamic filename
    filename = f"passport_posts_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Write to a string buffer
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response

@app.get("/api/export/pdf")
def export_pdf(
    platform: Optional[str] = None,
    region: Optional[str] = None,
    language: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    cluster_id: Optional[int] = None,
    is_gibberish: bool = False,
    db: Session = Depends(get_db)
):
    """Exports a stylized PDF report of filtered posts using ReportLab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    query = get_filtered_posts_query(
        db, platform, region, language, category, sentiment, search, cluster_id, is_gibberish
    )
    posts = query.all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=20
    )
    
    body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#334155'),
        leading=10
    )
    
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        textColor=colors.white
    )
    
    elements = []
    
    # Title & Metadata
    elements.append(Paragraph("Zebvo Passport Scraping Report", title_style))
    elements.append(Paragraph(
        f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Total Posts: {len(posts)}<br/>"
        f"Filters applied: Platform={platform or 'All'}, Category={category or 'All'}, Sentiment={sentiment or 'All'}, Search={search or 'None'}",
        subtitle_style
    ))
    
    # Table headers
    data = [[
        Paragraph("Platform", header_style),
        Paragraph("User/Handle", header_style),
        Paragraph("Category", header_style),
        Paragraph("Sentiment", header_style),
        Paragraph("Summary (~30 words)", header_style),
        Paragraph("Engagement", header_style)
    ]]
    
    # Populate Table rows
    for p in posts:
        engagement_str = f"L: {p.likes} | S: {p.shares} | C: {p.comments}"
        data.append([
            Paragraph(p.platform.upper(), body_style),
            Paragraph(f"{p.username}<br/>{p.user_handle}", body_style),
            Paragraph(p.category, body_style),
            Paragraph(p.sentiment, body_style),
            Paragraph(p.summary or p.content[:100], body_style),
            Paragraph(engagement_str, body_style)
        ])
        
    # Create reportlab table. Column widths total to 540 pt (width of letter page margins 612 - 72)
    col_widths = [55, 95, 75, 55, 180, 80]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Apply table styles
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')), # Dark slate header
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    elements.append(table)
    
    # Build document
    doc.build(elements)
    
    buffer.seek(0)
    
    filename = f"passport_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    response = StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response
