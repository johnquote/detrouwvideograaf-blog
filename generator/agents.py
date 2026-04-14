"""
Multi-Agent SEO Blog Generator voor De Trouwvideograaf
Gebaseerd op:
- Multi-Agent-SEO-Blog-Generator (pipeline structuur)
- seo-geo-claude-skills (CORE-EEAT framework voor kwaliteit)
- Claude Haiku API (goedkoop, snel, ~€0.002/artikel)
"""

import anthropic
import time
from config import CLAUDE_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Interne links naar detrouwvideograaf.net
INTERNAL_LINKS = {
    "offerte":    "https://www.detrouwvideograaf.net/#contact",
    "pakketten":  "https://www.detrouwvideograaf.net/#pakketten",
    "calculator": "https://www.detrouwvideograaf.net/#calculator",
    "portfolio":  "https://www.detrouwvideograaf.net/#portfolio",
    "over ons":   "https://www.detrouwvideograaf.net/#over-ons",
}


def call_claude(prompt: str, max_tokens: int = 2000) -> str:
    """Roep Claude API aan met retry logica."""
    for attempt in range(3):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"  Claude API fout (poging {attempt + 1}/3): {e}")
            time.sleep(2)
    raise Exception("Claude API mislukt na 3 pogingen")


# ─── AGENT 0: KEYWORD RESEARCH ────────────────────────────────────────────────

def agent_keyword_research(city: dict) -> dict:
    """
    Agent 0: Zoekwoordenonderzoek — wat googelen mensen ook?
    Genereert gerelateerde zoekopdrachten, 'people also ask' vragen
    en long-tail keywords voor het artikel.
    """
    print(f"  [Agent 0] Keyword research voor {city['keyword']}...")

    prompt = f"""Je bent een Nederlandse SEO-specialist gespecialiseerd in trouwbranch.
Mensen zoeken op "{city['keyword']}" in Google.

Genereer een lijst van GERELATEERDE zoekopdrachten die mensen ook doen rondom dit onderwerp.
Denk aan: variaties, vragen, long-tail keywords, gerelateerde onderwerpen.

Geef exact dit formaat terug (elke regel met het label en |||):

LONG_TAIL|||trouwvideograaf {city['city']} prijzen
LONG_TAIL|||trouwfilm {city['city']}
LONG_TAIL|||videograaf bruiloft {city['city']}
VRAAG|||Wat kost een trouwvideograaf in {city['city']}?
VRAAG|||Hoe kies ik een trouwvideograaf in {city['city']}?
VRAAG|||Wat is het verschil tussen een fotograaf en videograaf?
VRAAG|||Wanneer moet ik een trouwvideograaf boeken in {city['city']}?
VRAAG|||Welke trouwlocaties zijn er in {city['city']}?
GERELATEERD|||bruiloft {city['city']}
GERELATEERD|||trouwlocatie {city['city']}
GERELATEERD|||trouwfoto {city['city']}

Geef minimaal:
- 5 LONG_TAIL zoektermen (variaties op het hoofdkeyword)
- 6 VRAAG vragen (wat mensen echt googelen — "people also ask")
- 4 GERELATEERD zoektermen (bredere context)

Wees specifiek voor {city['city']} en de trouwbranche in Nederland.
"""
    result = call_claude(prompt, max_tokens=800)

    keywords = {"long_tail": [], "vragen": [], "gerelateerd": []}
    for line in result.strip().split('\n'):
        if '|||' in line:
            key, value = line.split('|||', 1)
            key = key.strip()
            value = value.strip()
            if key == 'LONG_TAIL':
                keywords["long_tail"].append(value)
            elif key == 'VRAAG':
                keywords["vragen"].append(value)
            elif key == 'GERELATEERD':
                keywords["gerelateerd"].append(value)

    total = len(keywords["long_tail"]) + len(keywords["vragen"]) + len(keywords["gerelateerd"])
    print(f"  Gevonden: {len(keywords['long_tail'])} long-tail, {len(keywords['vragen'])} vragen, {len(keywords['gerelateerd'])} gerelateerd")
    return keywords


