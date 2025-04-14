import json
import gradio as gr
from rapidfuzz import fuzz, process
import difflib

# --------------------------
# Load the dataset
# --------------------------
with open("search.json", "r") as f:
    schemes = json.load(f)

# --------------------------
# Keyword Sets
# --------------------------

# Greetings to ignore
greetings = ["hi", "hello", "hey", "namaste", "good morning", "good evening", "greetings"]

# List of Indian states and UTs
states = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry",
    "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep",
    "Andaman and Nicobar Islands"
]

# Synonyms to map to common categories
keyword_synonyms = {
    "education": ["school", "college", "student", "scholarship", "study", "learning"],
    "health": ["hospital", "medical", "doctor", "insurance", "treatment", "clinic"],
    "farming": ["agriculture", "farmer", "crop", "irrigation", "tractor", "kisan"],
    "finance": ["money", "loan", "subsidy", "pension", "support", "fund", "bank"],
    "employment": ["job", "work", "skill", "training", "internship"],
    "housing": ["home", "house", "shelter", "pradhan mantri awas", "pmay"],
}

# Flatten synonyms for reverse lookup
synonym_map = {syn: key for key, synonyms in keyword_synonyms.items() for syn in synonyms}


# --------------------------
# Query Normalization
# --------------------------

def normalize_query(query):
    query = query.lower()
    words = query.split()

    # Remove greetings
    words = [word for word in words if word not in greetings]

    # Replace synonyms
    normalized = [synonym_map.get(word, word) for word in words]

    # Match state using fuzzy match
    matched_state = process.extractOne(query, states, scorer=fuzz.partial_ratio)
    if matched_state and matched_state[1] > 75:
        normalized.append(matched_state[0].lower())  # add matched state

    return " ".join(normalized)


# --------------------------
# Search Logic
# --------------------------

def search_scheme(query):
    query = normalize_query(query)
    results = []

    for scheme in schemes:
        # Lowercase fields
        name = scheme["name"].lower()
        state = scheme["state"].lower()
        category = scheme["category"].lower()
        description = scheme["description"].lower()

        # Weighted fuzzy matching
        name_score = fuzz.token_sort_ratio(query, name)
        category_score = fuzz.partial_ratio(query, category)
        state_score = fuzz.partial_ratio(query, state)
        description_score = fuzz.partial_ratio(query, description)

        total_score = (
            0.4 * name_score +
            0.25 * category_score +
            0.2 * state_score +
            0.15 * description_score
        )

        if total_score > 50:
            results.append((total_score, scheme))

    # Sort results by score
    results.sort(key=lambda x: x[0], reverse=True)

    # Format results
    if results:
        return "\n\n".join([
            f"**{item['name']}** ({item['state']})\n"
            f"**Category**: {item['category'].title()}\n"
            f"{item['description']}\n"
            f"[🔗 Link]({item['link']})"
            for _, item in results[:5]
        ])
    else:
        # Try spelling correction fallback
        correction = difflib.get_close_matches(query, [s["name"].lower() for s in schemes], n=1)
        if correction:
            return f"No exact match found. Did you mean **{correction[0]}**?"
        return "No relevant schemes found. Try using different or simpler keywords."


# --------------------------
# Gradio UI
# --------------------------

iface = gr.Interface(
    fn=search_scheme,
    inputs=gr.Textbox(label="Ask about a government scheme"),
    outputs=gr.Markdown(label="Search Results"),
    title="Government Scheme Search",
    description="Search for Indian central and state government schemes using natural language. Handles typos, greetings, and synonyms like 'student', 'hospital', or 'farmer'."
)

iface.launch()
