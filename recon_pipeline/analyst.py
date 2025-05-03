# analyst.py
import asyncio
import logging
from typing import List
from mirascope.core import openai  # Use specific provider module
from dotenv import load_dotenv

load_dotenv() # Load OPENAI_API_KEY from .env file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Use Mirascope V1 decorator API for the LLM call
@openai.call(model="gpt-4o-mini")
async def summarize_headlines(headlines_text: str) -> List[str]:
    """
    OBJECTIVE: Deduplicate and cluster the provided news headlines, then generate 
               a concise 3-5 bullet point summary for each distinct cluster/topic.

    INPUT HEADLINES:
    {headlines_text}

    OUTPUT FORMAT:
    Return ONLY a single, valid Python list literal containing strings. 
    Each string ELEMENT in the list should represent ONE topic cluster and contain 
    the complete 3-5 bullet point summary for that cluster AS A SINGLE MULTILINE STRING 
    (using '\n' for newlines between bullets).
    
    IMPORTANT:
    - Do NOT return a list of lists. Each element in the main list must be a string.
    - Do NOT include markdown fences (like ```python) or any text before or after the list literal.
    - Start the output directly with '[' and end it directly with ']'.
    
    Correct Example Output Structure:
    [
      "- Cluster 1: Point 1\n- Cluster 1: Point 2\n- Cluster 1: Point 3", 
      "- Cluster 2: Point A\n- Cluster 2: Point B",
      "- Cluster 3: Info X\n- Cluster 3: Info Y\n- Cluster 3: Info Z"
    ]
    """
    # The decorator handles the LLM call with the docstring as the prompt template
    # and the function arguments (`headlines_text`) inserted.
    # The return type annotation `-> List[str]` guides the LLM's output format.
    pass # Decorator handles the implementation

# Example usage for standalone testing
async def main():
    # Sample headlines (replace with actual fetched data if needed)
    sample_headlines = """
    Title: Market Hits Record High; Source: Financial Times; URL: example.com/1
    Title: Tech Stocks Surge After Chip Announcement; Source: Tech News; URL: example.com/2
    Title: Dow Jones Reaches New Peak Amid Economic Optimism; Source: WSJ; URL: example.com/3
    Title: New AI Chip Promises Breakthrough Performance; Source: AI Today; URL: example.com/4
    Title: Inflation Concerns Ease Slightly; Source: Bloomberg; URL: example.com/5
    Title: Market Rally Continues Unabated; Source: Reuters; URL: example.com/6
    """
    logging.info("Analyst summarizing sample headlines...")
    try:
        # Call returns a response object, not the direct content
        from mirascope.core.openai import OpenAICallResponse
        analyst_response: OpenAICallResponse = await summarize_headlines(sample_headlines)
        summaries: List[str] = analyst_response.content # Extract the list

        print("\n--- Analyst Summaries ---")
        if summaries and isinstance(summaries, list) and all(isinstance(s, str) for s in summaries):
            # Check that it's a list and all elements are strings
            for i, summary in enumerate(summaries):
                print(f"Cluster {i+1} Summary:\n{summary}\n")
        else:
            print(f"No valid list of strings generated. Received: {summaries}")
    except Exception as e:
        logging.error(f"Error during summarization: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
