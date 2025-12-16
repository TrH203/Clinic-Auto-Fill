"""
Manual calculation to understand the exact times
"""

procedures = ["cứu", "giác", "kéo", "thủy"]
durations = {
    "cứu": 20,
    "giác": 20,
    "kéo": 20,
    "thủy": 30,
}

abilities = {
    "cứu": "ys",
    "giác": "ys",
    "kéo": "bs",  
    "thủy": "bs",
}

# Record 1: 1234567890, 08:00, staff: duy-anh-khoái
print("=" * 60)
print("RECORD 1: ID 1234567890")
print("Start time: 08:00")
print("Staff: duy (P1), anh (P2), khoái (P3)")
print("=" * 60)

# Initial time
from datetime import datetime, timedelta
start_time = datetime.strptime("08:00", "%H:%M")

# Adjust for CD time (5 minutes before)
cd_time = start_time - timedelta(minutes=5)
# Fix if too early
if cd_time.time() < datetime.strptime("07:00", "%H:%M").time():
    cd_time = datetime.strptime("07:00", "%H:%M")

print(f"\nChẩn đoán time: {cd_time.strftime('%H:%M')}")

current_time = start_time
flag = False  # For ys staff alternation

for i, proc in enumerate(procedures):
    ability = abilities[proc]
    
    # Determine staff
    if ability == "bs":
        staff = "anh (P2)"
    else:  # ys
        if flag:
            staff = "khoái (P3)"
        else:
            staff = "duy (P1)"
        flag = not flag
    
    end_time = current_time + timedelta(minutes=durations[proc])
    
    print(f"\n{i+1}. {proc} ({ability}):")
    print(f"   Staff: {staff}")
    print(f"   Time: {current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
    
    # Next procedure starts 2 minutes after current ends
    current_time = end_time + timedelta(minutes=2)


print("\n" + "=" * 60)
print("RECORD 2: ID 1234567891")
print("Start time: 08:00")
print("Staff: khoái (P1), anh (P2), lực (P3)")
print("=" * 60)

# Reset for record 2
start_time = datetime.strptime("08:00", "%H:%M")
cd_time = start_time - timedelta(minutes=5)
if cd_time.time() < datetime.strptime("07:00", "%H:%M").time():
    cd_time = datetime.strptime("07:00", "%H:%M")

print(f"\nChẩn đoán time: {cd_time.strftime('%H:%M')}")

current_time = start_time
flag = False

for i, proc in enumerate(procedures):
    ability = abilities[proc]
    
    # Determine staff
    if ability == "bs":
        staff = "anh (P2)"
    else:  # ys
        if flag:
            staff = "lực (P3)"
        else:
            staff = "khoái (P1)"
        flag = not flag
    
    end_time = current_time + timedelta(minutes=durations[proc])
    
    print(f"\n{i+1}. {proc} ({ability}):")
    print(f"   Staff: {staff}")
    print(f"   Time: {current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}")
    
    current_time = end_time + timedelta(minutes=2)


print("\n" + "=" * 60)
print("CONFLICT ANALYSIS")
print("=" * 60)

print("\nkhoái (Group 1) appears in:")
print("  Record 1, Procedure 2 (giác): 08:22 - 08:42")
print("  Record 2, Procedure 1 (cứu):  08:00 - 08:20")
print("\n  👉 NO OVERLAP! (08:00-08:20 vs 08:22-08:42)")

print("\nduy (Group 1) appears in:")
print("  Record 1, Procedure 1 (cứu): 08:00 - 08:20")
print("\n  👉 Only one appearance, no conflict")

print("\nlực (Group 1) appears in:")
print("  Record 2, Procedure 2 (giác): 08:22 - 08:42")  
print("\n  👉 Only one appearance, no conflict")

print("\nanh (Group 2 - Doctor) appears in BOTH but is EXEMPT from validation")

print("\n" + "=" * 60)
print("CONCLUSION: NO CONFLICTS - Validation is CORRECT! ✅")
print("=" * 60)
