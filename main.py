import base64
import os
from dotenv import load_dotenv

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

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

client = ImageAnalysisClient(endpoint, AzureKeyCredential(key))

app = FastAPI()


class ImageData(BaseModel):
    base64_image: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/image-analysis")
def image_analysis(image_data: ImageData):
    try:
        # decode the base64 string
        image_bytes = base64.b64decode(image_data.base64_image)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image data")

    result = client.analyze(
        image_data=image_bytes,
        visual_features=[VisualFeatures.CAPTION, VisualFeatures.READ],
    )

    # Convert analysis results into a JSON response
    response = {}

    # Process caption results
    if result.caption is not None:
        response["caption"] = {
            "text": result.caption.text,
            "confidence": round(result.caption.confidence, 4),
        }
    else:
        response["caption"] = None

    # Process OCR (read) results
    read_data = []
    if result.read is not None:
        for block in result.read.blocks:
            for line in block.lines:
                line_data = {
                    "text": line.text,
                    "bounding_polygon": line.bounding_polygon,
                    "words": [],
                }
                for word in line.words:
                    word_data = {
                        "text": word.text,
                        "bounding_polygon": word.bounding_polygon,
                        "confidence": round(word.confidence, 4),
                    }
                    line_data["words"].append(word_data)
                read_data.append(line_data)
    response["read"] = read_data

    return response
