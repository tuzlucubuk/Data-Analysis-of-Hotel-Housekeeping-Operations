import pandas as pd
import random
from datetime import datetime, timedelta
import os
import numpy as np

# Temizlik personeli ID'lerini oluşturma
def create_personnel_ids(num_personnel):
    return [f"P{str(i).zfill(3)}" for i in range(1, num_personnel + 1)]

# Mini bar görevlisi personel ID'lerini oluşturma
def create_mini_bar_ids(num_personnel):
    return [f"M{str(i).zfill(3)}" for i in range(1, num_personnel + 1)]

# Arıza personeli ID oluşturma
def create_repair_ids(num_personnel):
    return [f"A{str(i).zfill(3)}" for i in range(1, num_personnel + 1)]

# Oda numaralarını oluşturma
def create_room_numbers(start, end):
    return [str(i) for i in range(start, end + 1)]

# Mini bar süresi belirleme
def get_mini_bar_duration():
    return random.randint(3, 6)

# Arıza süresi belirleme
def get_repair_duration():
    return random.randint(10, 59)

# Temizlik süresi belirleme
def get_cleaning_duration(cleaning_type, room_type, sheets_changed, speed_multiplier=1.0):
    if cleaning_type == "Rutin":
        if room_type == "Standart":
            duration = random.randint(5, 15)
        elif room_type == "Suit":
            duration = random.randint(10, 17)
        elif room_type == "Lüx Suit":
            duration = random.randint(15, 20)
    elif cleaning_type == "Detaylı":
        if room_type == "Standart":
            duration = random.randint(20, 40)
        elif room_type == "Suit":
            duration = random.randint(30, 50)
        elif room_type == "Lüx Suit":
            duration = random.randint(40, 60)
    elif cleaning_type == "Müşteri Talebi":
        duration = random.randint(5, 30)
    return int(duration * speed_multiplier)

# Doluluk oranı belirleme
def get_occupancy_rate(month):
    if month in [6, 7, 8]:
        return random.uniform(0.9, 1.0)
    elif month in [5, 9]:
        return random.uniform(0.5, 0.7)
    elif month in [4, 10]:
        return random.uniform(0.3, 0.4)
    else:
        return random.uniform(0.05, 0.1)

# Giriş saati belirleme
def get_entry_time(task_type):
    if task_type == "Rutin":
        start_hour, end_hour = 8, 10
    elif task_type == "Detaylı":
        start_hour, end_hour = 12, 14
    elif task_type == "Mini Bar":
        start_hour, end_hour = 9, 11
    else:
        start_hour, end_hour = 8, 18
    random_hour = random.randint(start_hour, end_hour)
    random_minute = random.randint(0, 59)
    return datetime.strptime(f"{random_hour}:{random_minute:02d}", "%H:%M")

personnel_busy_times = {}

def get_available_entry_time(personnel_id, task_type):
    new_entry_time = get_entry_time(task_type)
    if personnel_id in personnel_busy_times:
        last_end_time = personnel_busy_times[personnel_id]
        if new_entry_time < last_end_time:
            new_entry_time = last_end_time + timedelta(minutes=5)
    return new_entry_time

def adjust_efficiency(base_eff, day_count):
    if day_count >= 10:
        return max(0.5, base_eff * 0.9)
    return base_eff

def get_repair_probability(room_type, month):
    base = 0.005
    if room_type == "Suit":
        base = 0.01
    elif room_type == "Lüx Suit":
        base = 0.02
    if month in [6, 7, 8]:
        base *= 1.5
    return base

personnel_ids = create_personnel_ids(100)
personnel_assignment_chance = {}
personnel_efficiency = {}
personnel_work_days = {pid: 0 for pid in personnel_ids}

# Kat bazlı personel ataması
floor_personnel_map = {
    floor: personnel_ids[(floor - 1) * 5: floor * 5] for floor in range(1, 19)
}

# Gaussian dağılımdan çalışkanlık üret (ortalama=1.0, std=0.2, sınırlar 0.5–1.5)
efficiencies = np.random.normal(loc=1.0, scale=0.2, size=len(personnel_ids))
efficiencies = np.clip(efficiencies, 0.5, 1.5)

for pid, eff in zip(personnel_ids, efficiencies):
    rand = random.random()
    if rand < 0.1:
        personnel_assignment_chance[pid] = 0.1 # çok tembel çalışanlar
    elif rand < 0.3:
        personnel_assignment_chance[pid] = 0.5 # tembel çalışanlar
    else:
        personnel_assignment_chance[pid] = 1.0
    personnel_efficiency[pid] = eff

