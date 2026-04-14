"""
HTML Template Generator voor De Trouwvideograaf Blog
Converteert Markdown artikel content naar onze exacte HTML template.
"""

import re
from datetime import datetime


def _make_figure_html(img):
    """Maak single-line figure HTML voor een afbeelding."""
    return (
        f'<figure class="article-figure">'
        f'<img src="{img["url"]}" alt="{img["alt"]}" class="inline-img" loading="lazy" />'
        f'<figcaption class="img-caption">{img["caption"]} &mdash; <small>{img["credit"]}</small></figcaption>'
        f'</figure>'
    )


def inject_images(text, images):
    """Verwerk afbeeldingen in de tekst.

    Stap 1: Vervang [FOTO_X] placeholders die Claude heeft geplaatst.
    Stap 2: Resterende afbeeldingen worden AUTOMATISCH ingespoten na H2-koppen,
            zodat alle afbeeldingen altijd in het artikel verschijnen.
    """
    if not images:
        return text

    # Bijhouden welke afbeeldingen al zijn geplaatst via placeholder
    placed = [False] * len(images)

    for i, img in enumerate(images):
        placeholder = f"[FOTO_{i+1}]"
        if placeholder in text:
            text = text.replace(placeholder, _make_figure_html(img))
            placed[i] = True

    # Verwijder eventuele overgebleven onbekende placeholders
    text = re.sub(r'\[FOTO_\d+\]', '', text)

    # Automatisch injecteren: afbeeldingen die niet via placeholder zijn geplaatst
    # worden na een H2-kop ingespoten (2e, 4e H2 etc.)
    unplaced = [i for i, p in enumerate(placed) if not p]
    if not unplaced:
        return text

    # Zoek alle H2-posities in de tekst
    h2_positions = [m.end() for m in re.finditer(r'## .+', text)]

    if not h2_positions:
        # Geen H2s — voeg afbeeldingen toe na de 3e paragraaf
        para_positions = [m.end() for m in re.finditer(r'\n\n', text)]
        target_positions = para_positions[2::3] if len(para_positions) > 2 else para_positions[-1:]
    else:
        # Gebruik elke 2e H2 als injectiepunt
        target_positions = h2_positions[1::2]  # 2e, 4e, 6e H2...

    # Injecteer afbeeldingen op gevonden posities (van achter naar voren om offset te bewaren)
    inject_pairs = list(zip(unplaced, target_positions))
    for img_idx, pos in sorted(inject_pairs, key=lambda x: x[1], reverse=True):
        img_html = "\n\n" + _make_figure_html(images[img_idx]) + "\n\n"
        text = text[:pos] + img_html + text[pos:]

    return text


