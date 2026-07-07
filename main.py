from plyer import notification
import flet as ft
import requests
import datetime
import asyncio

FIREBASE_URL = "https://cat-feeder-app-67e48-default-rtdb.europe-west1.firebasedatabase.app/cat_feeder.json"

SLOTS = ["6:00", "12:00", "18:00", "22:00"]

def main(page: ft.Page):
    page.title = "Котячий Годувальник 🐾"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "adaptive"

    current_user = ft.Ref[ft.Dropdown]()
    status_controls = {}

    def init_db():
        try:
            res = requests.get(FIREBASE_URL)
            if res.status_code == 200 and (res.json() is None or "date" not in res.json()):
                reset_slots()
        except Exception as e:
            print(f"Помилка ініціалізації: {e}")

    def reset_slots():
        today = datetime.date.today().isoformat()
        data = {
            "date": today,
            "slots": {slot: {"is_fed": False, "fed_at": "", "fed_by": ""} for slot in SLOTS}
        }
        try:
            requests.put(FIREBASE_URL, json=data)
        except Exception as e:
            print(f"Помилка скидання: {e}")

    def update_ui_from_db(data):
        if not data or "slots" not in data:
            return
        
        today = datetime.date.today().isoformat()
        if data.get("date") != today:
            reset_slots()
            return

        slots_data = data["slots"]
        for slot in SLOTS:
            slot_info = slots_data.get(slot, {"is_fed": False, "fed_at": "", "fed_by": ""})
            is_fed = slot_info["is_fed"]
            
            controls = status_controls[slot]
            text_status = controls["text_status"]
            btn = controls["btn"]
            info_text = controls["info_text"]

            if is_fed:
                text_status.value = "ПОГОДОВАНО ✅"
                text_status.color = ft.Colors.GREEN_700
                info_text.value = f"Час: {slot_info['fed_at']} | Хто: {slot_info['fed_by']}"
                btn.disabled = True
                btn.text = "Вже поїв"
                btn.icon = ft.Icons.CHECK
            else:
                text_status.value = "Голодний 🥣"
                text_status.color = ft.Colors.RED_700
                info_text.value = "Чекає на їжу..."
                btn.disabled = False
                btn.text = "Погодувати"
                btn.icon = ft.Icons.PETS

        page.update()

    async def poll_firebase():
        notified_slots = set()  # Слідкуємо, щоб не спамити сповіщеннями
        while True:
            try:
                res = requests.get(FIREBASE_URL)
                if res.status_code == 200:
                    data = res.json()
                    update_ui_from_db(data)
                    
                    # Логіка нагадувань
                    now = datetime.datetime.now()
                    
                    for slot in SLOTS:
                        h, m = map(int, slot.split(':'))
                        slot_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                        
                        # Розраховуємо різницю в хвилинах
                        diff = (slot_time - now).total_seconds() / 60
                        
                        is_fed = data["slots"].get(slot, {}).get("is_fed", False)
                        
                        if not is_fed:
                            # Нагадування за 30 хв (діапазон 25-35 хвилин)
                            if 25 <= diff <= 35 and slot not in notified_slots:
                                notification.notify(title='🐾 Годування скоро!', message=f'Кіт захоче їсти о {slot}', app_name='CatFeeder')
                                notified_slots.add(slot)
                            
                            # Нагадування в час (діапазон від -2 до +10 хвилин)
                            # Ми розширили діапазон, щоб сповіщення точно прийшло
                            if -2 <= diff <= 10 and slot not in notified_slots:
                                notification.notify(title='🥣 Час годувати!', message=f'Зараз час годування: {slot}', app_name='CatFeeder')
                                notified_slots.add(slot)
                    
                    # Очищаємо список лише якщо зараз ніч, щоб не накопичувати дані
                    if now.hour == 23 and now.minute > 50:
                        notified_slots.clear()

            except Exception as e:
                print(f"Помилка сповіщення: {e}")
            await asyncio.sleep(30) # Перевіряємо кожні 30 секунд

    def feed_cat_click(e, slot):
        user = current_user.current.value
        if not user:
            page.show_dialog(ft.SnackBar(ft.Text("Будь ласка, виберіть, хто годує кота!")))
            return

        now = datetime.datetime.now().strftime("%H:%M")
        base_endpoint = FIREBASE_URL.replace(".json", "")
        patch_url = f"{base_endpoint}/slots/{slot}.json"
        
        patch_data = {
            "is_fed": True,
            "fed_at": now,
            "fed_by": user
        }
        try:
            requests.patch(patch_url, json=patch_data)
            requests.patch(FIREBASE_URL, json={"date": datetime.date.today().isoformat()})
        except Exception as ex:
            print(f"Помилка відправки даних: {ex}")

    user_dropdown = ft.Dropdown(
        ref=current_user,
        label="Хто ти?",
        hint_text="Вибери своє ім'я",
        options=[
            ft.DropdownOption("Андрій"),
            ft.DropdownOption("Костянтин"),
            ft.DropdownOption("Ірина"),
            ft.DropdownOption("Євгеній"),
            ft.DropdownOption("Людмила"),
            ft.DropdownOption("Сергій")
        ],
        width=250,
    )

    page.add(
        ft.Container(height=10),
        ft.Text("Мій Кіт: Графік Годування 🐾", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        ft.Row([user_dropdown], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
    )

    for slot in SLOTS:
        text_status = ft.Text("Завантаження...", size=16, weight=ft.FontWeight.W_500)
        info_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
        
        # Змінено ElevatedButton на Button для сумісності з Flet 0.85+
        btn = ft.Button(
            "Погодувати", 
            icon=ft.Icons.PETS,
            on_click=lambda e, s=slot: feed_cat_click(e, s)
        )

        status_controls[slot] = {
            "text_status": text_status,
            "info_text": info_text,
            "btn": btn
        }

        card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ACCESS_TIME, color=ft.Colors.BLUE_GREY_500),
                        title=ft.Text(slot, size=18, weight=ft.FontWeight.BOLD),
                        subtitle=text_status,
                    ),
                    ft.Row(
                        [info_text, btn],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                ]),
                padding=15
            ),
            width=360
        )
        page.add(card)

    def force_reset(e):
        reset_slots()
        page.show_dialog(ft.SnackBar(ft.Text("Графік скинуто вручну!")))

    page.add(
        ft.Container(height=10),
        ft.TextButton("Скинути графік вручну", on_click=force_reset, icon=ft.Icons.REFRESH, icon_color=ft.Colors.GREY_500)
    )

    init_db()
    page.run_task(poll_firebase)

if __name__ == "__main__":
    # Змінено app() на run() для сумісності з новішими версіями
    ft.run(main)