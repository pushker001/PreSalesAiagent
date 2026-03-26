import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def collect_lead_intelligence(data):
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
    """Advanced website scraping using Playwright or fallback to requests"""
    if PLAYWRIGHT_AVAILABLE:
        return scrape_with_playwright(url)
    else:
        return scrape_with_requests(url)

def scrape_with_playwright(url):
    """Advanced scraping with Playwright (handles JS, SPAs)"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set realistic headers
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Navigate and wait for content
            page.goto(url, wait_until='networkidle')
            page.wait_for_timeout(2000)  # Wait for JS to load
            
            # Extract comprehensive data
            data = page.evaluate("""
                () => {
                    // Basic metadata
                    const title = document.title || '';
                    const description = document.querySelector('meta[name="description"]')?.content || '';
                    
                    // Headings
                    const h1s = Array.from(document.querySelectorAll('h1')).slice(0, 3).map(h => h.textContent.trim());
                    const h2s = Array.from(document.querySelectorAll('h2')).slice(0, 5).map(h => h.textContent.trim());
                    
                    // Services/Programs
                    const serviceKeywords = ['service', 'program', 'coaching', 'training', 'course'];
                    const services = [];
                    serviceKeywords.forEach(keyword => {
                        const elements = Array.from(document.querySelectorAll('*')).filter(el => 
                            el.textContent.toLowerCase().includes(keyword) && el.textContent.length < 200
                        );
                        services.push(...elements.slice(0, 2).map(el => el.textContent.trim().substring(0, 100)));
                    });
                    
                    // Call to actions
                    const ctaKeywords = ['book', 'call', 'contact', 'start', 'schedule', 'get started', 'learn more', 'sign up'];
                    const ctas = Array.from(document.querySelectorAll('a, button')).filter(el => {
                        const text = el.textContent.toLowerCase();
                        return ctaKeywords.some(keyword => text.includes(keyword));
                    }).slice(0, 5).map(el => el.textContent.trim());
                    
                    // Testimonials
                    const testimonials = Array.from(document.querySelectorAll('[class*="testimonial"], [class*="review"], blockquote'))
                        .slice(0, 3).map(el => el.textContent.trim().substring(0, 200));
                    
                    // Pricing
                    const pricingElements = Array.from(document.querySelectorAll('*')).filter(el => {
                        const text = el.textContent;
                        return /[$€£]\\d+/.test(text) && ['price', 'cost', 'fee', 'investment'].some(word => 
                            text.toLowerCase().includes(word)
                        );
                    });
                    const pricing = pricingElements.slice(0, 3).map(el => el.textContent.trim().substring(0, 100));
                    
                    // About section - use meta description first, then targeted selectors
                    const metaDesc = document.querySelector('meta[name="description"]')?.content || '';
                    let aboutSection = metaDesc;
                    if (!aboutSection) {
                        const aboutEl = document.querySelector(
                            '[class*="about"], [id*="about"], [class*="mission"], [class*="hero"] p, main p'
                        );
                        if (aboutEl) aboutSection = aboutEl.textContent.trim().substring(0, 500);
                    }
                    
                    return {
                        title,
                        description,
                        h1_headings: h1s,
                        h2_headings: h2s,
                        services: [...new Set(services)].slice(0, 5),
                        call_to_actions: [...new Set(ctas)],
                        testimonials: testimonials.filter(t => t.length > 20),
                        pricing_info: [...new Set(pricing)],
                        about_snippet: aboutSection
                    };
                }
            """)
            
            # Find and scrape important pages
            links = page.evaluate("""
                () => {
                    const keywords = ['about', 'services', 'contact', 'team', 'coaching', 'programs'];
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.filter(link => {
                        const text = link.textContent.toLowerCase();
                        const href = link.href.toLowerCase();
                        return keywords.some(keyword => text.includes(keyword) || href.includes(keyword));
                    }).slice(0, 3).map(link => link.href);
                }
            """)
            
            # Scrape additional pages
            additional_data = []
            for link in links:
                if link and link != url:
                    try:
                        page.goto(link, wait_until='networkidle')
                        page.wait_for_timeout(1000)
                        
                        page_data = page.evaluate("""
                            () => {
                                const services = Array.from(document.querySelectorAll('*')).filter(el => 
                                    ['service', 'program', 'coaching'].some(keyword => 
                                        el.textContent.toLowerCase().includes(keyword)
                                    ) && el.textContent.length < 200
                                ).slice(0, 3).map(el => el.textContent.trim().substring(0, 100));
                                
                                const testimonials = Array.from(document.querySelectorAll('[class*="testimonial"], [class*="review"], blockquote'))
                                    .slice(0, 2).map(el => el.textContent.trim().substring(0, 200));
                                
                                return { services, testimonials };
                            }
                        """)
                        
                        additional_data.append(page_data)
                    except Exception as e:
                        print(f"Failed to scrape additional page: {str(e)}")
                        continue
            
            browser.close()
            
            # Combine all data
            final_data = data.copy()
            final_data['url'] = url
            final_data['pages_scraped'] = len(additional_data) + 1
            final_data['comprehensive_data'] = True
            
            # Merge additional data
            for extra in additional_data:
                if 'services' in extra:
                    final_data['services'].extend(extra['services'])
                if 'testimonials' in extra:
                    final_data['testimonials'].extend(extra['testimonials'])
            
            # Remove duplicates
            final_data['services'] = list(set(final_data['services']))[:8]
            final_data['testimonials'] = list(set(final_data['testimonials']))[:5]
            
            return final_data
            
    except Exception as e:
        return {"error": str(e), "url": url}

def scrape_with_requests(url):
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
    except Exception as e:
        print(f"Failed to find important pages: {str(e)}")
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

        # Remove script/style tags before any extraction
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # About section - meta description first, then clean HTML elements
        about_section = ""
        if meta_desc and meta_desc.get("content"):
            about_section = meta_desc.get("content")[:500]
        else:
            for tag in soup.find_all(["p", "h1", "h2", "section"]):
                text = tag.get_text(strip=True)
                if 40 < len(text) < 600:
                    about_section = text[:500]
                    break

        # Services/Programs
        services = []
        for keyword in ["service", "program", "coaching", "training"]:
            elements = soup.find_all(string=lambda t: t and keyword.lower() in t.lower())
            services.extend([elem.strip()[:100] for elem in elements[:3]])

        # Call to action (CTA)
        cta_texts = []
        for btn in soup.find_all("a"):
            text = btn.text.strip().lower()
            if any(x in text for x in ["book", "call", "contact", "start", "schedule", "get started", "learn more"]):
                cta_texts.append(btn.text.strip())

        # Extract testimonials/reviews
        testimonials = []
        for elem in soup.find_all(['blockquote', 'div'], class_=lambda x: x and any(word in str(x).lower() for word in ['testimonial', 'review', 'feedback'])):
            text = elem.get_text(strip=True)
            if len(text) > 20:
                testimonials.append(text[:200])

        # Pricing indicators
        pricing_info = []
        import re
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