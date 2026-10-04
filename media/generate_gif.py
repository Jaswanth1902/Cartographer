import io
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

html_path = Path("01_Projects/Cartographer/media/comp.html").resolve().as_uri()
out_gif = Path("01_Projects/Cartographer/media/cartographer_demo.gif")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(html_path)

    time_points = [0.8, 2.0, 3.8, 5.2, 6.5, 8.0, 9.8, 12.0, 14.0]
    durations = [1000, 1000, 800, 1200, 800, 1000, 1000, 1500, 1500]

    frames = []
    for t in time_points:
        page.evaluate(f"window.__seek({t})")
        png_bytes = page.screenshot()
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        frames.append(img.quantize(colors=96))

    browser.close()

if frames:
    frames[0].save(
        out_gif,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Successfully generated animated GIF: {out_gif} ({out_gif.stat().st_size / 1024:.1f} KB)")
