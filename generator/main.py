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
from publisher import publish_article
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

        # ─── GEPUBLICEERD BIJHOUDEN ────────────────────────────────────
        if not test_mode:
            published_list = load_published()
            if city['slug'] not in published_list:
                published_list.append(city['slug'])
                save_published(published_list)

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
