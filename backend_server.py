from fastapi import FastAPI, Query
from pydantic import BaseModel
import pandas as pd
import requests
from typing import Optional
import re

app = FastAPI()

LM_STUDIO_ENDPOINT = "http://172.19.25.17:1234/v1/chat/completions"
MODEL_NAME = "Hemanth-thunder/Tamil-Mistral-7B-Instruct-v0.1"

def load_csvs():
    soil_crop_nutrient_path = "dataset/Soil Type,Crop,Nutrient Requirement.csv"
    crops_path = "dataset/Crops.csv"
    soil_crop_nutrient_df = pd.read_csv(soil_crop_nutrient_path)
    crops_df = pd.read_csv(crops_path)
    return soil_crop_nutrient_df, crops_df

soil_crop_nutrient_df, crops_df = load_csvs()

def normalize_text(text):
    # Lowercase, remove punctuation, and normalize whitespace
    return re.sub(r'\W+', ' ', text.lower()).strip()

class ChatRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    max_tokens: int = 256

@app.get("/suitable-crops")
def suitable_crops(soil_type: str = Query(...)):
    df = crops_df[crops_df['Soil Type'].str.contains(soil_type, case=False, na=False)]
    if df.empty:
        return {"error": f"No data for soil type: {soil_type}"}
    return df[['Soil Type', 'Suitable Crops', 'Regions/Places']].to_dict(orient="records")

@app.get("/nutrient-requirements")
def nutrient_requirements(crop: str = Query(...)):
    df = soil_crop_nutrient_df[soil_crop_nutrient_df['Crop'].str.contains(crop, case=False, na=False)]
    if df.empty:
        return {"error": f"No data for crop: {crop}"}
    return df[['Soil Type', 'Crop', 'Required Ingredients', 'Nutrient Content (% by weight)']].to_dict(orient="records")

@app.get("/crop-regions")
def crop_regions(crop: str = Query(...)):
    df = crops_df[crops_df['Suitable Crops'].str.contains(crop, case=False, na=False)]
    if df.empty:
        return {"error": f"No data for crop: {crop}"}
    return df[['Soil Type', 'Suitable Crops', 'Regions/Places']].to_dict(orient="records")

@app.get("/soil-crop-nutrient-sample")
def soil_crop_nutrient_sample(n: int = 5):
    return soil_crop_nutrient_df.head(n).to_dict(orient="records")

@app.get("/crops-sample")
def crops_sample(n: int = 5):
    return crops_df.head(n).to_dict(orient="records")

@app.post("/chat")
def chat(req: ChatRequest):
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.prompt})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": req.max_tokens
    }
    response = requests.post(LM_STUDIO_ENDPOINT, json=payload)
    data = response.json()
    if "choices" in data and len(data["choices"]) > 0:
        return {"response": data["choices"][0]["message"]["content"]}
    return {"response": "No valid response from LLM."}

DEFAULT_SYSTEM_PROMPT = (
    "Always answer in the following format: "
    "Soil: <soil type> | Plant: <crop> | Nutrients: <nutrient info>. "
    "If multiple results, list each on a new line."
)

@app.post("/smart-chat")
def smart_chat(req: ChatRequest):
    context = ""
    prompt_norm = normalize_text(req.prompt) if req.prompt else ""
    # Add relevant crop/soil/nutrient info as context
    if req.prompt:
        # Check for soil types
        for soil_type in crops_df['Soil Type'].unique():
            soil_type_norm = normalize_text(str(soil_type))
            if soil_type_norm and soil_type_norm in prompt_norm:
                info = crops_df[crops_df['Soil Type'].str.lower() == soil_type.lower()]
                context += f"Crops for {soil_type}:\n" + info[['Suitable Crops', 'Regions/Places']].to_string(index=False) + "\n"
        # Check for crops
        for crop in soil_crop_nutrient_df['Crop'].unique():
            crop_norm = normalize_text(str(crop))
            if crop_norm and crop_norm in prompt_norm:
                info = soil_crop_nutrient_df[soil_crop_nutrient_df['Crop'].str.lower() == crop.lower()]
                context += f"Nutrient info for {crop}:\n" + info[['Soil Type', 'Required Ingredients', 'Nutrient Content (% by weight)']].to_string(index=False) + "\n"
    # Log the context for debugging
    print("Context sent to LLM:\n", context)
    # Compose the system prompt
    if req.system:
        system_prompt = req.system.strip() + "\n" + DEFAULT_SYSTEM_PROMPT
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    if context:
        system_prompt += "\nReference Data:\n" + context
    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": req.prompt})
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": req.max_tokens
    }
    response = requests.post(LM_STUDIO_ENDPOINT, json=payload)
    data = response.json()
    if "choices" in data and len(data["choices"]) > 0:
        return {"response": data["choices"][0]["message"]["content"]}
    return {"response": "No valid response from LLM."} 