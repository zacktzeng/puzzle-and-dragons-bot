# bot.py
import sys
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
import cv2
import numpy as np
import math
from copy import deepcopy
import subprocess
import time
import os

# --- CONFIGURATION ---
DEFAULT_ROUNDS_TO_PLAY = 3
FAINT_THRESHOLD = 130
RECOVERY_THRESHOLD = 180
ROWS, COLS = 5, 6

# --- Core Bot ---
ORB_TEMPLATES = {
    "fire":   {"path": "screenshots/red_orb.png", "color": (0, 0, 255)},
    "water":  {"path": "screenshots/blue_orb.png", "color": (255, 0, 0)},
    "wood":   {"path": "screenshots/green_orb.png", "color": (0, 255, 0)},
    "light":  {"path": "screenshots/light_orb.png", "color": (0, 255, 255)},
    "dark":   {"path": "screenshots/dark_orb.png", "color": (128, 0, 128)},
    "heart":  {"path": "screenshots/heart_orb.png", "color": (255, 0, 255)},
}

# --- Helper Functions ---
def start_scrcpy_once():
    try:
        result = subprocess.run(["pgrep", "scrcpy"], capture_output=True, text=True)
        if result.returncode == 0:
            print("📺 scrcpy already running, skipping launch.")
            return
    except Exception as e:
        print(f"⚠️ Error checking scrcpy process: {e}")

    print("🚀 Starting scrcpy screen mirror...")
    try:
        subprocess.Popen(
            ["scrcpy", "--max-fps", "60", "--video-bit-rate", "16M", "--window-title", "PAD Bot Stream"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
    except FileNotFoundError:
        print("❌ scrcpy is not installed! Install it with 'brew install scrcpy'")

def capture_screenshot(driver):
    png_data = driver.get_screenshot_as_png()
    nparr = np.frombuffer(png_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def load_orb_templates(template_dict):
    templates = {}
    for orb_name, data in template_dict.items():
        img = cv2.imread(data["path"])
        if img is not None:
            templates[orb_name] = {
                "image": img,
                "gray": cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
                "color": data["color"]
            }
        else:
            print(f"⚠️ Failed to load template for {orb_name}")
    return templates

def find_candidates_from_all_templates(screenshot, templates, threshold=0.8):
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    matches = []
    for orb_name, data in templates.items():
        template_gray = data["gray"]
        result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        h, w = template_gray.shape[:2]
        for (x, y) in zip(*locations[::-1]):
            matches.append({"x": x, "y": y, "w": w, "h": h})
    return matches

def classify_orbs(matches, screenshot, templates):
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    for orb in matches:
        x, y, w, h = orb["x"], orb["y"], orb["w"], orb["h"]
        orb_crop = screenshot_gray[y:y+h, x:x+w]
        best_match = None
        best_score = float("-inf")
        for orb_name, template_data in templates.items():
            template = template_data["gray"]
            if orb_crop.shape != template.shape:
                orb_crop_resized = cv2.resize(orb_crop, (template.shape[1], template.shape[0]))
            else:
                orb_crop_resized = orb_crop
            result = cv2.matchTemplate(orb_crop_resized, template, cv2.TM_CCOEFF_NORMED)
            score = result[0][0]
            if score > best_score:
                best_score = score
                best_match = orb_name
        orb["orb_type"] = best_match
        orb["color"] = templates[best_match]["color"]
    return matches

def filter_close_matches(matches, distance_threshold=20):
    filtered = []
    for new in matches:
        too_close = False
        for existing in filtered:
            dx = new['x'] - existing['x']
            dy = new['y'] - existing['y']
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < distance_threshold:
                too_close = True
                break
        if not too_close:
            filtered.append(new)
    return filtered

def structure_into_grid(matches):
    sorted_matches = sorted(matches, key=lambda m: (m['y'], m['x']))
    rows = []
    current_row = []
    row_threshold = 20
    for match in sorted_matches:
        if not current_row:
            current_row.append(match)
            continue
        if abs(match['y'] - current_row[0]['y']) < row_threshold:
            current_row.append(match)
        else:
            rows.append(current_row)
            current_row = [match]
    if current_row:
        rows.append(current_row)
    grid = []
    for row in rows:
        sorted_row = sorted(row, key=lambda m: m['x'])
        grid.append(sorted_row)
    if len(grid) != ROWS or any(len(row) != COLS for row in grid):
        print("⚠️ Warning: Grid shape mismatch!")
        return None
    return [[match['orb_type'] for match in row] for row in grid]

def count_combos(grid):
    visited = [[False] * COLS for _ in range(ROWS)]
    combos = 0
    def dfs(r, c, orb_type, group):
        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            return
        if visited[r][c] or grid[r][c] != orb_type:
            return
        visited[r][c] = True
        group.append((r, c))
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            dfs(r+dr, c+dc, orb_type, group)
    to_clear = set()
    for r in range(ROWS):
        for c in range(COLS-2):
            if grid[r][c] == grid[r][c+1] == grid[r][c+2] != "":
                to_clear.update([(r,c),(r,c+1),(r,c+2)])
    for r in range(ROWS-2):
        for c in range(COLS):
            if grid[r][c] == grid[r+1][c] == grid[r+2][c] != "":
                to_clear.update([(r,c),(r+1,c),(r+2,c)])
    for (r,c) in to_clear:
        if not visited[r][c]:
            group = []
            dfs(r,c,grid[r][c],group)
            if group:
                combos +=1
    return combos

def simulate_path(grid, path):
    board = deepcopy(grid)
    if not path:
        return board
    prev_r, prev_c = path[0]
    for r, c in path[1:]:
        board[prev_r][prev_c], board[r][c] = board[r][c], board[prev_r][prev_c]
        prev_r, prev_c = r, c
    return board

def generate_paths(start_r, start_c, max_steps):
    paths = []
    def dfs(r, c, path, visited, steps):
        if steps > max_steps:
            return
        paths.append(path[:])
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<ROWS and 0<=nc<COLS and (nr,nc) not in visited:
                visited.add((nr,nc))
                dfs(nr,nc,path+[(nr,nc)],visited,steps+1)
                visited.remove((nr,nc))
    dfs(start_r, start_c, [(start_r,start_c)], set([(start_r,start_c)]), 0)
    return paths

def find_best_path(grid, max_steps=8):
    best_combo = 0
    best_path = None
    for r in range(ROWS):
        for c in range(COLS):
            for path in generate_paths(r,c,max_steps):
                combos = count_combos(simulate_path(grid,path))
                if combos > best_combo:
                    best_combo = combos
                    best_path = path
    return best_path, best_combo

def send_appium_swipe_path(driver, path, top_left, bottom_right):
    finger = PointerInput("touch", "finger")
    actions = ActionBuilder(driver, mouse=finger)
    cell_width = (bottom_right[0] - top_left[0]) / (COLS-1)
    cell_height = (bottom_right[1] - top_left[1]) / (ROWS-1)
    def grid_to_pixel(r,c):
        x = int(top_left[0] + c*cell_width)
        y = int(top_left[1] + r*cell_height)
        return x,y
    r0,c0 = path[0]
    x,y = grid_to_pixel(r0,c0)
    actions.pointer_action.move_to_location(x,y)
    actions.pointer_action.pointer_down()
    for (r,c) in path[1:]:
        target_x,target_y = grid_to_pixel(r,c)
        if x != target_x:
            actions.pointer_action.move_to_location(target_x, y)
            x = target_x
        if y != target_y:
            actions.pointer_action.move_to_location(x, target_y)
            y = target_y
    actions.pointer_action.pointer_up()
    actions.perform()

def get_orb_brightness(driver, grid_r, grid_c, top_left, bottom_right):
    img = capture_screenshot(driver)
    cell_width = (bottom_right[0] - top_left[0]) / (COLS - 1)
    cell_height = (bottom_right[1] - top_left[1]) / (ROWS - 1)
    x = int(top_left[0] + grid_c * cell_width)
    y = int(top_left[1] + grid_r * cell_height)
    crop = img[max(0, y - 5):y + 5, max(0, x - 5):x + 5]
    gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray_crop)
    max_brightness = np.max(gray_crop)
    print(f"🧪 Brightness (mean: {mean_brightness:.2f}, max: {max_brightness:.2f})")
    return int(max_brightness)

def wait_for_attack_and_recovery(driver, top_left, bottom_right, sample_orbs=[(2,2), (1,1), (1,4), (3,1)]):
    print("⏳ Short wait after swipe...")
    time.sleep(1.0)

    print("⏳ Checking orb brightness for recovery...")
    max_attempts = 5
    for attempt in range(max_attempts):
        brightnesses = [int(get_orb_brightness(driver, r, c, top_left, bottom_right)) for r, c in sample_orbs]
        print(f"📈 Brightnesses attempt {attempt+1}: {brightnesses}")

        if any(b >= RECOVERY_THRESHOLD for b in brightnesses):
            print("✅ Board ready for next move!")
            return

        time.sleep(1.0)

    print("⚠️ Proceeding after maximum brightness checks.")


# --- Main ---
def main(rounds_to_play):
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android Device"
    options.no_reset = True

    driver = webdriver.Remote("http://localhost:4723", options=options)

    for round_num in range(1, rounds_to_play + 1):
        print(f"\n🎮 Starting Round {round_num}")

        screenshot = capture_screenshot(driver)
        templates = load_orb_templates(ORB_TEMPLATES)
        matches = find_candidates_from_all_templates(screenshot, templates, threshold=0.8)
        matches = filter_close_matches(matches)
        matches = classify_orbs(matches, screenshot, templates)

        orb_grid = structure_into_grid(matches)
        if orb_grid is None:
            print("❌ Failed to build orb grid")
            break

        all_centers = [(m["x"] + m["w"]//2, m["y"] + m["h"]//2) for m in matches]
        top_left = (min(x for x, y in all_centers), min(y for x, y in all_centers))
        bottom_right = (max(x for x, y in all_centers), max(y for x, y in all_centers))

        path, combos = find_best_path(orb_grid)
        print(f"💡 Best Path: {path}")
        print(f"🔥 Combos: {combos}")

        send_appium_swipe_path(driver, path, top_left, bottom_right)

        wait_for_attack_and_recovery(driver, top_left, bottom_right)

        print(f"✅ Round {round_num} complete!")
        time.sleep(2)

    driver.quit()

# Entry point
if __name__ == "__main__":
    try:
        rounds_arg = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROUNDS_TO_PLAY
    except ValueError:
        print(f"⚠️ Invalid argument. Using default {DEFAULT_ROUNDS_TO_PLAY} rounds.")
        rounds_arg = DEFAULT_ROUNDS_TO_PLAY

    main(rounds_arg)
