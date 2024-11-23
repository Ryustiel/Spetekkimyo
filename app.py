import subprocess
import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jinja2 import Template
from PIL import Image, ImageDraw, ImageFont


# File paths
FONT_PATH = "./static/seiso.ttf"  # Output font path
HTML_PATH = "./static/interface.html"
EXAMPLES_PATH = "./static/examples.txt"
FONT_GENERATOR_SCRIPT = "run.py"  # Path to spetekkimyo generator script
FFPYTHON = "./ffpython/bin/ffpython.exe"  # Special Python executable
IMAGE_PATH = "./static/image.png"  # Path for generated image

# Ensure the output directory exists
os.makedirs("./static", exist_ok=True)


def generate_font_safely(output_path):
    """
    Generate the font file using the special Python environment.
    This function calls 'generate_font()' indirectly via a subprocess.
    """
    try:
        subprocess.run(
            [FFPYTHON, FONT_GENERATOR_SCRIPT, output_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error generating font: {e.stderr}")
        raise RuntimeError("Failed to generate the font file.") from e


def load_template(file_path):
    """Load and return a Jinja2 template as a string."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template_str, context):
    """
    Render a template string with the given context.
    Args:
        template_str: Template content as a string.
        context: Dictionary of variables to render into the template.
    Returns:
        Rendered HTML string.
    """
    template = Template(template_str)
    return template.render(**context)


def load_examples():
    """Read examples from the examples file."""
    if os.path.exists(EXAMPLES_PATH):
        with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return []


# Pydantic models
class TextInput(BaseModel):
    input_text: str


class ImageOutput(BaseModel):
    image_path: str


# FastAPI app setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Preload HTML template
interface_template_str = load_template(HTML_PATH)


@app.on_event("startup")
async def startup_event():
    # On startup, ensure the font file is generated
    if not os.path.exists(FONT_PATH):
        generate_font_safely(FONT_PATH)


@app.get("/")
async def read_root(request: Request):
    # Check if the font file exists; if not, regenerate it
    if not os.path.exists(FONT_PATH):
        generate_font_safely(FONT_PATH)

    examples = load_examples()
    rendered_html = render_template(
        template_str=interface_template_str,
        context={
            "request": request,
            "examples": examples,
            "font_path": "/static/seiso.ttf",
        },
    )
    return HTMLResponse(content=rendered_html)


@app.post("/regenerate-font")
async def regenerate_font():
    # Regenerate the font using the external Python environment
    generate_font_safely(FONT_PATH)
    return RedirectResponse(url="/", status_code=303)


@app.post("/update-examples")
async def update_examples(text: str = Form(...)):
    new_examples = text.split("\n")
    with open(EXAMPLES_PATH, "w", encoding="utf-8") as f:
        f.writelines([example.strip() + '\n' for example in new_examples])
    return RedirectResponse(url="/", status_code=303)


@app.post("/generate-image", response_model=ImageOutput)
def generate_image(input_model: TextInput):
    """Generate an image for the provided text and save to IMAGE_PATH."""
    input_text = input_model.input_text

    # Check if the font file exists
    if not os.path.exists(FONT_PATH):
        generate_font_safely(FONT_PATH)

    # Create an image based on the text
    try:
        font = ImageFont.truetype(FONT_PATH, 40)  # Font size 40
        # Set image dimensions
        image_width = 800
        image_height = 200
        image = Image.new("RGB", (image_width, image_height), color="white")

        # Draw the text
        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), input_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (image_width - text_width) // 2
        text_y = (image_height - text_height) // 2

        draw.text((text_x, text_y), input_text, fill="black", font=font)
        image.save(IMAGE_PATH)

        return ImageOutput(image_path=IMAGE_PATH)
    except Exception as e:
        print(f"Error generating image: {e}")
        raise RuntimeError("Failed to generate the image.") from e