def markdown_to_html(text):
    """Converteer Markdown naar HTML (vereenvoudigd)."""
    lines = text.split('\n')
    html_parts = []
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue

        # Doorgeef HTML-blokken (figure, img, div, etc.) ongewijzigd
        if re.match(r'^<[a-zA-Z/]', line):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(line)
            continue

        # Headers
        if line.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('# '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            # H1 wordt overgeslagen (staat al in hero)
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            content = line[2:]
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', content)
            html_parts.append(f'<li>{content}</li>')
        elif line.startswith('> '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<blockquote><p>{line[2:]}</p></blockquote>')
        else:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            # Bold en links
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            content = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', content)
            html_parts.append(f'<p>{content}</p>')

    if in_list:
        html_parts.append('</ul>')

    return '\n'.join(html_parts)


def extract_faq_section(content):
    """Haal FAQ sectie uit de Markdown content en geef terug als structuur."""
    faq_items = []
    remaining_content = []
    in_faq = False
    current_q = None
    current_a = []

    for line in content.split('\n'):
        stripped = line.strip()

        # Detecteer FAQ sectie
        if re.match(r'^##\s*(veelgestelde vragen|faq|vraag en antwoord)', stripped.lower()):
            in_faq = True
            continue

        if in_faq:
            # Nieuwe vraag (H3)
            if stripped.startswith('### '):
                if current_q and current_a:
                    faq_items.append({'q': current_q, 'a': ' '.join(current_a)})
                current_q = stripped[4:]
                current_a = []
            # Volgende H2 = einde FAQ
            elif stripped.startswith('## '):
                if current_q and current_a:
                    faq_items.append({'q': current_q, 'a': ' '.join(current_a)})
                in_faq = False
                remaining_content.append(line)
            elif stripped and not stripped.startswith('#'):
                if current_q:
                    current_a.append(stripped)
        else:
            remaining_content.append(line)

    # Laatste FAQ item
    if current_q and current_a:
        faq_items.append({'q': current_q, 'a': ' '.join(current_a)})

    return '\n'.join(remaining_content), faq_items


def build_faq_html(faq_items):
    """Bouw FAQ HTML sectie."""
    if not faq_items:
        return ''

    items_html = '\n'.join([
        f'''<div class="faq-item">
  <h3>{item['q']}</h3>
  <p>{item['a']}</p>
</div>'''
        for item in faq_items
    ])

    return f'''<h2>Veelgestelde vragen over trouwen in {{city}}</h2>
{items_html}'''


def build_faq_schema(faq_items, city_name):
    """Genereer FAQ Schema markup."""
    if not faq_items:
        return ''

    qa_items = ',\n'.join([
        f'''      {{
        "@type": "Question",
        "name": "{item['q'].replace('"', "'")}",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "{item['a'][:200].replace('"', "'")}"
        }}
      }}'''
        for item in faq_items
    ])

    return f'''  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
{qa_items}
    ]
  }}
  </script>'''


def build_related_cards(related_slugs):
    """Bouw gerelateerde artikelen cards."""
    if not related_slugs:
        return ''

    def slug_to_city(slug):
        return slug.replace('-', ' ').title()

    cards = '\n'.join([
        f'''    <a href="https://blog.detrouwvideograaf.net/{slug}" class="related-card">
      <div class="city">Trouwvideograaf</div>
      {slug_to_city(slug)}
    </a>'''
        for slug in related_slugs[:3]
    ])

    return f'''<div class="related">
  <h3>Meer steden in de regio</h3>
  <div class="related-grid">
{cards}
  </div>
</div>'''


def generate_html(city, content, meta):
    """
    Genereer complete HTML pagina van artikel content en metadata.
    """
    today = datetime.now()
    date_str = today.strftime("%-d %B %Y").lower()
    date_iso = today.strftime("%Y-%m-%d")

    city_name = city['city']
    slug = city['slug']
    hero_img = city['wikimedia_hero']
    keyword = city['keyword']

    # CTA achtergrond = laatste inline afbeelding (anders dan hero)
    images_list = city.get("inline_images", [])
    cta_img = images_list[-1]['url'] if images_list else hero_img

    meta_title = meta.get('meta_title', f'Trouwvideograaf {city_name} | De Trouwvideograaf')
    meta_desc = meta.get('meta_desc', f'Professionele trouwvideograaf in {city_name}.')
    reading_time = meta.get('reading_time', '6 min leestijd')
    secondary_kw = ', '.join(meta.get('secondary_keywords', []))

    # Injecteer foto's (vervang [FOTO_1] etc. door echte img-tags — single-line!)
    images = city.get("inline_images", [])
    content_with_images = inject_images(content, images)

    # Extraheer FAQ sectie
    content_without_faq, faq_items = extract_faq_section(content_with_images)

    # Converteer content naar HTML
    article_html = markdown_to_html(content_without_faq)

    # FAQ HTML + Schema
    faq_html = build_faq_html(faq_items).replace('{city}', city_name)
    faq_schema = build_faq_schema(faq_items, city_name)

    # Gerelateerde artikelen
    related_html = build_related_cards(city.get('related', []))

    # Canonical URL
    canonical = f"https://blog.detrouwvideograaf.net/{slug}"

    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{meta_title}</title>
  <meta name="description" content="{meta_desc}" />
  <meta name="keywords" content="{keyword}, bruiloftfilm {city_name}, videograaf bruiloft {city_name}{", " + secondary_kw if secondary_kw else ""}" />
  <link rel="canonical" href="{canonical}" />
  <link rel="icon" href="https://horizons-cdn.hostinger.com/7cd8ba0d-3977-441d-bf44-807d3f62ddbd/246cf8ed4e7e7c18381b5834fe2100e9.png" />

  <meta property="og:title" content="{meta_title}" />
  <meta property="og:description" content="{meta_desc}" />
  <meta property="og:image" content="{hero_img}" />
  <meta property="og:type" content="article" />

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.detrouwvideograaf.net" }},
      {{ "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://blog.detrouwvideograaf.net" }},
      {{ "@type": "ListItem", "position": 3, "name": "Trouwvideograaf {city_name}", "item": "{canonical}" }}
    ]
  }}
  </script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Trouwvideograaf {city_name} \u2013 Jouw Bruiloft Vastgelegd",
    "description": "{meta_desc}",
    "image": "{hero_img}",
    "author": {{
      "@type": "Organization",
      "name": "De Trouwvideograaf",
      "url": "https://www.detrouwvideograaf.net"
    }},
    "publisher": {{
      "@type": "Organization",
      "name": "De Trouwvideograaf",
      "url": "https://www.detrouwvideograaf.net"
    }},
    "datePublished": "{date_iso}",
    "dateModified": "{date_iso}",
    "speakable": {{
      "@type": "SpeakableSpecification",
      "cssSelector": [".hero-text p", "article > p:first-of-type"]
    }}
  }}
  </script>

  <!-- LocalBusiness / ProfessionalService — voor AI-modellen (ChatGPT, Perplexity, Google AI) -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    "name": "De Trouwvideograaf",
    "url": "https://www.detrouwvideograaf.net",
    "telephone": "+31683247177",
    "priceRange": "€€",
    "image": "https://horizons-cdn.hostinger.com/7cd8ba0d-3977-441d-bf44-807d3f62ddbd/246cf8ed4e7e7c18381b5834fe2100e9.png",
    "description": "Professionele trouwvideograaf actief door heel Nederland. Cinematic trouwfilms op maat, inclusief drone en same-day edit.",
    "serviceType": "Trouwvideografie",
    "areaServed": {{
      "@type": "City",
      "name": "{city_name}",
      "containedInPlace": {{
        "@type": "Country",
        "name": "Nederland"
      }}
    }},
    "sameAs": [
      "https://www.youtube.com/@detrouwvideograaf"
    ],
    "hasOfferCatalog": {{
      "@type": "OfferCatalog",
      "name": "Trouwvideografie pakketten",
      "url": "https://www.detrouwvideograaf.net/#pakketten"
    }}
  }}
  </script>

