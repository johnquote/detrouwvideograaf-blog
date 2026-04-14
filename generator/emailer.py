"""
Email notificatie voor De Trouwvideograaf blog generator.
Stuurt een dagelijkse email met het gegenereerde artikel.
Gebruikt Gmail SMTP (gratis).
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD, EMAIL_ENABLED


def send_article_notification(city: dict, meta: dict, html_content: str, published: bool) -> bool:
    """
    Stuur een email notificatie met het gegenereerde artikel.

    Args:
        city: Stad dictionary
        meta: SEO metadata
        html_content: De volledige HTML van het artikel
        published: Of het artikel live staat

    Returns:
        True als email succesvol verstuurd
    """
    if not EMAIL_ENABLED:
        print("  Email notificatie uitgeschakeld (stel EMAIL_ENABLED=true in .env)")
        return False

    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASSWORD:
        print("  Email niet geconfigureerd — sla email notificatie over")
        return False

    print(f"  Email versturen naar {EMAIL_TO}...")

    city_name = city['city']
    slug = city['slug']
    today = datetime.now().strftime("%d %B %Y")
    live_url = f"https://blog.detrouwvideograaf.net/{slug}"
    status_text = f'<span style="color:#22c55e;font-weight:bold;">✓ LIVE</span> op <a href="{live_url}">{live_url}</a>' if published else '<span style="color:#f59e0b;">⚠ Lokaal opgeslagen (push handmatig)</span>'

    # Email body (HTML)
    email_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; color: #333; max-width: 680px; margin: 0 auto; padding: 20px; }}
  .header {{ background: #1a1a1a; color: white; padding: 24px 28px; border-radius: 8px 8px 0 0; }}
  .header h1 {{ font-size: 1.3rem; margin: 0; }}
  .header p {{ color: #999; font-size: 0.85rem; margin: 6px 0 0; }}
  .body {{ border: 1px solid #eee; border-top: none; padding: 28px; border-radius: 0 0 8px 8px; }}
  .stat {{ display: inline-block; background: #f8f8f8; border-radius: 6px; padding: 8px 14px; margin: 4px; font-size: 0.85rem; }}
  .stat strong {{ display: block; font-size: 1.1rem; color: #1a1a1a; }}
  .preview {{ background: #fdf9f1; border: 1px solid #e8d9a8; border-radius: 8px; padding: 20px; margin: 20px 0; font-size: 0.9rem; color: #555; line-height: 1.6; }}
  .btn {{ display: inline-block; background: #c9a84c; color: white; padding: 12px 28px; border-radius: 30px; text-decoration: none; font-weight: bold; margin: 8px 4px; }}
  .btn.secondary {{ background: #333; }}
  .footer {{ color: #999; font-size: 0.8rem; margin-top: 28px; text-align: center; }}
  .score {{ background: #c9a84c; color: white; font-weight: bold; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="header">
  <h1>Nieuw artikel gegenereerd: Trouwvideograaf {city_name}</h1>
  <p>De Trouwvideograaf · Blog Generator · {today}</p>
</div>
<div class="body">

  <p>Er is automatisch een nieuw SEO artikel aangemaakt voor <strong>{city_name}</strong>.</p>

  <div style="margin: 20px 0;">
    <div class="stat"><strong>{city_name}</strong>Stad</div>
    <div class="stat"><strong>{city['province']}</strong>Provincie</div>
    <div class="stat"><strong>{meta.get('reading_time', '6 min')}</strong>Leestijd</div>
  </div>

  <p><strong>Status:</strong> {status_text}</p>

  <h3 style="margin: 24px 0 8px;">SEO Details</h3>
  <table style="width:100%;font-size:0.9rem;border-collapse:collapse;">
    <tr><td style="padding:6px 0;color:#999;width:40%;">Meta title</td><td style="padding:6px 0;"><strong>{meta.get('meta_title', '')}</strong></td></tr>
    <tr><td style="padding:6px 0;color:#999;">Meta description</td><td style="padding:6px 0;">{meta.get('meta_desc', '')}</td></tr>
    <tr><td style="padding:6px 0;color:#999;">Focus keyword</td><td style="padding:6px 0;">{meta.get('focus_keyword', '')}</td></tr>
    <tr><td style="padding:6px 0;color:#999;">Gerelateerde kw.</td><td style="padding:6px 0;">{', '.join(meta.get('secondary_keywords', []))}</td></tr>
  </table>

  <div style="margin: 24px 0;">
    <a href="{live_url}" class="btn">Bekijk artikel live</a>
    <a href="https://app.netlify.com/projects/cute-twilight-a0f2fe" class="btn secondary">Netlify dashboard</a>
  </div>

  <div class="preview">
    <strong>Meta description:</strong><br>
    {meta.get('meta_desc', '')}
  </div>

  <p class="footer">
    Automatisch gegenereerd door De Trouwvideograaf Blog Generator<br>
    Aangedreven door Claude Haiku API · Multi-Agent Pipeline · CORE-EEAT geoptimaliseerd
  </p>
</div>
</body>
</html>
"""

    # Email tekst versie
    email_text = f"""
Nieuw artikel: Trouwvideograaf {city_name}
{'=' * 50}

Status: {'LIVE op ' + live_url if published else 'Lokaal opgeslagen'}
Meta title: {meta.get('meta_title', '')}
Meta description: {meta.get('meta_desc', '')}
Focus keyword: {meta.get('focus_keyword', '')}

Live URL: {live_url}
Netlify: https://app.netlify.com/projects/cute-twilight-a0f2fe

---
De Trouwvideograaf Blog Generator
"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Nieuw artikel: Trouwvideograaf {city_name} – De Trouwvideograaf Blog"
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO

        msg.attach(MIMEText(email_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(email_html, 'html', 'utf-8'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

        print(f"  Email verstuurd naar {EMAIL_TO}")
        return True

    except Exception as e:
        print(f"  Email fout: {e}")
        print(f"  Tip: Gebruik een Gmail App Password (niet je normale wachtwoord)")
        print(f"  Gmail App Password instellen: myaccount.google.com/apppasswords")
        return False