mini_bar_ids = create_mini_bar_ids(50)
repair_ids = create_repair_ids(10)
rooms = []

start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
current_date = start_date
room_cleaning_tracker = {}

while current_date <= end_date:
    month = current_date.month
    occupancy_rate = get_occupancy_rate(month)
    mini_bar_index = 0

    for floor in range(1, 19):
        max_rooms = 70 if floor <= 10 else 50 if floor <= 14 else 25
        room_numbers = create_room_numbers(floor * 100 + 1, floor * 100 + max_rooms)
        personnel_per_floor = floor_personnel_map[floor]
        mini_bar_per_floor = mini_bar_ids[mini_bar_index: mini_bar_index + 2] if floor <= 14 else [mini_bar_ids[mini_bar_index]]
        mini_bar_index += len(mini_bar_per_floor)

        occupied_rooms = int(len(room_numbers) * occupancy_rate)
        random.shuffle(room_numbers)
        occupied_room_numbers = room_numbers[:occupied_rooms]

        for room in occupied_room_numbers:
            available_personnel = [p for p in personnel_per_floor if random.random() < personnel_assignment_chance[p]]
            if not available_personnel:
                continue
            personnel_id = random.choice(available_personnel)

            mini_bar_personnel = random.choice(mini_bar_per_floor)
            stay_duration = random.randint(1, 7)
            routine_days = room_cleaning_tracker.get((room, "Rutin"), 0)
            repair_personnel = random.choice(repair_ids)

            if routine_days >= stay_duration:
                cleaning_type = "Detaylı"
                room_cleaning_tracker[(room, "Rutin")] = 0
            else:
                cleaning_type = "Rutin"
                room_cleaning_tracker[(room, "Rutin")] = routine_days + 1

            room_type = "Standart" if floor <= 10 else "Suit" if floor <= 14 else "Lüx Suit"
            entry_time = get_available_entry_time(personnel_id, "Rutin")
            effective_eff = adjust_efficiency(personnel_efficiency[personnel_id], personnel_work_days[personnel_id])
            duration = get_cleaning_duration(cleaning_type, room_type, "Evet", effective_eff)
            exit_time = entry_time + timedelta(minutes=duration)
            personnel_busy_times[personnel_id] = exit_time
            personnel_work_days[personnel_id] += 1

            rooms.append({
                "Tarih": current_date.strftime("%Y-%m-%d"),
                "Oda Numarası": room,
                "Oda Tipi": room_type,
                "Personel ID": personnel_id,
                "Temizlik Türü": cleaning_type,
                "Giriş Saati": entry_time.strftime("%H:%M"),
                "Çıkış Saati": exit_time.strftime("%H:%M")
            })

            mini_bar_start_time = get_available_entry_time(mini_bar_personnel, "Mini Bar")
            mini_bar_duration = get_mini_bar_duration()
            mini_bar_end_time = mini_bar_start_time + timedelta(minutes=mini_bar_duration)
            personnel_busy_times[mini_bar_personnel] = mini_bar_end_time

            rooms.append({
                "Tarih": current_date.strftime("%Y-%m-%d"),
                "Oda Numarası": room,
                "Oda Tipi": room_type,
                "Personel ID": mini_bar_personnel,
                "Temizlik Türü": "Mini Bar",
                "Giriş Saati": mini_bar_start_time.strftime("%H:%M"),
                "Çıkış Saati": mini_bar_end_time.strftime("%H:%M")
            })

            if random.random() < get_repair_probability(room_type, month):
                repair_start_time = get_available_entry_time(repair_personnel, "Arıza")
                repair_duration = get_repair_duration()
                repair_end_time = repair_start_time + timedelta(minutes=repair_duration)

                rooms.append({
                    "Tarih": current_date.strftime("%Y-%m-%d"),
                    "Oda Numarası": room,
                    "Oda Tipi": room_type,
                    "Personel ID": repair_personnel,
                    "Temizlik Türü": "Arıza",
                    "Giriş Saati": repair_start_time.strftime("%H:%M"),
                    "Çıkış Saati": repair_end_time.strftime("%H:%M")
                })

    current_date += timedelta(days=1)

now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename_csv = f"otel_temizlik_veriseti_{now}.csv"
filename_xlsx = f"otel_temizlik_veriseti_{now}.xlsx"
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
df = pd.DataFrame(rooms)
df.to_csv(os.path.join(desktop_path, filename_csv), index=False)

# df.to_excel(os.path.join(desktop_path, filename_xlsx), index=False)
print(f"Guncellenmis veri seti basariyla kaydedildi: {filename_csv}\n{filename_xlsx}")
