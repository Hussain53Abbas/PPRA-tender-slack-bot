import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
if not SLACK_WEBHOOK_URL:
    raise Exception("SLACK_WEBHOOK_URL not set in environment variables")

PPRA_URL = 'https://www.ppra.org.pk/daily_tenders'
KEYWORDS = [
    'safety', 'safety equipment', 'ppe', 'masks', 'gloves', 'helmets', 'boots', 'vests', 'respirators',
    'goggles', 'ear plugs', 'face shield', 'fire extinguisher', 'coveralls', 'high visibility',
    'hats', 'hammers', 'diamond blade', 'diamond cup', 'hand tools', 'wrenches', 'screwdrivers',
    'pliers', 'chisels', 'saws', 'cutting disc', 'drill bits', 'grinders', 'toolkits', 'impact driver'
]

def fetch_ppra_data():
    response = requests.get(PPRA_URL)
    response.encoding = 'utf-8'
    if response.status_code != 200:
        raise Exception("Failed to fetch PPRA website")
    return response.text

def parse_tenders(html):
    soup = BeautifulSoup(html, 'html.parser')
    tenders = []

    for row in soup.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) < 5:
            continue
        tender_text = ' '.join(cell.get_text(strip=True).lower() for cell in cells)

        if any(keyword in tender_text for keyword in KEYWORDS):
            tender = {
                'date': cells[0].text.strip(),
                'organization': cells[1].text.strip(),
                'details': cells[2].text.strip(),
                'location': cells[3].text.strip(),
                'link': cells[4].find('a')['href'] if cells[4].find('a') else 'N/A'
            }
            tenders.append(tender)
    return tenders

def send_to_slack(tenders):
    if not tenders:
        message = { "text": "📢 No relevant safety or tool tenders found today." }
        requests.post(SLACK_WEBHOOK_URL, data=json.dumps(message))
        return

    blocks = [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*🛠️ PPRA Tender Alerts (Filtered)*"}
    }]

    for t in tenders:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*📅 Date:* {t['date']}\n"
                    f"*🏢 Org:* {t['organization']}\n"
                    f"*📝 Details:* {t['details']}\n"
                    f"*📍 Location:* {t['location']}\n"
                    f"<{t['link']}|🔗 View Tender>"
                )
            }
        })
        blocks.append({ "type": "divider" })

    payload = {
        "blocks": blocks
    }
    requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))

def main():
    print(f"Running tender scrape at {datetime.datetime.now()}")
    html = fetch_ppra_data()
    tenders = parse_tenders(html)
    send_to_slack(tenders)

if __name__ == '__main__':
    main()
