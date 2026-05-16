# stage6_priority.py
import requests
from datetime import datetime

# Fetch notifications from API
API_URL = "http://4.224.186.213/evaluation-service/notifications"
HEADERS = {"Authorization": "Bearer <your-token>"}

def get_notifications():
    response = requests.get(API_URL, headers=HEADERS)
    return response.json()["notifications"]

def priority_score(notification):
    # Weight: Placement=3, Result=2, Event=1
    type_weight = {"Placement": 3, "Result": 2, "Event": 1}
    weight = type_weight.get(notification["Type"], 0)
    
    # Recency score — more recent = higher score
    timestamp = datetime.fromisoformat(notification["Timestamp"])
    now = datetime.now()
    age_minutes = (now - timestamp).total_seconds() / 60
    recency = max(0, 1000 - age_minutes)
    
    return (weight * 1000) + recency

def get_top_n(n=10):
    notifications = get_notifications()
    
    # Sort by priority score descending
    sorted_notifs = sorted(
        notifications,
        key=priority_score,
        reverse=True
    )
    
    return sorted_notifs[:n]

if __name__ == "__main__":
    top_10 = get_top_n(10)
    print(f"Top 10 Priority Notifications:")
    for i, notif in enumerate(top_10, 1):
        print(f"{i}. [{notif['Type']}] {notif['Message']} | {notif['Timestamp']}")