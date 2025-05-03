# main.py
import asyncio
import logging
import os
# import ast # No longer needed
from datetime import date # Import date
from typing import List

from scout import fetch_headlines, Headline
# Update analyst import to include the Pydantic model
from analyst import summarize_headlines, AnalystOutput
from commander import compose_email, generate_chart, send_email, EmailContent

# Import the response type for checking - only needed if NOT using response_model
# from mirascope.core.openai import OpenAICallResponse

# Set logging level back to INFO for cleaner output, or keep DEBUG if needed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define news sources (replace with your desired RSS feeds)
NEWS_SOURCES = {
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "NYT Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "Wired": "https://www.wired.com/feed/rss",
    # Add more sources as needed
}

async def run_pipeline():
    """Runs the full Scout -> Analyst -> Commander pipeline."""
    logging.info("Starting Recon Briefing Pipeline...")

    # --- Scout Phase ---
    logging.info("Deploying Scouts...")
    scout_tasks = [
        fetch_headlines(name, url) for name, url in NEWS_SOURCES.items()
    ]
    all_headlines_lists = await asyncio.gather(*scout_tasks)
    
    all_headlines: List[Headline] = [h for sublist in all_headlines_lists if sublist for h in sublist]
    
    if not all_headlines:
        logging.warning("No headlines fetched by Scouts. Pipeline terminating.")
        return

    logging.info(f"Scouts returned {len(all_headlines)} total headlines.")
    
    headlines_text = "\n".join(
        f"Source: {h.source}; Title: {h.title}; URL: {h.url}" + (f"; Summary: {h.summary}" if h.summary else "")
        for h in all_headlines
    )
    logging.debug(f"Formatted headlines for Analyst:\n{headlines_text}") # Keep DEBUG or change level

    # --- Analyst Phase (Using response_model) --- 
    logging.info("Sending headlines to Analyst for summarization...")
    summaries = None  # Initialize
    cluster_sizes = None # Initialize
    try:
        # The awaited call now directly returns the Pydantic model instance
        analysis_result: AnalystOutput = await summarize_headlines(headlines_text)
        
        # Validate and extract the summaries list and cluster sizes
        if not isinstance(analysis_result, AnalystOutput) or \
           not analysis_result.summaries or \
           not analysis_result.cluster_sizes or \
           len(analysis_result.summaries) != len(analysis_result.cluster_sizes):
             logging.warning(f"Analyst did not return a valid AnalystOutput object with matching summaries and cluster_sizes. Received: {analysis_result!r}. Cannot proceed.")
             return
        
        summaries = analysis_result.summaries # Assign the list of strings
        cluster_sizes = analysis_result.cluster_sizes # Assign the list of ints
        logging.info(f"Analyst processing complete. Found {len(summaries)} summary clusters with sizes: {cluster_sizes}")
        
    except Exception as e:
        logging.error(f"Analyst phase failed unexpectedly: {e}", exc_info=True) 
        return

    # Ensure we have summaries and sizes before proceeding
    if summaries is None or cluster_sizes is None:
        logging.error("Summaries or cluster_sizes variable is None after Analyst phase. Cannot proceed.")
        return

    # --- Commander Phase ---
    # Pass the PARSED summaries list to the commander
    logging.info("Sending summaries list to Commander for email composition...")
    try:
        # Pass the actual list of summary strings now
        email_content: EmailContent = await compose_email(summaries)
        
        if not isinstance(email_content, EmailContent):
            logging.error(f"Commander call did not return an EmailContent object as expected (received type: {type(email_content)}). Content: {email_content!r}. Cannot proceed.")
            return
            
        logging.info("Commander composed email content successfully.")
        
        # --- Post-process subject line for Date --- 
        today_str = date.today().strftime("%Y-%m-%d") 
        final_subject = email_content.subject.replace("[Current Date]", today_str)
        logging.info(f"Final email subject: {final_subject}")
        # --------------------------------------------

        # --- Generate Chart Data & Chart --- 
        # Pass the cluster_sizes list directly to generate_chart
        logging.info(f"Generating chart with cluster sizes: {cluster_sizes}")
        chart_file = generate_chart(cluster_sizes)
        # -----------------------------------

        # Use the final subject with the date included
        send_email(final_subject, email_content.body, chart_file)

    except Exception as e:
        logging.error(f"Commander phase failed: {e}", exc_info=True) 
        return

    logging.info("Recon Briefing Pipeline finished successfully.")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Please create a .env file with your key or set it manually.")
    else:
        asyncio.run(run_pipeline()) 
