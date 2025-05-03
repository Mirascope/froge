# analyst.py
import asyncio
import logging
from typing import List
from mirascope.core import openai  # Use specific provider module
from dotenv import load_dotenv
from pydantic import BaseModel, Field # Import Pydantic components

load_dotenv() # Load OPENAI_API_KEY from .env file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a Pydantic model for the analyst's structured output
class AnalystOutput(BaseModel):
    summaries: List[str] = Field(..., description="A list of concise summaries (3-5 bullet points each, formatted as single strings with \n for newlines) for distinct news topic clusters.")
    cluster_sizes: List[int] = Field(..., description="A list of integers representing the number of original headlines grouped into each corresponding summary cluster.")

# Use Mirascope V1 decorator API with the response_model
@openai.call(model="gpt-4o-mini", response_model=AnalystOutput)
async def summarize_headlines(headlines_text: str) -> AnalystOutput:
    """
    OBJECTIVE: Deduplicate and cluster the provided news headlines. For each distinct cluster/topic, 
               count the number of original headlines in that cluster and generate a concise 
               3-5 bullet point summary.

    INPUT HEADLINES:
    {headlines_text}

    TASK:
    1. Identify the distinct topic clusters in the input headlines.
    2. For each cluster, count how many headlines belong to it.
    3. For each cluster, generate a 3-5 bullet point summary (as a single string with \n newlines).
    4. Extract these summaries and their corresponding headline counts into the structure defined by the `AnalystOutput` model.
       Ensure the order of `summaries` matches the order of `cluster_sizes`. 
       Example: If cluster 1 has 5 headlines and cluster 2 has 3, the output might look like:
       `summaries`: ["- Summary for cluster 1...", "- Summary for cluster 2..."]
       `cluster_sizes`: [5, 3]
    """
    # The decorator handles the LLM call, using the docstring as the prompt
    # and automatically parsing the LLM response into the AnalystOutput model.
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
    logging.info("Analyst summarizing sample headlines (using response_model)...")
    try:
        # The awaited call now directly returns the Pydantic model instance
        analysis_result: AnalystOutput = await summarize_headlines(sample_headlines)

        print("\n--- Analyst Summaries (from response_model) ---")
        if analysis_result and isinstance(analysis_result, AnalystOutput) and analysis_result.summaries and analysis_result.cluster_sizes:
            if len(analysis_result.summaries) == len(analysis_result.cluster_sizes):
                for i, (summary, size) in enumerate(zip(analysis_result.summaries, analysis_result.cluster_sizes)):
                    print(f"Cluster {i+1} (Size: {size}) Summary:\n{summary}\n")
            else:
                print("Warning: Mismatch between number of summaries and cluster sizes reported.")
                print(f"Summaries: {analysis_result.summaries}")
                print(f"Cluster Sizes: {analysis_result.cluster_sizes}")
        else:
            print(f"No valid AnalystOutput generated. Received: {analysis_result!r}")
    except Exception as e:
        logging.error(f"Error during summarization: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 
