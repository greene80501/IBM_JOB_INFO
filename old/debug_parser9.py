from bs4 import BeautifulSoup

with open('job_detail.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
root = soup.find("main") or soup

fields = root.find_all("div", class_="article__content__view__field")
headers = root.find_all("summary", class_="article__header")
elems = sorted(fields + headers, key=lambda e: e.sourceline if e.sourceline else 0)

current_section = ""
current_field = ""

for elem in elems:
    if elem.name == "summary" and "article__header" in (elem.get("class") or []):
        h3 = elem.find("h3")
        current_section = h3.get_text(strip=True).upper() if h3 else ""
        print(f'[HEADER] {current_section}')
        continue

    label_div = elem.find("div", class_="article__content__view__field__label")
    value_div = elem.find("div", class_="article__content__view__field__value")

    if label_div and value_div:
        raw_label = label_div.get_text(separator=" ", strip=True).lower()
        current_field = raw_label
        print(f'  [LABELED] {raw_label}')
    elif value_div:
        raw_value = value_div.get_text(separator="\n", strip=True)
        cleaned = raw_value.strip()
        if not cleaned:
            print('  [UNLABELED] EMPTY - skipped')
            continue
        
        section = current_section.upper()
        lower_val = cleaned.lower()
        
        if current_field == "preferred technical and professional experience":
            key = "about_business"
        elif section == "ABOUT BUSINESS UNIT":
            key = "about_business"
        elif section == "YOUR LIFE @ IBM":
            key = "life_at_ibm"
        elif section == "ABOUT IBM":
            if "equal-opportunity employer" in lower_val or "equal opportunity" in lower_val:
                key = "equal_opportunity"
            else:
                key = "about_ibm"
        elif section == "OTHER RELEVANT JOB DETAILS":
            if "benefits program" in lower_val or "healthcare benefits" in lower_val:
                key = "benefits"
            elif "visa sponsorship" in lower_val:
                key = "visa_policy"
            elif "compensation range" in lower_val or "salary will vary" in lower_val:
                key = "compensation_policy"
            else:
                key = "other_notes"
        else:
            key = "extra_content"
        
        print(f'  [UNLABELED] key={key} text={cleaned[:40]}...')