# ─── AGENT 1: RESEARCH ────────────────────────────────────────────────────────

def agent_research(city: dict) -> str:
    """
    Agent 1: Verzamel lokale kennis over de stad.
    """
    print(f"  [Agent 1] Lokale research voor {city['city']}...")

    prompt = f"""Je bent een Nederlandse trouwvideograaf die gespecialiseerd is in lokale bruiloften.
Schrijf een gedetailleerde lokale research briefing voor {city['city']}, {city['province']}.

STAD INFO:
- Karakter: {city['character']}
- Kerken: {', '.join(city['churches'])}
- Trouwlocaties: {', '.join(city['venues'])}
- Regio: {city['region']}

Schrijf een research briefing met:
1. WAT MAAKT {city['city'].upper()} UNIEK voor trouwen? (tradities, sfeer, typische elementen)
2. PRAKTISCHE INFO voor het trouwen in {city['city']}:
   - Typisch tijdschema trouwdag
   - Beste seizoenen/tijden
   - Typische locatiecombinaties (kerk + feestlocatie)
3. LOKALE DETAILS die een trouwvideograaf zou kennen:
   - Mooiste filmlocaties in {city['city']}
   - Lokale tradities of gebruiken
   - Wat bezoekers verrast aan {city['city']}
4. FOTO/FILM TIPS specifiek voor {city['city']}:
   - Beste lichtomstandigheden
   - Unieke filmhoeken of locaties

Schrijf in het Nederlands. Wees specifiek en accuraat — geen generieke informatie.
"""
    return call_claude(prompt, max_tokens=1500)


# ─── AGENT 2: OUTLINE ─────────────────────────────────────────────────────────

def agent_outline(city: dict, research: str, keywords: dict) -> str:
    """
    Agent 2: Maak een SEO-geoptimaliseerde outline op basis van keywords + research.
    """
    print(f"  [Agent 2] Outline maken voor {city['keyword']}...")

    vragen_str = '\n'.join([f"- {v}" for v in keywords.get("vragen", [])])
    long_tail_str = ', '.join(keywords.get("long_tail", []))

    prompt = f"""Je bent een SEO-expert voor Nederlandse lokale zoekopdrachten.
Maak een gedetailleerde artikel outline voor het keyword: "{city['keyword']}"

RESEARCH BRIEFING:
{research}

GERELATEERDE ZOEKOPDRACHTEN (verwerk deze in het artikel):
Long-tail keywords: {long_tail_str}

VRAGEN DIE MENSEN OOK GOOGELEN (verwerk als FAQ of secties):
{vragen_str}

INTERNE LINKS BESCHIKBAAR (verwerk 3-4 keer natuurlijk in het artikel):
- Prijzen/offerte: https://www.detrouwvideograaf.net/#contact
- Pakketten bekijken: https://www.detrouwvideograaf.net/#pakketten
- Prijscalculator: https://www.detrouwvideograaf.net/#calculator
- Portfolio / voorbeeldfilms: https://www.detrouwvideograaf.net/#portfolio

CORE-EEAT EISEN (VERPLICHT):
- C02: Directe answer in eerste 150 woorden
- C09: Minimaal 5 FAQ vragen (uit de lijst hierboven!)
- O01: Correcte H1→H2→H3 structuur
- O08: Inhoudsopgave
- E06: Dek vragen die concurrenten NIET beantwoorden

Maak een outline met:
1. Meta title (max 60 tekens)
2. Meta description (max 155 tekens)
3. H1 titel
4. Inleiding (directe answer + interne link naar pakketten of calculator)
5. H2 secties (6-8 secties) — verwerk long-tail keywords als H2/H3 titels
6. FAQ sectie (gebruik de vragen uit de lijst hierboven)
7. Call-to-action (link naar offerte)

Schrijf in het Nederlands.
"""
    return call_claude(prompt, max_tokens=1500)


