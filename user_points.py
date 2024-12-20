
import json

# Save user points to a file
def save_user_points(user_points):
    with open("user_points.json", "w") as f:
        json.dump(user_points, f)

# Load user points from a file
def load_user_points():
    global user_points
    try:
        with open("user_points.json", "r") as f:
            user_points = json.load(f)
    except FileNotFoundError:
        user_points = {}
    return user_points
