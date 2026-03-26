import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re

def collect_lead_intelligence(data):
    """Web search + scraping for lead intelligence"""
    intelligence = {
        "client_name": data.client_name,
        "linkedin_data": scrape_linkedin(data.linkedin_url) if data.linkedin_url else None,
        "website_data": scrape_website(data.website_url) if data.website_url else None,
        "client_type": data.client_type,
        "revenue_stage": data.revenue_stage,
        "lead_source": data.lead_source,
        "lead_temperature": data.lead_temperature,
        "problem_mentioned": data.problem_mentioned,
        "coach_offer_price_range": data.coach_offer_price_range
    }
    return intelligence

def scrape_linkedin(url):
    """Basic LinkedIn scraping (limited due to anti-bot measures)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('title')
        return {
            "title": title.text if title else "LinkedIn Profile",
            "url": url,
            "accessible": response.status_code == 200
        }
    except Exception as e:
        return {"error": str(e), "url": url}

def scrape_website(url):
    """Advanced website scraping for business intelligence"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Scrape main page
        main_data = scrape_single_page(url, headers)
        if "error" in main_data:
            return main_data
        
        # Find important pages to scrape
        important_pages = find_important_pages(url, headers)
        
        # Scrape additional pages (limit to 3 for performance)
        additional_data = []
        for page_url in important_pages[:3]:
            time.sleep(1)  # Rate limiting
            page_data = scrape_single_page(page_url, headers)
            if "error" not in page_data:
                additional_data.append(page_data)
        
        # Combine all data
        combined_data = combine_scraped_data(main_data, additional_data)
        return combined_data
        
    except Exception as e:
        return {"error": str(e), "url": url}

def find_important_pages(base_url, headers):
    """Find important pages like About, Services, Contact"""
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        important_pages = set()
        keywords = ['about', 'services', 'contact', 'team', 'coaching', 'programs']
        
        # Find links containing important keywords
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.text.lower().strip()
            
            if any(keyword in text for keyword in keywords) or any(keyword in href.lower() for keyword in keywords):
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc == urlparse(base_url).netloc:  # Same domain only
                    important_pages.add(full_url)
        
        return list(important_pages)
    except:
        return []

def scrape_single_page(url, headers):
    """Scrape a single page for content"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Basic metadata
        title = soup.find('title')
        meta_desc = soup.find('meta', attrs={'name': 'description'})

        # Headings
        h1_tags = [h1.text.strip() for h1 in soup.find_all('h1')[:3]]
        h2_tags = [h2.text.strip() for h2 in soup.find_all('h2')[:5]]

        # About section (best guess)
        about_section = ""
        for keyword in ["about", "who we are", "our story", "mission", "vision"]:
            section = soup.find(string=lambda t: t and keyword.lower() in t.lower())
            if section:
                about_section = section.strip()[:500]  # Limit length
                break

        # Services/Programs
        services = []
        for keyword in ["service", "program", "coaching", "training", "course"]:
            elements = soup.find_all(string=lambda t: t and keyword.lower() in t.lower())
            services.extend([elem.strip()[:100] for elem in elements[:3]])

        # Call to action (CTA)
        cta_texts = []
        for btn in soup.find_all("a"):
            text = btn.text.strip().lower()
            if any(x in text for x in ["book", "call", "contact", "start", "schedule", "get started", "learn more", "sign up"]):
                cta_texts.append(btn.text.strip())

        # Extract testimonials/reviews
        testimonials = []
        for elem in soup.find_all(['blockquote', 'div'], class_=lambda x: x and any(word in str(x).lower() for word in ['testimonial', 'review', 'feedback'])):
            text = elem.get_text(strip=True)
            if len(text) > 20:
                testimonials.append(text[:200])

        # Pricing indicators
        pricing_info = []
        for elem in soup.find_all(string=lambda t: t and re.search(r'[$€£]\d+', t)):
            if any(word in elem.lower() for word in ['price', 'cost', 'fee', 'investment']):
                pricing_info.append(elem.strip()[:100])

        return {
            "url": url,
            "title": title.text if title else "",
            "description": meta_desc.get('content') if meta_desc else "",
            "h1_headings": h1_tags,
            "h2_headings": h2_tags,
            "about_snippet": about_section,
            "services": services[:5],
            "call_to_actions": cta_texts[:5],
            "testimonials": testimonials[:3],
            "pricing_info": pricing_info[:3]
        }

    except Exception as e:
        return {"error": str(e), "url": url}

def combine_scraped_data(main_data, additional_data):
    """Combine data from multiple pages"""
    combined = main_data.copy()
    
    # Merge lists from additional pages
    for data in additional_data:
        for key in ['h1_headings', 'h2_headings', 'services', 'call_to_actions', 'testimonials', 'pricing_info']:
            if key in data and key in combined:
                combined[key].extend(data[key])
                combined[key] = list(set(combined[key]))[:10]  # Remove duplicates, limit size
        
        # Combine about sections
        if data.get('about_snippet') and len(data['about_snippet']) > len(combined.get('about_snippet', '')):
            combined['about_snippet'] = data['about_snippet']
    
    # Add summary
    combined['pages_scraped'] = len(additional_data) + 1
    combined['comprehensive_data'] = True
    
    return combined