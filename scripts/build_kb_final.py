import os
import time
import re
import uuid
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
from bs4 import BeautifulSoup
import requests
from Bio import Entrez
import html
import datetime

Entrez.email = "student.project@example.com"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "kb")
os.makedirs(DATA_PATH, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"

FAILED_URLS = []

SKIP_HEADINGS = [
    "language switcher", "share", "print", "related", "references", 
    "last reviewed", "last updated", "infographic", "rural", "learn more", 
    "help and support", "was this page helpful", "cookie", "more information",
    "navigation", "menu", "find out more"
]

def clean_text(text):
    if not text: return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    text = re.sub(r'\(([A-Z]+-)+[A-Za-z]+\):[^.]*\.', '', text)
    
    text = re.sub(r'\s+([,\.?!;:])', r'\1', text)
    text = text.replace('.,', '.').replace(', This', '. This')
    text = re.sub(r'(?:,\s*)+,', ',', text)
    
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    
    text = text.replace(' to or ', ' to ').replace(' of or ', ' of ').replace(' as or ', ' as ')
    text = text.replace(' and and ', ' and ').replace('such as ,', 'such as').replace('related to .', 'related to it.')
    
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        l = re.sub(r'[ \t]+', ' ', line).strip()
        l_lower = l.lower()
        if any(b in l_lower for b in ["last reviewed", "last updated", "was this page helpful", "health topics", "more information", "next review", "references", "find out more"]):
            continue
        if l: clean_lines.append(l)
        
    final_text = "\n".join(clean_lines)
    final_text = final_text.replace('<', '').replace('>', '')
    
    final_text = re.sub(r'(?i)next review due:.*', '', final_text)
    final_text = re.sub(r'(?i)page last reviewed:.*', '', final_text)
    final_text = re.sub(r'(?i)references.*', '', final_text)
    final_text = re.sub(r'(?i)find out more.*', '', final_text)
    
    return final_text.strip()

def chunk_text(text, min_words=60, max_words=120, hard_max=220):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    raw_sentences = []
    for line in lines:
        if line.startswith("- "):
            raw_sentences.append(line)
        else:
            sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', line) if s.strip()]
            raw_sentences.extend(sents)
            
    chunks = []
    current_chunk = ""
    
    for s in raw_sentences:
        current_words = len(current_chunk.split())
        s_words = len(s.split())
        
        if current_words + s_words > max_words and current_words >= min_words:
            chunks.append(current_chunk.strip())
            current_chunk = s + ("\n" if s.startswith("- ") else " ")
        else:
            current_chunk += s + ("\n" if s.startswith("- ") else " ")

    if current_chunk:
        chunks.append(current_chunk.strip())
        
    merged = []
    for c in chunks:
        if not merged:
            merged.append(c)
            continue
            
        c_words = len(c.split())
        first_word = c.split()[0].lower() if c.split() else ""
        starts_with_dash = c.startswith("-")
        starts_with_pronoun = first_word in ["these", "this", "they", "it", "those"]
        
        if c_words < 60 or starts_with_dash or starts_with_pronoun:
            prev = merged[-1]
            if starts_with_dash and not prev.endswith("\n"):
                merged[-1] = prev + "\n" + c
            else:
                merged[-1] = prev + " " + c
        else:
            merged.append(c)
            
    final_merged = []
    i = 0
    while i < len(merged):
        c = merged[i]
        c_words = len(c.split())
        if c_words < 60 and i + 1 < len(merged):
            merged[i+1] = c + " " + merged[i+1]
        elif c_words >= 60:
            final_merged.append(c)
        i += 1
            
    final_chunks = []
    for c in final_merged:
        c = re.sub(r'NIH: National Heart, Lung, and Blood Institute\.*', '', c).strip()
        c_lines = c.split('\n')
        short_lines = sum(1 for l in c_lines if len(l.split()) < 6)
        if len(c_lines) > 0 and short_lines > len(c_lines) / 2:
            continue
        nav_words = ["home", "back to", "skip to", "menu", "sign in"]
        c_lower = c.lower()
        if sum(1 for w in nav_words if w in c_lower) >= 2:
            continue
            
        if "child" in c_lower and "adult" not in c_lower and "everyone" not in c_lower:
            if c_lower.count("child") > 1 or c_lower.count("pediatric") > 0:
                continue
        if re.search(r'\b\d+\s*(puffs?|mg|mcg|doses?)\b', c_lower) or 'puff counts' in c_lower:
            continue
            
        if c:
            if c.startswith("- "):
                c = c.lstrip("- ").lstrip()
            final_chunks.append(c)
            
    return final_chunks

CAT_HEADING_ONLY = {
    "emergency": ["emergency", "911", "999", "severe", "attack", "er", "hospital"],
    "when_to_seek_help": ["when to", "see a doctor", "get help", "seek", "call your", "appointment"],
    "self_care": ["self-care", "lifestyle", "prevent", "vaccin", "living with", "quit smoking", "home"],
    "treatment": ["treatment", "medicine", "medication", "therapy", "inhaler", "manage", "action plan"],
    "diagnosis": ["diagnos", "test", "spirometry"],
    "risk_factors": ["risk"],
    "causes": ["cause", "trigger", "transmission", "spread"],
    "symptoms": ["symptom", "signs", "cough", "wheez", "breathless", "shortness of breath", "feel like"],
    "overview": ["what is", "overview", "about", "facts", "impact", "types", "who response"]
}

def determine_category(heading, content):
    c_lower = content.lower()
    if any(x in c_lower for x in ["call 911", "call 999", "call 112", "emergency room", "a&e"]):
        return "emergency"
    if any(x in c_lower for x in ["see a doctor", "see your doctor", "see a gp", "get medical help", "seek medical", "call your healthcare provider"]):
        return "when_to_seek_help"
        
    h_lower = heading.lower()
    for cat, kws in CAT_HEADING_ONLY.items():
        if any(k in h_lower for k in kws):
            return cat
            
    return "overview"

def format_title(heading):
    clean_head = heading.strip().replace('\n', ' ')
    if clean_head.lower() == "asthma" or not clean_head:
        clean_head = "Overview"
    return f"Asthma: {clean_head}"

KEPT_HEADINGS = []
DROPPED_HEADINGS = []

def extract_sections_from_html(html_content, source_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for tag in list(soup.find_all()):
        if not hasattr(tag, 'attrs') or tag.attrs is None: continue
        cls_list = tag.get('class') or []
        if isinstance(cls_list, str): cls_list = [cls_list]
        cls_str = " ".join(cls_list).lower()
        id_str = (tag.get('id') or "").lower()
        
        if tag.name == 'dfn':
            tag.decompose()
            continue
            
        if any(x in cls_str or x in id_str for x in ['glossary', 'tooltip', 'definition', 'popover']):
            if 'modal' in cls_str or 'modal' in id_str or 'content' in cls_str or 'popup' in cls_str or tag.name == 'div':
                tag.decompose()
            elif tag.name == 'span' and 'usa-modal' in cls_str:
                tag.decompose()
                
    main_node = soup.find('main') or soup.find('article') or soup.find('div', role='main') or soup.body or soup
    if not main_node: return {}
    
    sections = {}
    current_heading = "Overview"
    current_text = []
    
    for tag in main_node.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
        if tag.find_parent(['nav', 'header', 'footer', 'aside']):
            continue
            
        if tag.name in ['h1', 'h2', 'h3']:
            h_text = clean_text(tag.get_text(separator=' '))
            if any(skip in h_text.lower() for skip in SKIP_HEADINGS) or "child" in h_text.lower():
                DROPPED_HEADINGS.append(h_text + " (matched skip word or child)")
                current_heading = "SKIP"
                continue
                
            if current_text and current_heading != "SKIP":
                sections[current_heading] = sections.get(current_heading, "") + "\n" + "\n".join(current_text)
            current_heading = h_text
            current_text = []
        elif current_heading != "SKIP":
            if tag.name == 'p':
                p_text = clean_text(tag.get_text(separator=' '))
                if p_text: current_text.append(p_text)
            elif tag.name in ['ul', 'ol']:
                for li in tag.find_all('li', recursive=False):
                    li_text = clean_text(li.get_text(separator=' '))
                    if li_text: current_text.append("- " + li_text)
                
    if current_text and current_heading != "SKIP":
        sections[current_heading] = sections.get(current_heading, "") + "\n" + "\n".join(current_text)
        
    cleaned_sections = {}
    for k, v in sections.items():
        if any(skip in k.lower() for skip in SKIP_HEADINGS): continue
        v_clean = clean_text(v)
        if v_clean:
            cleaned_sections[clean_text(k)] = v_clean
            KEPT_HEADINGS.append(k)
            
    return cleaned_sections

def discover_nhlbi_urls():
    url = "https://www.nhlbi.nih.gov/health/asthma"
    r = requests.get(url, headers={"User-Agent": USER_AGENT})
    soup = BeautifulSoup(r.text, 'html.parser')
    links = set()
    links.add(url)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/health/asthma') and not href.endswith('children'):
            if "nhlbi.nih.gov" not in href:
                links.add("https://www.nhlbi.nih.gov" + href)
            else:
                links.add(href)
    return list(links)

def fetch_web_pages():
    results = []
    headers = {"User-Agent": USER_AGENT}
    
    URLS = [
        ("WHO", "https://www.who.int/news-room/fact-sheets/detail/asthma"),
        ("NHS", "https://www.nhs.uk/conditions/asthma/"),
        ("NHS", "https://www.nhs.uk/conditions/asthma/symptoms/"),
        ("NHS", "https://www.nhs.uk/conditions/asthma/causes/"),
        ("NHS", "https://www.nhs.uk/conditions/asthma/diagnosis/"),
        ("NHS", "https://www.nhs.uk/conditions/asthma/treatment/"),
        ("NHS", "https://www.nhs.uk/conditions/asthma/living-with/")
    ]
    
    for url in discover_nhlbi_urls():
        URLS.append(("NHLBI", url))
        
    for source_name, url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                sections = extract_sections_from_html(r.text, source_name)
                for heading, text in sections.items():
                    chunks = chunk_text(text)
                    for chunk in chunks:
                        cat = determine_category(heading, chunk)
                        title = format_title(heading)
                        results.append({
                            "chunk_id": str(uuid.uuid4()),
                            "condition": "asthma",
                            "category": cat,
                            "title": title,
                            "content": chunk,
                            "source": source_name,
                            "source_url": url,
                            "source_type": "patient_info",
                            "audience": "adult",
                            "year": "2024"
                        })
            else:
                FAILED_URLS.append(f"{url} ({r.status_code})")
        except Exception as e:
            FAILED_URLS.append(f"{url} ({str(e)})")
        time.sleep(1)
    return results

def fetch_medline_plus():
    topics = ["asthma", "asthma attack", "asthma triggers"]
    results = []
    for topic_query in topics:
        try:
            url = f"https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term={urllib.parse.quote(topic_query)}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            docs = root.findall(".//document")
            if not docs: continue
            doc = docs[0]
            url_node = doc.attrib.get('url', '')
            title_node = ""
            for el in doc.findall('content'):
                if el.attrib.get('name') == 'title': title_node = el.text
            summary_node = ""
            for el in doc.findall('content'):
                if el.attrib.get('name') == 'FullSummary': summary_node = el.text
            if summary_node:
                sections = extract_sections_from_html(summary_node, "MedlinePlus")
                if not sections:
                    sections = {"Overview": clean_text(summary_node)}
                    
                for heading, text in sections.items():
                    if heading == "Overview":
                        heading = clean_text(title_node)
                    chunks = chunk_text(text)
                    for chunk in chunks:
                        cat = determine_category(heading, chunk)
                        title = format_title(heading)
                        results.append({
                            "chunk_id": str(uuid.uuid4()),
                            "condition": "asthma",
                            "category": cat,
                            "title": clean_text(title),
                            "content": chunk,
                            "source": "MedlinePlus",
                            "source_url": url_node,
                            "source_type": "patient_info",
                            "audience": "adult",
                            "year": "2024"
                        })
        except Exception as e:
            pass
        time.sleep(1)
    return results

def fetch_pubmed():
    valid = []
    query = '"Asthma"[Majr] AND humans[MeSH Terms] AND English[lang] AND hasabstract AND (Review[ptyp] OR Guideline[ptyp] OR "Practice Guideline"[ptyp]) AND ("2021/01/01"[PDat] : "3000"[PDat]) AND (diagnosis OR management OR emergency OR risk)'
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=5, sort="date")
        record = Entrez.read(handle)
        handle.close()
        id_list = record["IdList"]
        if not id_list: return valid
        handle = Entrez.efetch(db="pubmed", id=id_list, retmode="xml")
        papers = Entrez.read(handle)
        handle.close()
        
        for paper in papers['PubmedArticle']:
            try:
                title = clean_text(paper['MedlineCitation']['Article']['ArticleTitle'])
                abstract_text = ""
                if 'Abstract' in paper['MedlineCitation']['Article']:
                    abs_list = paper['MedlineCitation']['Article']['Abstract']['AbstractText']
                    abstract_text = clean_text(" ".join([str(a) for a in abs_list]))
                if not abstract_text: continue
                
                pmid = str(paper['MedlineCitation']['PMID'])
                year = "2023"
                try:
                    pub_date = paper['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']
                    if 'Year' in pub_date: year = pub_date['Year']
                    elif 'MedlineDate' in pub_date: year = pub_date['MedlineDate'][:4]
                except: pass
                
                cat = determine_category(title, abstract_text)
                
                chunks = chunk_text(abstract_text)
                for chunk in chunks:
                    valid.append({
                        "chunk_id": str(uuid.uuid4()),
                        "condition": "asthma",
                        "category": cat,
                        "title": format_title(title),
                        "content": chunk,
                        "source": "PubMed",
                        "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "source_type": "research",
                        "audience": "adult",
                        "year": year
                    })
            except: pass
    except: pass
    return valid

def main():
    data = []
    data.extend(fetch_web_pages())
    data.extend(fetch_medline_plus())
    data.extend(fetch_pubmed())
    
    seen = set()
    deduped = []
    for row in data:
        text_hash = hash(row["content"][:100])
        if text_hash not in seen:
            seen.add(text_hash)
            deduped.append(row)
            
    df = pd.DataFrame(deduped)
    csv_path = os.path.join(DATA_PATH, "kb_final.csv")
    df.to_csv(csv_path, index=False)
    
    df_read = pd.read_csv(csv_path)
    
    abs_path = os.path.abspath(csv_path)
    row_count = len(df_read)
    mtime = os.path.getmtime(csv_path)
    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"{abs_path}")
    print(f"{row_count}")
    print(f"{mtime_str}")
    
    print("\nSource Counts:")
    for k, v in df_read['source'].value_counts().items():
        print(f"{k}: {v}")
        
    print("\nCategory Counts:")
    for k, v in df_read['category'].value_counts().items():
        print(f"{k}: {v}")
        
    c_content = df_read['content']
    word_counts = c_content.str.split().str.len()
    
    print("\n--- STATS ---")
    print((word_counts > 220).sum())
    print((word_counts < 60).sum())
    print(c_content.str.contains(r'[a-z][A-Z][a-z]').sum())
    print(c_content.str.contains(r'- -').sum())
    print(c_content.str.contains(r'(?i)next review').sum())
    print(c_content.str.contains(r'(?i)references').sum())
    print(df_read['title'].str.contains(chr(10)).sum())
    print(c_content.str.contains('999').sum())
    print(c_content.str.contains('111').sum())
    print(c_content.str.contains('A&E').sum())
    
    print("\nFailed URLs:")
    for url in FAILED_URLS:
        print(url)
        
    print("\nDropped Headings:")
    for h in set(DROPPED_HEADINGS):
        print(f"{h}")
        
    print("\nKept Headings:")
    for h in set(KEPT_HEADINGS):
        print(f"{h}")

if __name__ == "__main__":
    main()
