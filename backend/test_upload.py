import requests
import json

with requests.Session() as s:
    r = s.post("http://localhost:8000/api/auth/token", data={"username": "990101000001", "password": "admin123"})
    token = r.json().get("access_token")
    if not token:
        print("No token:", r.text)
        exit(1)
        
    with open("c:/Users/user/Desktop/scheduleSYS/Сетки часов/сетка часов БД на 2025-2026 жанна 1 курс свод  чистовик !!!!.xls", "rb") as f:
        res = s.post(
            "http://localhost:8000/api/hour-grid/import-file?academic_period_id=5&weeks=18",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": f}
        )
        
    print(res.status_code)
    try:
        d = res.json()
        print('created:', d.get('created'), '| skipped:', d.get('skipped'))
        for e in d.get('errors', [])[:5]: 
            print(' -', e)
    except Exception as e:
        print("Error:", e)
        print(res.text)
