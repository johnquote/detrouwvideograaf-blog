"""
De Trouwvideograaf Blog Generator
==================================
Automatisch SEO artikelen genereren en publiceren voor trouwvideograaf.net

Gebruik:
  python main.py                    # Genereer volgende ongepubliceerde stad
  python main.py --stad kampen      # Genereer specifieke stad
  python main.py --lijst            # Toon alle steden en status
  python main.py --test             # Test zonder te publiceren (geen GitHub push)

Pipeline (Multi-Agent):
  1. Research   – lokale kennis verzamelen
  2. Outline    – SEO-geoptimaliseerde structuur
  3. Schrijf    – volledig artikel in Nederlands
  4. SEO-check  – meta title, description, keywords
  5. Kwaliteit  – CORE-EEAT benchmark check
  6. Publiceer  – HTML opslaan + GitHub push
  7. Email      – notificatie sturen

Gebaseerd op:
  - Multi-Agent-SEO-Blog-Generator (pipeline structuur)
  - seo-geo-claude-skills (CORE-EEAT kwaliteitsframework)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

from config import check_config, BLOG_DIR
from cities import CITIES, get_city, get_next_city
from agents import run_pipeline
from html_template import generate_html
from publisher import publish_article, run_git
from emailer import send_article_notification


# Bestand dat bijhoudt welke steden al gepubliceerd zijn
PUBLISHED_FILE = Path(BLOG_DIR) / 'generator' / 'published.json'


def print_keyword_report(city, meta):
    """Print overzicht van gevonden zoekwoorden (keyword research rapport)."""
    keywords = meta.get('keywords_data', {})
    if not keywords:
        return

    print("\n" + "=" * 60)
    print(f"KEYWORD RAPPORT — {city['keyword']}")
    print("=" * 60)

    long_tail = keywords.get('long_tail', [])
    vragen = keywords.get('vragen', [])
    gerelateerd = keywords.get('gerelateerd', [])

    if long_tail:
        print(f"\n LONG-TAIL KEYWORDS ({len(long_tail)} gevonden):")
        for kw in long_tail:
            print(f"   • {kw}")

    if vragen:
        print(f"\n PEOPLE ALSO ASK — VRAGEN ({len(vragen)} gevonden):")
        for v in vragen:
            print(f"   ? {v}")

    if gerelateerd:
        print(f"\n GERELATEERDE ZOEKTERMEN ({len(gerelateerd)} gevonden):")
        for g in gerelateerd:
            print(f"   ~ {g}")

    secondary = meta.get('secondary_keywords', [])
    if secondary:
        print(f"\n SEO SECONDARY KEYWORDS:")
        for s in secondary:
            print(f"   · {s}")

    print(f"\n FOCUS KEYWORD: {meta.get('focus_keyword', city['keyword'])}")
    print(f" META TITLE:    {meta.get('meta_title', '')}")
    print(f" LEESTIJD:      {meta.get('reading_time', '')}")
    print("=" * 60 + "\n")


def load_published():
    """Laad lijst van gepubliceerde stad-slugs."""
    if PUBLISHED_FILE.exists():
        try:
            return json.loads(PUBLISHED_FILE.read_text())
        except:
            pass

    # Als geen published.json: detecteer bestaande HTML bestanden
    blog_path = Path(BLOG_DIR)
    existing = [
        f.stem for f in blog_path.glob('*.html')
        if f.stem not in ('index',)
    ]
    return existing


def save_published(published):
    """Sla bij welke steden gepubliceerd zijn."""
    PUBLISHED_FILE.write_text(json.dumps(published, indent=2, ensure_ascii=False))


def show_status():
    """Toon overzicht van alle steden en hun publicatie-status."""
    published = load_published()

    print("\nDe Trouwvideograaf – Blog Status")
    print("=" * 60)
    print(f"{'Stad':<20} {'Provincie':<15} {'Status':<10}")
    print("-" * 60)

    for city in CITIES:
        slug = city['slug']
        city_name = city['city']
        province = city['province']
        status = "✓ LIVE" if slug in published else "○ Gepland"
        print(f"{city_name:<20} {province:<15} {status}")

    total = len(CITIES)
    done = len([c for c in CITIES if c['slug'] in published])
    print("-" * 60)
    print(f"Gepubliceerd: {done}/{total} steden")
    print(f"Nog te doen: {total - done} steden\n")


def rebuild_index_html(published_list):
    """
    Herbouw index.html op basis van alle gepubliceerde steden.
    Voegt automatisch nieuwe steden toe na elke publicatie.
    """
    blog_path = Path(BLOG_DIR)

    # Haal city-data op voor elke gepubliceerde stad (in volgorde van CITIES)
    published_cities = [c for c in CITIES if c['slug'] in published_list]

    if not published_cities:
        return

    # Genereer kaartjes HTML
    cards_html = ''
    for c in published_cities:
        img = c.get('wikimedia_hero', '')
        slug = c['slug']
        city_name = c['city']
        province = c['province']
        character = c.get('character', '')
        # Korte beschrijving op basis van character
        desc = character.capitalize() + '.' if character else f'Trouwvideografie in {city_name}.'

        cards_html += f'''
    <a href="{slug}.html" class="card">
      <div class="card-img">
        <img src="{img}" alt="Trouwvideograaf {city_name}" loading="lazy" />
      </div>
      <div class="card-body">
        <div class="card-tag">{city_name} &middot; {province}</div>
        <h2>Trouwvideograaf {city_name} – Professionele Trouwfilm</h2>
        <p>{desc}</p>
        <span class="card-link">Lees verder &rarr;</span>
      </div>
    </a>
'''

    index_html = f'''<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Blog | De Trouwvideograaf – Trouwfilms door heel Nederland</title>
  <meta name="description" content="Lees alles over trouwvideografie per stad. Tips, locaties en inspiratie van De Trouwvideograaf voor jouw bruiloft." />
  <link rel="canonical" href="https://blog.detrouwvideograaf.net" />
  <link rel="icon" href="https://horizons-cdn.hostinger.com/7cd8ba0d-3977-441d-bf44-807d3f62ddbd/246cf8ed4e7e7c18381b5834fe2100e9.png" />
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Georgia', serif; color: #1a1a1a; background: #fff; line-height: 1.8; }}
    nav {{ background: #fff; border-bottom: 1px solid #eee; padding: 14px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
    nav .logo {{ display: flex; align-items: center; text-decoration: none; }}
    nav .logo img {{ height: 52px; width: auto; display: block; }}
    nav a.cta {{ background: #c9a84c; color: white; padding: 10px 22px; border-radius: 30px; text-decoration: none; font-size: 0.9rem; font-family: sans-serif; font-weight: bold; }}
    nav a.cta:hover {{ background: #b8943e; }}
    .page-hero {{ background: #1a1a1a; color: white; padding: 80px 40px 60px; text-align: center; }}
    .page-hero .tag {{ font-family: sans-serif; font-size: 0.75rem; letter-spacing: 3px; text-transform: uppercase; color: #c9a84c; margin-bottom: 16px; }}
    .page-hero h1 {{ font-size: 2.8rem; margin-bottom: 16px; }}
    .page-hero p {{ font-size: 1.1rem; color: rgba(255,255,255,0.75); max-width: 600px; margin: 0 auto; font-family: sans-serif; }}
    .posts {{ max-width: 1100px; margin: 0 auto; padding: 60px 32px 80px; }}
    .posts-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; }}
    .card {{ border-radius: 16px; overflow: hidden; border: 1px solid #eee; background: #fff; text-decoration: none; color: #1a1a1a; display: block; transition: box-shadow 0.2s, transform 0.2s; }}
    .card:hover {{ box-shadow: 0 8px 32px rgba(0,0,0,0.10); transform: translateY(-3px); }}
    .card-img {{ height: 200px; overflow: hidden; }}
    .card-img img {{ width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.4s; }}
    .card:hover .card-img img {{ transform: scale(1.05); }}
    .card-body {{ padding: 22px 24px 28px; }}
    .card-tag {{ font-family: sans-serif; font-size: 0.72rem; letter-spacing: 2px; text-transform: uppercase; color: #c9a84c; margin-bottom: 8px; }}
    .card-body h2 {{ font-size: 1.15rem; line-height: 1.4; margin-bottom: 10px; color: #1a1a1a; }}
    .card-body p {{ font-size: 0.92rem; color: #666; font-family: sans-serif; line-height: 1.6; margin-bottom: 16px; }}
    .card-link {{ font-family: sans-serif; font-size: 0.85rem; font-weight: bold; color: #c9a84c; }}
    footer {{ background: #1a1a1a; color: #999; text-align: center; padding: 48px 32px 32px; font-family: sans-serif; font-size: 0.85rem; }}
    .footer-logo {{ height: 64px; width: auto; display: block; margin: 0 auto 24px; opacity: 0.9; }}
    footer a {{ color: #c9a84c; text-decoration: none; }}
    @media (max-width: 900px) {{ .posts-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (max-width: 580px) {{
      .posts-grid {{ grid-template-columns: 1fr; }}
      .page-hero h1 {{ font-size: 2rem; }}
      nav {{ padding: 10px 20px; }}
      nav .logo img {{ height: 40px; }}
      .posts {{ padding: 40px 20px 60px; }}
    }}
  </style>
</head>
<body>

<nav>
  <a href="https://www.detrouwvideograaf.net" class="logo">
    <img src="https://horizons-cdn.hostinger.com/7cd8ba0d-3977-441d-bf44-807d3f62ddbd/82feefc4ccc72bbcb44edf66a1b1ba2b.png"
         alt="De Trouwvideograaf" />
  </a>
  <a href="https://www.detrouwvideograaf.net/#contact" class="cta">Gratis offerte</a>
</nav>

<div class="page-hero">
  <div class="tag">Trouwvideografie &middot; Per stad</div>
  <h1>Blog</h1>
  <p>Alles over trouwen op bijzondere locaties door heel Nederland — en hoe wij jouw dag vastleggen.</p>
</div>

<main class="posts">
  <div class="posts-grid">
{cards_html}
  </div>
</main>

<footer>
  <a href="https://www.detrouwvideograaf.net">
    <img src="https://horizons-cdn.hostinger.com/7cd8ba0d-3977-441d-bf44-807d3f62ddbd/246cf8ed4e7e7c18381b5834fe2100e9.png"
         alt="De Trouwvideograaf" class="footer-logo" />
  </a>
  <p>&copy; 2026 <a href="https://www.detrouwvideograaf.net">De Trouwvideograaf</a> &middot; Professionele trouwvideografie door heel Nederland &middot; <a href="https://www.detrouwvideograaf.net/#contact">Contact</a></p>
</footer>

</body>
</html>'''

    index_path = blog_path / 'index.html'
    index_path.write_text(index_html, encoding='utf-8')
    print(f"  Index bijgewerkt met {len(published_cities)} steden.")

    # Sitemap.xml bijwerken
    today = datetime.now().strftime('%Y-%m-%d')
    url_entries = '\n\n  <url>\n    <loc>https://blog.detrouwvideograaf.net/</loc>\n    <lastmod>' + today + '</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>'
    for c in published_cities:
        url_entries += f'\n\n  <url>\n    <loc>https://blog.detrouwvideograaf.net/{c["slug"]}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>'

    sitemap_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{url_entries}\n\n</urlset>\n'
    sitemap_path = blog_path / 'sitemap.xml'
    sitemap_path.write_text(sitemap_xml, encoding='utf-8')
    print(f"  Sitemap bijgewerkt met {len(published_cities)} steden.")

    # Push index.html + sitemap.xml naar GitHub
    run_git(['add', 'index.html', 'sitemap.xml'], cwd=str(blog_path))
    ok, status = run_git(['status', '--short'], cwd=str(blog_path))
    if status.strip():
        run_git(['commit', '-m', f'Update blog index + sitemap ({len(published_cities)} steden)'], cwd=str(blog_path))
        run_git(['push', 'origin', 'main'], cwd=str(blog_path))


def generate_for_city(city, test_mode=False):
    """
    Genereer en publiceer een artikel voor een specifieke stad.

    Args:
        city: Stad dictionary
        test_mode: Als True, sla op maar push NIET naar GitHub

    Returns:
        True als succesvol
    """
    print(f"\nStarting pipeline voor: {city['city']}")
    print(f"Keyword: {city['keyword']}")
    print(f"Modus: {'TEST (geen push)' if test_mode else 'PRODUCTIE'}")
    print("=" * 60)

    try:
        # ─── MULTI-AGENT PIPELINE ─────────────────────────────────────
        content, meta = run_pipeline(city)

        # ─── KEYWORD RAPPORT ──────────────────────────────────────────
        print_keyword_report(city, meta)

        # ─── HTML GENEREREN ───────────────────────────────────────────
        print("\n  HTML genereren...")
        html = generate_html(city, content, meta)
        filename = f"{city['slug']}.html"

        # ─── PUBLICEREN ───────────────────────────────────────────────
        if test_mode:
            # Sla lokaal op maar push niet
            output_path = Path(BLOG_DIR) / filename
            output_path.write_text(html, encoding='utf-8')
            print(f"\n  TEST: Opgeslagen als {output_path}")
            print(f"  Open in browser: file://{output_path}")
            published = False
        else:
            published = publish_article(html, filename, city['city'])

        # ─── GEPUBLICEERD BIJHOUDEN + INDEX UPDATEN ───────────────────
        if not test_mode:
            published_list = load_published()
            if city['slug'] not in published_list:
                published_list.append(city['slug'])
                save_published(published_list)
            # Herbouw index.html zodat nieuwe stad zichtbaar is
            print("\n  Blog index updaten...")
            rebuild_index_html(published_list)

        # ─── EMAIL NOTIFICATIE ─────────────────────────────────────────
        send_article_notification(city, meta, html, published if not test_mode else False)

        print(f"\nKlaar! Artikel voor {city['city']} is {'gepubliceerd' if published else 'opgeslagen'}.")
        return True

    except Exception as e:
        print(f"\nFOUT: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='De Trouwvideograaf Blog Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python main.py                      # Volgende ongepubliceerde stad
  python main.py --stad kampen        # Specifieke stad
  python main.py --lijst              # Overzicht van alle steden
  python main.py --test               # Test zonder GitHub push
  python main.py --stad zwolle --test # Test Zwolle artikel
        """
    )

    parser.add_argument('--stad', type=str, help='Stad slug (bijv. kampen, zwolle)')
    parser.add_argument('--lijst', action='store_true', help='Toon statusoverzicht')
    parser.add_argument('--test', action='store_true', help='Test modus (geen GitHub push)')

    args = parser.parse_args()

    # Toon statusoverzicht
    if args.lijst:
        show_status()
        return

    # Controleer configuratie
    if not check_config():
        sys.exit(1)

    # Bepaal welke stad
    if args.stad:
        # Specifieke stad
        slug = args.stad.replace('trouwvideograaf-', '')
        city = get_city(slug)
        if not city:
            print(f"Stad '{args.stad}' niet gevonden in cities.py")
            print("Beschikbare steden:")
            for c in CITIES:
                print(f"  {c['slug']}")
            sys.exit(1)
    else:
        # Volgende ongepubliceerde stad
        published = load_published()
        city = get_next_city(published)
        if not city:
            print("Alle steden zijn al gepubliceerd!")
            show_status()
            return

    # Genereer artikel
    success = generate_for_city(city, test_mode=args.test)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
