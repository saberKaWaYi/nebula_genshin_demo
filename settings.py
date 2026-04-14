import json

settings = {
  "crontab_task": {
    "website_cookies": {
      "wiki_biligame_com": {
        "cookie_name": {
          "SESSDATA": "80e2be21%2C1789203900%2C949ca%2A32CjD2Gvwg3haOu5McOA0u_hAKlykzCa6TzdsDlON4b_h26Jc82hpLsMRb8d9OHJ6phFASVmRBOXFxcFd1QUVZUTRuVXY1LU0tSjUyTnhfZEpSdWlFeVhlVUJNZkJOVVVYT2xiV3BZZFl6czFEM2dua3BELWhYWUt5SzBSNll2OGdZS0wwemRYV1lRIIEC"
        }
      }
    },
    "headers": {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
    },
    "time_sleep": 3
  }
}

settings_json = json.dumps(settings, indent=2, ensure_ascii=False)