# ─── AGENT 3: SCHRIJF ─────────────────────────────────────────────────────────

def agent_write(city: dict, research: str, outline: str, keywords: dict) -> str:
    """
    Agent 3: Schrijf de volledige artikel tekst met foto-plaatsingen en interne links.
    """
    print(f"  [Agent 3] Artikel schrijven voor {city['city']}...")

    # Bouw foto instructies op
    images = city.get("inline_images", [])
    img_instructions = ""
    if images:
        img_instructions = "\nFOTO PLAATSING (gebruik deze exact zo in de tekst):\n"
        for i, img in enumerate(images):
            img_instructions += f"- Na sectie {i+2}: voeg toe [FOTO_{i+1}] als placeholder\n"
        img_instructions += "(De foto's worden automatisch ingevuld in de HTML)\n"

    vragen_str = '\n'.join([f"- {v}" for v in keywords.get("vragen", [])])

    prompt = f"""Je bent De Trouwvideograaf, een professionele videograaf gebaseerd in Nederland.
Je schrijft een artikel voor je blog over trouwen in {city['city']}.

RESEARCH:
{research}

OUTLINE:
{outline}

SCHRIJFINSTRUCTIES:
- Schrijf in het Nederlands, informeel maar professioneel (je/jij aanspreekvorm)
- Minimaal 1500 woorden
- Toon: warm, persoonlijk, deskundig
- Gebruik ECHTE lokale details (namen van kerken, locaties, straten)
- GEEN nep-testimonials of verzonnen citaten
- GEEN clichés zoals "de mooiste dag van je leven"

INTERNE LINKS (verwerk dit 3-4 keer NATUURLIJK in de tekst):
- Schrijf bijv: "Bekijk onze [trouwpakketten](https://www.detrouwvideograaf.net/#pakketten)"
- Of: "Bereken direct je prijs met onze [prijscalculator](https://www.detrouwvideograaf.net/#calculator)"
- Of: "Vraag een [gratis offerte aan](https://www.detrouwvideograaf.net/#contact)"
- Of: "Bekijk voorbeeldfilms in ons [portfolio](https://www.detrouwvideograaf.net/#portfolio)"
Gebruik VERSCHILLENDE links door het artikel heen, niet steeds dezelfde.

FOTO PLAATSING:
{img_instructions if img_instructions else "Geen inline foto's beschikbaar voor deze stad."}

FAQ SECTIE (VERPLICHT — gebruik deze echte Google-zoekvragen):
{vragen_str}
Schrijf een ## Veelgestelde vragen sectie met H3 per vraag en een duidelijk antwoord.

STRUCTUUR:
1. Open met directe lokale hook (eerste 150 woorden = direct antwoord)
2. Volg de outline met H2/H3 headers
3. Foto placeholders [FOTO_1], [FOTO_2] op logische plekken
4. FAQ sectie met echte vragen
5. Eindig met call-to-action + link naar offerte

GEEF ALLEEN DE ARTIKEL TEKST TERUG — geen uitleg, geen metadata.
Gebruik Markdown headers (## voor H2, ### voor H3).
"""
    return call_claude(prompt, max_tokens=3500)


# ─── AGENT 4: SEO OPTIMALISATIE ───────────────────────────────────────────────

