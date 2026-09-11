import requests
import json

TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjcwMTgyNTg4MywiYWFpIjoxMSwidWlkIjoxMTUwNDUwNDUsImlhZCI6IjIwMjYtMDktMDhUMjE6NTk6MzUuMDAwWiIsInBlciI6Im1lOndyaXRlIiwiYWN0aWQiOjMxMzI4NTkwLCJyZ24iOiJ1c2UxIn0.H6mFyP0V346H2px3Rwd4PTuMsULpFQlk1_HR9pxgjXw"
BOARD_ID = 18415696704

URL = "https://api.monday.com/v2"

headers = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}

query = f"""
query {{
  boards(ids: {BOARD_ID}) {{
    id
    name

    views {{
      id
      name
      type
      filter
      sort
      settings
    }}
  }}
}}
"""

response = requests.post(
    URL,
    json={"query": query},
    headers=headers
)

print("Status:", response.status_code)

data = response.json()

if "errors" in data:
    print(data["errors"])
    raise SystemExit

views = data["data"]["boards"][0]["views"]

for view in views:

    print("\n" + "=" * 80)

    print("ID:", view["id"])
    print("Nombre:", view["name"])
    print("Tipo:", view["type"])

    print("\nFILTER:")
    print(
        json.dumps(
            view["filter"],
            indent=4,
            ensure_ascii=False
        )
    )

    print("\nSORT:")
    print(
        json.dumps(
            view["sort"],
            indent=4,
            ensure_ascii=False
        )
    )