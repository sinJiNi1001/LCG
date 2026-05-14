import os
import requests
from dotenv import load_dotenv

# Import the Groq-powered AI function we built in ai_engine.py
from services.ai_engine import extract_linkedin_contact

load_dotenv()

# Safely grab the SerpAPI key regardless of how it's named in .env
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")

# 👇 1. Add target_location to the function parameters 👇
async def find_linkedin_contacts(company_name: str, target_roles: list, target_location: str) -> list:
    """
    Uses Google X-Ray searching to find actual employees on LinkedIn,
    then uses Groq AI to rigorously verify and extract their exact titles.
    """
    if not SERPAPI_API_KEY:
        print("⚠️ SERPAPI_API_KEY missing in .env. Cannot find contacts.")
        return []

    found_contacts = []
    
    print(f"🔍 Hunting for executives at {company_name} in {target_location}...")

    # We only look for the top 2 roles to save API credits
    for role in target_roles[:2]:
        
        # 👇 2. THE FIX: Inject the target_location into the Google query 👇
        query = f'site:linkedin.com/in/ "{role}" "{company_name}" "{target_location}"'
        
        url = "https://serpapi.com/search"
        # ... (the rest of your function stays exactly the same) ...
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "num": 1 # We only need the top result
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Did Google find a LinkedIn profile?
            if "organic_results" in data and len(data["organic_results"]) > 0:
                top_result = data["organic_results"][0]
                profile_url = top_result.get("link", "")
                
                # Make sure it's an actual profile, not a company page
                if "linkedin.com/in/" in profile_url:
                    
                    # Combine the title and snippet to give Groq maximum context
                    raw_title = top_result.get("title", "")
                    snippet = top_result.get("snippet", "")
                    full_text_to_analyze = f"{raw_title}\n{snippet}"
                    
                    # 👇 THE BRAIN TRANSPLANT: Pass the text to Groq for strict extraction 👇
                    extracted_data = await extract_linkedin_contact(full_text_to_analyze, target_roles)
                    
                    # Validate that Groq actually returned a valid JSON dict with a matching name & title
                    if extracted_data and extracted_data.get('name') and extracted_data.get('designation'):
                        print(f"   🎯 AI Verified: {extracted_data['name']} ({extracted_data['designation']})")
                        
                        found_contacts.append({
                            "name": extracted_data['name'],
                            "designation": extracted_data['designation'], # Uses the EXACT title Groq found
                            "linkedin_url": profile_url,
                            "relevance_score": 95, 
                            "rank": len(found_contacts) + 1
                        })
                    else:
                        # Groq's Bouncer rejected them! (e.g., they were an Android Dev, not a Sales Exec)
                        print(f"   🚫 AI Rejected Google Result for '{role}' (Title mismatch)")
                        
        except Exception as e:
            print(f"⚠️ Error finding {role} for {company_name}: {e}")

    return found_contacts