import os
import time
import img2pdf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

url = "https://stotranidhi.com/sundaradasu-ms-rama-rao-sundarakanda-in-telugu/"
output_dir = "screenshots"
pdf_output = "Sundaradasu_Sundarakanda_Part1.pdf"

def take_screenshots(overlap=30):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # Wait for page to load

    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    offset = 0
    index = 0
    screenshots = []

    while offset < total_height:
        driver.execute_script(f"window.scrollTo(0, {offset})")
        time.sleep(1.5)  # Wait for rendering after scroll

        screenshot_path = os.path.join(output_dir, f"shot_{index}.png")
        driver.save_screenshot(screenshot_path)
        screenshots.append(screenshot_path)

        # Scroll down by viewport_height minus overlap
        offset += (viewport_height - overlap)
        index += 1

    driver.quit()
    return screenshots

def create_pdf_from_images(images):
    if not images:
        print("No screenshots found.")
        return
    pdf_bytes = img2pdf.convert(images)
    with open(pdf_output, "wb") as f:
        f.write(pdf_bytes)
    print(f"PDF created successfully: {pdf_output}")

if __name__ == "__main__":
    if os.path.exists(output_dir) and any(f.endswith(".png") for f in os.listdir(output_dir)):
        print("Screenshots found, skipping capture...")
        screenshots = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".png")])
    else:
        print("Taking screenshots with overlap...")
        screenshots = take_screenshots(overlap=200)

    create_pdf_from_images(screenshots)
