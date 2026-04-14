"""
GitHub Publisher voor De Trouwvideograaf Blog
Pusht gegenereerde HTML artikelen automatisch naar GitHub.
Netlify detecteert de push en deployt automatisch naar blog.detrouwvideograaf.net
"""

import os
import subprocess
from pathlib import Path
from config import BLOG_DIR, GITHUB_REPO


def run_git(args: list[str], cwd: str = None) -> tuple[bool, str]:
    """Voer een git commando uit en geef (succes, output) terug."""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd or BLOG_DIR,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return success, output
    except Exception as e:
        return False, str(e)


def check_git_setup() -> bool:
    """Controleer of git en remote correct geconfigureerd zijn."""
    # Check of we in een git repo zitten
    ok, output = run_git(['status'])
    if not ok:
        print(f"  Git niet gevonden of geen repo: {output}")
        return False

    # Check of remote bestaat
    ok, remotes = run_git(['remote', '-v'])
    if 'origin' not in remotes:
        print(f"  Geen git remote 'origin' gevonden.")
        print(f"  Voeg toe met: git remote add origin {GITHUB_REPO}")
        return False

    return True


def publish_article(html_content: str, filename: str, city_name: str) -> bool:
    """
    Sla HTML op en push naar GitHub.
    Netlify deployt automatisch na de push.

    Args:
        html_content: De volledige HTML string
        filename: Bestandsnaam bijv. 'trouwvideograaf-kampen.html'
        city_name: Naam van de stad voor het commit bericht

    Returns:
        True als succesvol gepubliceerd
    """
    blog_path = Path(BLOG_DIR)
    file_path = blog_path / filename

    print(f"\n  Publiceer artikel: {filename}")

    # Stap 1: Sla HTML op
    print(f"  Stap 1/4: HTML opslaan...")
    try:
        file_path.write_text(html_content, encoding='utf-8')
        print(f"  Opgeslagen: {file_path}")
    except Exception as e:
        print(f"  FOUT bij opslaan: {e}")
        return False

    if not check_git_setup():
        print("  SKIP: Git niet correct geconfigureerd, artikel is wel lokaal opgeslagen.")
        return True  # Lokaal opslaan is gelukt

    # Stap 2: Git add
    print(f"  Stap 2/4: git add...")
    ok, output = run_git(['add', filename])
    if not ok:
        print(f"  FOUT bij git add: {output}")
        return False

    # Check of er iets te committen is
    ok, status = run_git(['status', '--short'])
    if not status.strip():
        print(f"  Geen wijzigingen — artikel bestaat al.")
        return True

    # Stap 3: Git commit
    print(f"  Stap 3/4: git commit...")
    commit_msg = f"Voeg toe: Trouwvideograaf {city_name} artikel"
    ok, output = run_git(['commit', '-m', commit_msg])
    if not ok:
        print(f"  FOUT bij git commit: {output}")
        return False

    # Stap 4: Git push
    print(f"  Stap 4/4: git push naar GitHub...")
    ok, output = run_git(['push', 'origin', 'main'])
    if not ok:
        # Probeer 'master' als 'main' niet werkt
        ok, output = run_git(['push', 'origin', 'master'])
        if not ok:
            print(f"  FOUT bij git push: {output}")
            print(f"  Artikel is lokaal opgeslagen. Push handmatig met: git push")
            return False

    print(f"  Gepubliceerd! Netlify deployt automatisch.")
    print(f"  Live op: https://blog.detrouwvideograaf.net/{filename.replace('.html', '')}")
    return True


def update_index(articles: list[dict]) -> bool:
    """
    Update de blog homepage (index.html) met alle artikelen.

    Args:
        articles: Lijst van {'city': str, 'slug': str, 'date': str, 'desc': str}
    """
    from html_template import build_index_html

    print(f"\n  Blog homepage updaten ({len(articles)} artikelen)...")

    index_html = build_index_html(articles)
    index_path = Path(BLOG_DIR) / 'index.html'

    try:
        index_path.write_text(index_html, encoding='utf-8')
    except Exception as e:
        print(f"  FOUT bij opslaan index.html: {e}")
        return False

    if not check_git_setup():
        return True

    run_git(['add', 'index.html'])
    ok, status = run_git(['status', '--short'])
    if status.strip():
        run_git(['commit', '-m', f'Update blog homepage ({len(articles)} artikelen)'])
        run_git(['push', 'origin', 'main'])
        print(f"  Homepage gepubliceerd!")

    return True
