import json, time

moves = [
    {"x": 200, "y": 100, "speed": 0.06},
    {"x": 3200, "y": 100, "speed": 0.08},
    {"x": 3200, "y": 1300, "speed": 0.08},
    {"x": 200, "y": 1300, "speed": 0.08},
    {"x": 1720, "y": 720, "speed": 0.06},
    {"x": 500, "y": 400, "speed": 0.1},
    {"x": 2800, "y": 400, "speed": 0.1},
    {"x": 1720, "y": 1200, "speed": 0.05},
    {"x": 1720, "y": 200, "speed": 0.12},
    {"x": 1720, "y": 720, "speed": 0.04},
]

for i, m in enumerate(moves):
    with open("dog_cursor_cmd.json", "w") as f:
        json.dump(m, f)
    print(f"Move {i+1}: dog -> ({m['x']}, {m['y']})")
    time.sleep(2.5)

print("Tour complete!")
