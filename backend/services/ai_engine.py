import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

# 1. HELPER FUNCTION TO LOAD PROMPTS
def load_prompt(filename: str) -> str:
    """Loads a text prompt from the backend/prompts directory."""
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', filename)
    with open(prompt_path, 'r', encoding='utf-8') as file:
        return file.read()

# 2. COMPANY ANALYZER
async def analyze_company_with_ai(company_name, company_url, website_text, sales_inputs, target_location):
    try:
        clean_text = website_text[:8000] 
        
        # Load the raw text and inject the variables
        raw_prompt = load_prompt('company_analyzer.txt')
        system_prompt = raw_prompt.replace("[SALES_INPUTS]", json.dumps(sales_inputs, indent=2)) \
                                  .replace("[COMPANY_URL]", company_url) \
                                  .replace("[WEBSITE_TEXT]", clean_text) \
                                  .replace("[TARGET_LOCATION]", target_location)
        
        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze: {company_name}"}
            ],
            response_format={"type": "json_object"}, 
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"⚠️ Groq Analysis Failed for {company_name}: {e}")
        return None

# 3. LINKEDIN EXTRACTOR 
async def extract_linkedin_contact(linkedin_snippet_text, target_roles, company_name, target_location):
    try:
        raw_prompt = load_prompt('linkedin_extractor.txt')
        
        # Inject all validation variables into the prompt
        system_prompt = raw_prompt.replace("[TARGET_ROLES]", json.dumps(target_roles)) \
                                  .replace("[LINKEDIN_SNIPPET]", linkedin_snippet_text) \
                                  .replace("[COMPANY_NAME]", company_name) \
                                  .replace("[TARGET_LOCATION]", target_location)

        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"⚠️ Groq Contact Extraction Failed: {e}")
        return {}