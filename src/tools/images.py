import tempfile
from pathlib import Path
from openai import OpenAI
from PIL import Image
from src.schemas.image import ImageRequest, ImageResult
from src.settings import settings


def generate_image(request: ImageRequest) -> ImageResult:
    client = OpenAI(api_key=settings.openai_api_key)

    with open(request.seed_image_path, "rb") as image_file:
        seed_image = Image.open(image_file)

    style_prompt = {
        "photoreal": "photorealistic style",
        "watercolor": "watercolor painting style",
        "comic": "comic book illustration style"
    }[request.style]

    gender_age = f"{request.age} year old {request.gender}"

    prompt = f"Generate a full body portrait of a {gender_age} person in {style_prompt}. Base the appearance on the provided seed image but create a complete character illustration."

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_seed:
        seed_image.save(temp_seed.name, format="PNG")

        response = client.images.edit(
            image=open(temp_seed.name, "rb"),
            prompt=prompt,
            size="1024x1024"
        )

    output_path = Path(tempfile.mkdtemp()) / f"generated_{request.age}_{request.gender}_{request.style}.png"

    import requests
    img_data = requests.get(response.data[0].url).content
    with open(output_path, "wb") as f:
        f.write(img_data)

    params_used = {
        "style": request.style,
        "age": request.age,
        "gender": request.gender,
        "seed_image": request.seed_image_path
    }

    return ImageResult(image_path=str(output_path), params_used=params_used)