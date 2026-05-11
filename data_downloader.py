import requests
import os
import time
from html.parser import HTMLParser

###Use this script to download data programatically from the Bureau Of Transportation Statistics

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://transtats.bts.gov/DL_SelectFields.aspx"
PARAMS = "?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr"


###The fields I would like my dataset to include
EXPLICIT_FIELDS = [ 
    "YEAR", "QUARTER", "MONTH", "DAY_OF_MONTH", "DAY_OF_WEEK",
    "OP_UNIQUE_CARRIER",
    "ORIGIN_AIRPORT_ID", "ORIGIN_AIRPORT_SEQ_ID", "ORIGIN_CITY_MARKET_ID",
    "ORIGIN", "ORIGIN_STATE_NM", "ORIGIN_WAC",
    "DEST_AIRPORT_ID", "DEST_AIRPORT_SEQ_ID", "DEST_CITY_MARKET_ID",
    "DEST", "DEST_CITY_NAME", "DEST_STATE_NM", "DEST_WAC",
    "CRS_DEP_TIME", "DEP_TIME", "DEP_DELAY", "DEP_DEL15",
    "DEP_DELAY_GROUP", "DEP_TIME_BLK", "TAXI_OUT", "WHEELS_OFF",
    "WHEELS_ON", "TAXI_IN", "CRS_ARR_TIME", "ARR_TIME", "ARR_DELAY",
    "ARR_DEL15", "ARR_DELAY_GROUP", "ARR_TIME_BLK",
    "CANCELLED", "CANCELLATION_CODE", "DIVERTED",
    "CRS_ELAPSED_TIME", "ACTUAL_ELAPSED_TIME", "AIR_TIME",
    "FLIGHTS", "DISTANCE", "DISTANCE_GROUP",
    "CARRIER_DELAY", "WEATHER_DELAY", "NAS_DELAY", "SECURITY_DELAY", "LATE_AIRCRAFT_DELAY",
]


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) Gecko/20100101 Firefox/150.0",
    "Referer": BASE_URL + PARAMS,
    "Origin": "https://transtats.bts.gov",
    "Content-Type": "application/x-www-form-urlencoded",
}


class ViewStateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            attrs = dict(attrs)
            name = attrs.get("name", "")
            if name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
                self.fields[name] = attrs.get("value", "")

def get_viewstate(session):
    r = session.get(BASE_URL + PARAMS, headers=HEADERS)
    parser = ViewStateParser()
    parser.feed(r.text)
    return parser.fields

session = requests.Session()

for year in range(2002, 2026): ###This will take a long time to download, consider reducing the year range if you are fine with less data.
    for month in range(1, 13):
        filename = f"{OUTPUT_DIR}/On_Time_{year}_{month:02d}.zip"
        if os.path.exists(filename): #Skip existing files
            print(f"Skipping {year}-{month:02d} (already downloaded)")
            continue

        print(f"Downloading {year}-{month:02d}...")

        for attempt in range(3): #We make three attempts to download
            try:
                vs = get_viewstate(session)

                payload = {
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__LASTFOCUS": "",
                    "__VIEWSTATE": vs.get("__VIEWSTATE", ""),
                    "__VIEWSTATEGENERATOR": vs.get("__VIEWSTATEGENERATOR", ""),
                    "__EVENTVALIDATION": vs.get("__EVENTVALIDATION", ""),
                    "txtSearch": "",
                    "cboGeography": "All",
                    "cboYear": str(year),
                    "cboPeriod": str(month),
                    "btnDownload": "Download",
                }

                for field in EXPLICIT_FIELDS:
                    payload[field] = "on" #Flagging all the attributes we want to download in the payload.

                r = session.post(BASE_URL + PARAMS, data=payload, headers=HEADERS, timeout=300)

                if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("application/zip"):
                    with open(filename, "wb") as f:
                        f.write(r.content)
                    print(f"  Saved {len(r.content) / 1024:.1f} KB")
                    break  # success, stop retrying
                else:
                    print(f"  WARNING: Unexpected response ({r.status_code}, {len(r.content)} bytes)")
                    time.sleep(30)

            except Exception as e:
                print(f"  ERROR (attempt {attempt+1}): {e}")
                time.sleep(30)

        time.sleep(5)

print("Done!")