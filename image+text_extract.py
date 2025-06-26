import os
import pandas as pd
import spacy
import json
import re
from tqdm import tqdm
from deepface import DeepFace
import requests

# ----------- 配置路径 -----------
img_path = "data/images"
profile_path = "data/profile"
outpath = "output"
os.makedirs(outpath, exist_ok=True)

# ----------- 图像识别：提取性别和种族信息 -----------
def analyze_images():
    results = []
    for filename in os.listdir(img_path):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            path = os.path.join(IMG_DIR, filename)
            try:
                obj = DeepFace.analyze(img_path=path, actions=['gender', 'race'], enforce_detection=False)
                results.append({
                    "filename": filename,
                    "gender": obj[0]["dominant_gender"],
                    "race": obj[0]["dominant_race"]
                })
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    df_img = pd.DataFrame(results)
    df_img.to_csv(os.path.join(outpath, "demographic_predictions.csv"), index=False)
    return df_img

# ----------- NLP信息抽取部分 -----------
API_KEY = "api-key" 
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def build_prompt(text):
    return f"""
You are a helpful assistant. Extract the following structured fields from the self-introduction text:

1. Institution – the university or research institution the person is affiliated with.
2. Identity – academic role such as PhD student, faculty member, postdoc, etc.
3. Discipline – the formal academic discipline(s), such as Sociology, Political Science, Computer Science.
4. Research interests – specific research topics or methods mentioned.
5. Publications – only peer-reviewed academic journal names.

⚠️ Do NOT fabricate or infer any information. Extract only what is clearly stated in the original text.
⚠️ If any field is not mentioned, return null.

Text:
\"\"\"{text}\"\"\"

Return the result strictly as a JSON object using lowercase keys:
"institution", "identity", "discipline", "research_interests", "publications"
"""

def extract_fields_from_bio(text):
    prompt = build_prompt(text)
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a structured information extraction assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, data=json.dumps(payload))
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ API error: {e}")
        return "{}"

def clean_and_parse_json_strict(text):
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON found")
        json_text = match.group(0)
        return json.loads(json_text)
    except Exception as e:
        print(f"❌ Error parsing JSON: {e}")
        return {}

def standardize_list_field(x):
    if isinstance(x, str):
        if ',' in x or ';' in x:
            return [d.strip() for d in re.split(r'[;,]', x)]
        else:
            return [x.strip()] 
    elif isinstance(x, list):
        return [str(i).strip() for i in x] 
    else:
        return None

# ----------- 主批量处理逻辑：对每个 CSV 文件做结构抽取 -----------
def process_profiles():
    nlp = spacy.load("en_core_web_sm")

    for file in os.listdir(profile_path):
        if file.endswith(".csv"):
            filepath = os.path.join(profile_path, file)
            df = pd.read_csv(filepath)

            tqdm.pandas()
            df["structured_info"] = df["bio"].progress_apply(extract_fields_from_bio)
            df["cleaned"] = df["structured_info"].apply(clean_and_parse_json_strict)
            
            df["Institution"] = df["cleaned"].apply(lambda x: standardize_list_field(x.get('institution', None)))
            df["Identity"] = df["cleaned"].apply(lambda x: standardize_list_field(x.get('identity', None)))
            df["Discipline"] = df["cleaned"].apply(lambda x: standardize_list_field(x.get('discipline', None)))
            df["Research_interests"] = df["cleaned"].apply(lambda x: standardize_list_field(x.get('research_interests', None)))
            df["Publication"] = df["cleaned"].apply(lambda x: standardize_list_field(x.get('publications', None)))

            output_name = os.path.splitext(file)[0] + "_structured.csv"
            df.to_csv(os.path.join(outpath, output_name), index=False)

# ------------------ 执行所有任务 ------------------
if __name__ == "__main__":
    print("Step 1: Analyzing images...")
    analyze_images()

    print("Step 2: Extracting profile information...")
    process_profiles()

    print("All outputs saved to:", outpath)
