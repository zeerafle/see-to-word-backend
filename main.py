import base64
import os
from dotenv import load_dotenv

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


load_dotenv()


# Set the values for your Azure Cognitive Services account key and endpoint
try:
    endpoint = os.environ["AI_SERVICES_ENDPOINT"]
    key = os.environ["AI_SERVICES_KEY"]
except KeyError:
    print("Missing environment variable 'AI_SERVICES_ENDPOINT' or 'AI_SERVICES_KEY'")
    exit()

image_client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
translation_client = TextTranslationClient(endpoint=endpoint, credential=AzureKeyCredential(key))


app = FastAPI()


class ImageData(BaseModel):
    base64_image: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/describe")
def describe(image_data: ImageData):
    try:
        # decode the base64 string
        image_bytes = base64.b64decode(image_data.base64_image)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data")

    result = image_client.analyze(
        image_data=image_bytes,
        visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
    )

    # Convert analysis results into a JSON response
    response = {}
    text = ""

    # Process caption results
    if result.caption is not None:
        response["caption"] = {
            "text": result.caption.text,
            "confidence": round(result.caption.confidence, 4),
        }
        text = result.caption.text
    else:
        response["caption"] = None

    # Process OCR (read) results
    read_data = []
    high_confidence_words = []

    if result.read is not None:
        for block in result.read.blocks:
            for line in block.lines:
                line_data = {
                    "text": line.text,
                    "bounding_polygon": line.bounding_polygon,
                    "words": [],
                }
                for word in line.words:
                    conf = round(word.confidence, 4)
                    word_data = {
                        "text": word.text,
                        "bounding_polygon": word.bounding_polygon,
                        "confidence": conf
                    }
                    line_data["words"].append(word_data)
                    if conf > 0.8:
                        high_confidence_words.append(word.text)
                read_data.append(line_data)

    if read_data:
        text += f" and some text that says \"{' '.join(high_confidence_words)}\""

    response["read"] = read_data
    response["text"] = text

    # translate text to indonesian
    try:
        translation_result = translation_client.translate(
            [InputTextItem(text=text)],
            to=["id"],
            from_parameter="en"
        )
        translation = translation_result[0] if translation_result else None

        if translation:
            response["translation"] = translation.translations[0].text

    except HttpResponseError as e:
        if e.error is not None:
            print("HTTP error: " + e.error.message)
        raise

    return response