{faq_schema}

  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Georgia', serif; color: #1a1a1a; background: #fff; line-height: 1.8; }}

    /* ── NAV ── */
    nav {{ background: #fff; border-bottom: 1px solid #eee; padding: 14px 40px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
    nav .logo {{ display: flex; align-items: center; text-decoration: none; }}
    nav .logo img {{ height: 52px; width: auto; display: block; }}
    nav a.cta {{ background: #c9a84c; color: white; padding: 10px 22px; border-radius: 30px; text-decoration: none; font-size: 0.9rem; font-family: sans-serif; font-weight: bold; }}
    nav a.cta:hover {{ background: #b8943e; }}

    /* ── HERO ── */
    .hero {{ position: relative; height: 520px; overflow: hidden; }}
    .hero img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .hero-overlay {{ position: absolute; inset: 0; background: rgba(0,0,0,0.55); }}
    .hero-text {{ position: absolute; bottom: 60px; left: 50%; transform: translateX(-50%); text-align: center; color: white; width: 90%; max-width: 750px; }}
    .hero-text .tag {{ font-family: sans-serif; font-size: 0.8rem; letter-spacing: 3px; text-transform: uppercase; color: #c9a84c; margin-bottom: 14px; }}
    .hero-text h1 {{ font-size: 2.4rem; line-height: 1.3; margin-bottom: 16px; }}
    .hero-text p {{ font-size: 1.1rem; opacity: 0.9; }}

    /* ── ARTICLE ── */
    article {{ max-width: 780px; margin: 60px auto; padding: 0 24px; }}
    article h2 {{ font-size: 1.7rem; margin: 48px 0 16px; color: #1a1a1a; }}
    article h3 {{ font-size: 1.25rem; margin: 32px 0 12px; color: #333; }}
    article p {{ margin-bottom: 20px; font-size: 1.05rem; color: #333; }}
    article ul {{ margin: 0 0 24px 24px; }}
    article ul li {{ margin-bottom: 10px; font-size: 1.05rem; color: #333; }}
    article a {{ color: #c9a84c; }}
    article a:hover {{ color: #b8943e; }}

    blockquote {{ border-left: 4px solid #c9a84c; padding: 20px 28px; margin: 36px 0; background: #fdf9f1; font-style: italic; font-size: 1.05rem; color: #555; border-radius: 0 8px 8px 0; }}

    /* ── INLINE FOTO'S ── */
    .article-figure {{ margin: 36px 0; }}
    .inline-img {{ width: 100%; border-radius: 12px; object-fit: cover; height: 380px; display: block; }}
    .img-caption {{ text-align: center; font-size: 0.85rem; color: #999; font-family: sans-serif; margin-top: 10px; }}

    /* ── INFO BOX ── */
    .info-box {{ background: #fdf9f1; border: 1px solid #e8d9a8; border-radius: 12px; padding: 28px 32px; margin: 36px 0; }}
    .info-box h3 {{ margin-top: 0; margin-bottom: 12px; color: #1a1a1a; }}
    .info-box p {{ margin-bottom: 0; font-size: 0.98rem; color: #555; }}

    .checklist {{ background: #f8f8f8; border-radius: 12px; padding: 28px 32px; margin: 36px 0; }}
    .checklist h3 {{ margin-top: 0; margin-bottom: 16px; }}
    .checklist ul {{ list-style: none; margin: 0; }}
    .checklist ul li {{ margin-bottom: 10px; font-size: 1.05rem; }}
    .checklist ul li::before {{ content: "\2713  "; color: #c9a84c; font-weight: bold; }}

    .locaties-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 24px 0 36px; }}
    .locatie-card {{ background: #f8f8f8; border-radius: 10px; padding: 20px 22px; }}
    .locatie-card strong {{ display: block; margin-bottom: 4px; color: #1a1a1a; }}
    .locatie-card span {{ font-size: 0.9rem; color: #666; font-family: sans-serif; }}

    /* ── CTA BLOCK met achtergrondafbeelding ── */
    .cta-block {{ position: relative; border-radius: 16px; overflow: hidden; margin: 56px 0; background-size: cover; background-position: center; }}
    .cta-overlay {{ background: rgba(0,0,0,0.65); padding: 72px 40px; text-align: center; }}
    .cta-overlay h2 {{ color: white; font-size: 1.9rem; margin: 0 0 14px; font-family: 'Georgia', serif; }}
    .cta-overlay p {{ color: rgba(255,255,255,0.85); margin-bottom: 32px; font-family: sans-serif; font-size: 1.05rem; }}
    .cta-overlay a {{ background: #c9a84c; color: white; padding: 16px 40px; border-radius: 30px; text-decoration: none; font-size: 1.05rem; font-family: sans-serif; display: inline-block; font-weight: bold; letter-spacing: 0.5px; }}
    .cta-overlay a:hover {{ background: #b8943e; }}

    /* ── FAQ ── */
    .faq-item {{ border-bottom: 1px solid #eee; padding: 24px 0; }}
    .faq-item:last-child {{ border-bottom: none; }}
    .faq-item h3 {{ margin: 0 0 10px; font-size: 1.1rem; }}
    .faq-item p {{ margin: 0; }}

    /* ── RELATED ── */
    .related {{ border-top: 1px solid #eee; padding-top: 40px; margin-top: 60px; }}
    .related h3 {{ font-size: 1.2rem; margin-bottom: 20px; font-family: sans-serif; }}
    .related-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
    .related-card {{ background: #f8f8f8; border-radius: 10px; padding: 20px; text-decoration: none; color: #1a1a1a; font-size: 0.95rem; transition: background 0.2s; }}
    .related-card:hover {{ background: #f0ead8; }}
    .related-card .city {{ font-size: 0.75rem; color: #c9a84c; font-family: sans-serif; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }}

    /* ── FOOTER ── */
    footer {{ background: #1a1a1a; color: #999; text-align: center; padding: 48px 32px 32px; font-family: sans-serif; font-size: 0.85rem; margin-top: 80px; }}
    footer a {{ color: #c9a84c; text-decoration: none; }}
    .footer-logo {{ height: 64px; width: auto; display: block; margin: 0 auto 24px; opacity: 0.9; }}

    /* ── STICKY BAR ── */
    .sticky-bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a1a; border-top: 2px solid #c9a84c; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; z-index: 999; gap: 12px; }}
    .sticky-bar .sticky-text {{ color: #fff; font-family: sans-serif; font-size: 0.9rem; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .sticky-bar .sticky-text span {{ color: #c9a84c; font-weight: bold; }}
    .sticky-bar .sticky-actions {{ display: flex; gap: 10px; flex-shrink: 0; }}
    .sticky-bar a.btn-bel {{ background: transparent; border: 1px solid #c9a84c; color: #c9a84c; padding: 9px 18px; border-radius: 30px; text-decoration: none; font-size: 0.85rem; font-family: sans-serif; white-space: nowrap; }}
    .sticky-bar a.btn-offerte {{ background: #c9a84c; color: white; padding: 9px 20px; border-radius: 30px; text-decoration: none; font-size: 0.85rem; font-family: sans-serif; font-weight: bold; white-space: nowrap; }}
    .sticky-bar a.btn-bel:hover {{ background: #c9a84c; color: white; }}
    .sticky-bar a.btn-offerte:hover {{ background: #b8943e; }}
    body {{ padding-bottom: 70px; }}

    /* ── BREADCRUMB & META ── */
    .breadcrumb {{ max-width: 780px; margin: 20px auto 0; padding: 0 24px; font-family: sans-serif; font-size: 0.82rem; color: #999; }}
    .breadcrumb a {{ color: #999; text-decoration: none; }}
    .breadcrumb a:hover {{ color: #c9a84c; }}
    .breadcrumb span {{ margin: 0 6px; }}

    .artikel-meta {{ max-width: 780px; margin: 12px auto 0; padding: 0 24px 24px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 20px; font-family: sans-serif; font-size: 0.85rem; color: #999; }}
    .auteur-avatar {{ width: 32px; height: 32px; border-radius: 50%; background: #c9a84c; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.75rem; font-weight: bold; flex-shrink: 0; }}

    /* ── RESPONSIVE ── */
    @media (max-width: 600px) {{
      .hero-text h1 {{ font-size: 1.8rem; }}
      .related-grid {{ grid-template-columns: 1fr; }}
      .locaties-grid {{ grid-template-columns: 1fr; }}
      nav {{ padding: 10px 20px; }}
      nav .logo img {{ height: 40px; }}
      .sticky-bar .sticky-text {{ display: none; }}
      .sticky-bar {{ justify-content: center; }}
      .artikel-meta {{ flex-wrap: wrap; gap: 10px; }}
      .cta-overlay {{ padding: 48px 24px; }}
      .cta-overlay h2 {{ font-size: 1.5rem; }}
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

<div class="breadcrumb">
  <a href="https://www.detrouwvideograaf.net">Home</a>
  <span>&#8250;</span>
  <a href="https://blog.detrouwvideograaf.net">Blog</a>
  <span>&#8250;</span>
  Trouwvideograaf {city_name}
</div>

<div class="artikel-meta">
  <div class="auteur" style="display:flex;align-items:center;gap:8px;">
    <div class="auteur-avatar">DT</div>
    <span>De Trouwvideograaf</span>
  </div>
  <span>&middot;</span>
  <span>{date_str}</span>
  <span>&middot;</span>
  <span>{reading_time}</span>
</div>

<div class="hero">
  <img src="{hero_img}" alt="Trouwen in {city_name} \u2013 {city['character']}" loading="lazy" />
  <div class="hero-overlay"></div>
  <div class="hero-text">
    <div class="tag">Trouwvideograaf &middot; {city_name}</div>
    <h1>Trouwvideograaf {city_name}</h1>
    <p>{meta_desc}</p>
  </div>
</div>

<article>

{article_html}

{faq_html}

<!-- CTA BLOCK met stadsafbeelding als achtergrond -->
<div class="cta-block" style="background-image: url('{cta_img}');">
  <div class="cta-overlay">
    <h2>Trouwen in {city_name}?</h2>
    <p>Wij kennen {city_name} op onze duim. Bereken direct de kosten voor jouw bruiloft.</p>
    <a href="https://www.detrouwvideograaf.net/#calculator">Bereken uw bruiloft &rarr;</a>
  </div>
</div>

{related_html}

</article>

<footer>
  <a href="https://www.detrouwvideograaf.net">
    <img src="https://horizons-cdn.hostinger.com/7cd8ba0d-3977-441d-bf44-807d3f62ddbd/246cf8ed4e7e7c18381b5834fe2100e9.png"
         alt="De Trouwvideograaf" class="footer-logo" />
  </a>
  <p>&copy; {today.year} <a href="https://www.detrouwvideograaf.net">De Trouwvideograaf</a> &middot; Professionele trouwvideografie door heel Nederland &middot; <a href="https://www.detrouwvideograaf.net/#contact">Contact</a></p>
</footer>

<!-- STICKY CTA BAR -->
<div class="sticky-bar">
  <div class="sticky-text">Trouwen in {city_name}? <span>Vraag vrijblijvend een offerte aan</span></div>
  <div class="sticky-actions">
    <a href="tel:+31683247177" class="btn-bel">&#128222; Bel ons</a>
    <a href="https://www.detrouwvideograaf.net/#contact" class="btn-offerte">Gratis offerte &rarr;</a>
  </div>
</div>

</body>
</html>'''
