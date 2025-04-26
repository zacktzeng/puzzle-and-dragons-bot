from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
import time

def swipe_square(driver, center_x, center_y, offset):
    # Create the action builder
    finger = PointerInput("touch", "finger")
    actions = ActionBuilder(driver, mouse=finger)

    # Finger presses down at center
    actions.pointer_action.move_to_location(center_x, center_y)
    actions.pointer_action.pointer_down()

    # Move up
    actions.pointer_action.move_to_location(center_x, center_y - offset)

    # Move right
    actions.pointer_action.move_to_location(center_x + offset, center_y - offset)

    # Move down
    actions.pointer_action.move_to_location(center_x + offset, center_y)

    # Move left
    actions.pointer_action.move_to_location(center_x, center_y)

    # Lift up
    actions.pointer_action.pointer_up()

    # Perform the full gesture
    actions.perform()

def main():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android Device"
    options.app_package = "com.android.settings"  # or any app you like
    options.app_activity = ".Settings"
    options.no_reset = True

    driver = webdriver.Remote("http://localhost:4723", options=options)

    size = driver.get_window_size()
    width = size['width']
    height = size['height']

    center_x = width // 2
    center_y = height // 2
    offset = 300

    swipe_square(driver, center_x, center_y, offset)

    time.sleep(2)
    driver.quit()

if __name__ == "__main__":
    main()