def agent_seo_optimize(city: dict, content: str) -> dict:
    """
    Agent 4: Optimaliseer voor SEO en genereer meta-data.
    """
    print(f"  [Agent 4] SEO optimalisatie...")

    prompt = f"""Je bent een Nederlandse SEO-specialist.
Analyseer dit artikel over "{city['keyword']}" en geef SEO meta-data.

ARTIKEL (begin):
{content[:1000]}

Geef exact dit formaat (gebruik ||| als separator):

META_TITLE|||[max 60 tekens, bevat '{city['keyword']}']
META_DESC|||[max 155 tekens, lokaal + overtuigend, met stad naam]
FOCUS_KEYWORD|||[het primaire keyword]
SECONDARY_KEYWORDS|||[5 gerelateerde keywords, komma-gescheiden]
READING_TIME|||[schatting in minuten, bijv. "7 min leestijd"]
"""
    result = call_claude(prompt, max_tokens=400)

    meta = {
        "meta_title": f"Trouwvideograaf {city['city']} | De Trouwvideograaf",
        "meta_desc": f"Professionele trouwvideograaf in {city['city']}. Bekijk pakketten en vraag een offerte aan.",
        "focus_keyword": city['keyword'],
        "secondary_keywords": [],
        "reading_time": "6 min leestijd",
        "slug": city['slug'],
    }

    for line in result.strip().split('\n'):
        if '|||' in line:
            key, value = line.split('|||', 1)
            key = key.strip()
            value = value.strip()
            if key == 'META_TITLE':
                meta['meta_title'] = value
            elif key == 'META_DESC':
                meta['meta_desc'] = value
            elif key == 'FOCUS_KEYWORD':
                meta['focus_keyword'] = value
            elif key == 'SECONDARY_KEYWORDS':
                meta['secondary_keywords'] = [k.strip() for k in value.split(',')]
            elif key == 'READING_TIME':
                meta['reading_time'] = value

    return meta


# ─── AGENT 5: KWALITEITSCHECK ─────────────────────────────────────────────────

def agent_quality_check(city: dict, content: str) -> tuple:
    """
    Agent 5: Check kwaliteit op basis van CORE-EEAT benchmark.
    """
    print(f"  [Agent 5] CORE-EEAT kwaliteitscheck...")

    prompt = f"""Je bent een SEO content auditor.
Beoordeel dit artikel over "{city['keyword']}" snel:

ARTIKEL (eerste 1500 woorden):
{content[:1500]}

Check:
1. Bevat eerste 150 woorden een direct antwoord? (ja/nee)
2. Zijn er FAQ vragen aanwezig? (ja/nee)
3. Zijn er interne links naar detrouwvideograaf.net? (ja/nee)
4. Zijn foto-placeholders [FOTO_x] aanwezig? (ja/nee)
5. Is er een persoonlijke toon? (ja/nee)

Formaat:
SCORE|||[getal 1-10]
VERBETERPUNT|||[verbeterpunt indien nodig]
"""
    result = call_claude(prompt, max_tokens=300)

    score = 7
    improvements = []

    for line in result.strip().split('\n'):
        if '|||' in line:
            key, value = line.split('|||', 1)
            key = key.strip()
            value = value.strip()
            if key == 'SCORE':
                try:
                    score = int(value)
                except:
                    pass
            elif key == 'VERBETERPUNT':
                improvements.append(value)

    print(f"  CORE-EEAT Score: {score}/10")
    return content, improvements


# ─── HOOFDPIPELINE ────────────────────────────────────────────────────────────

def run_pipeline(city: dict) -> tuple:
    """
    Voer de volledige multi-agent pipeline uit voor een stad.
    Returns: (artikel_tekst, meta_data)
    """
    print(f"\nGenereer artikel voor: {city['keyword']}")
    print("=" * 50)

    # Agent 0: Keyword research
    keywords = agent_keyword_research(city)

    # Agent 1: Research
    research = agent_research(city)

    # Agent 2: Outline (met keywords)
    outline = agent_outline(city, research, keywords)

    # Agent 3: Schrijf (met foto-placeholders + interne links)
    content = agent_write(city, research, outline, keywords)

    # Agent 4: SEO optimalisatie
    meta = agent_seo_optimize(city, content)
    meta['keywords_data'] = keywords

    # Agent 5: Kwaliteitscheck
    content, improvements = agent_quality_check(city, content)

    print(f"\n  Artikel klaar! ({len(content.split())} woorden)")
    return content, meta
