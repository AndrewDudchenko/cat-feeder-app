A cross-platform app to track and sync pet feeding schedules in real time.

Features

* Uses Firebase Realtime Database to update feeding status instantly across all devices.
* Sends automated reminders 30 minutes before and exactly at scheduled feeding times. (Unfortunately does not work(Xiaomi phone is blocking push notifications))
* Tracks 4 daily slots (6:00, 12:00, 18:00, 22:00), logging the exact time and the person who fed the cat.
* Automatically resets the feeding slots every day at midnight.

Tech Stack

* Python
* Flet (Flutter engine)
* Firebase Realtime Database (REST API)
* Plyer (Notifications)

How to Run Locally

1. Clone the repository.
2. Open `main.py` and replace `YOUR_FIREBASE_DATABASE_URL` with your own Firebase Realtime Database URL.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
