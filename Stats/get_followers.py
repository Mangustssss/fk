import requests
import json
import time
from datetime import datetime

url = "https://www.instagram.com/api/v1/friendships/57702485776/followers/"

big_circle = []

params = {
    'count': '12',
    'search_surface': 'follow_list_page',
}

headers = {
    'Host': 'www.instagram.com',
    'Cookie': '6syRdJlXHAeGkVGOhFET1y7hpLqnCytn; mid=ZcY-LgALAAGxIQzWcy2rgaNKcwui; ig_did=1F94FF48-6D3F-4506-A81B-FC010B59B205; ds_user_id=65059906798; datr=PT7GZckqpUnk4J-Sm3lzUwDV; sessionid=65059906798%3A55AlcTlpYHVuZk%3A8%3AAYc8OPlKYvCtywoVWESVflspK9J8fcFcl8KZA23k2g; rur="RVA\05465059906798\0541739810770:01f7dba3b03bbb7db98779b464634ef588dee029d6690bc55512f7d140a2cd51f65809e8"',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'X-Csrftoken': '6syRdJlXHAeGkVGOhFET1y7hpLqnCytn',
    'X-Ig-App-Id': '936619743392459',
    'X-Asbd-Id': '129477',
    'X-Ig-Www-Claim': 'hmac.AR2nt3AQ2PGEyrWUBYubU9OZudt7WIYDG1hPa1whdeRRk6rr',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://www.instagram.com/fkreceipts/followers/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Te': 'trailers'
}
while len(big_circle) != 3000:
    time.sleep(1)
    response = requests.get(url, params=params, headers=headers)
    print(response.status_code)
    data = json.loads(response.text)
    print(data)
    small_circle = [i['username'] for i in data['users']]

    print(len(big_circle)/3000)
    try:
        params['max_id'] += 12
    except KeyError:
        params['max_id'] = 12
    big_circle += small_circle

print(big_circle)
NOW_DATE = datetime.now()
with open(f"followers_{NOW_DATE.day}_{NOW_DATE.month}_{NOW_DATE.year}.txt", "w", encoding='utf-8') as f:
    f.write("\n".join(big_circle))
