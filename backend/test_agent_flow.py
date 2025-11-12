from langgraph_kisaan_agents import image_retrieval_agent

# Simulate a KisaanAgentState with image queries
state = {
    "requires_images": True,
    "image_queries": ["Urea fertilizer bag India"],
    "image_context": "fertilizer_products"
}

result = image_retrieval_agent(state)
print("Image retrieval agent returned keys:", list(result.keys()))
print("image_urls:")
for img in result.get('image_urls', []):
    print("-", img.get('title'), img.get('url'))
