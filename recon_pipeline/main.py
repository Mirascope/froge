# main.py
import asyncio
import logging
import os
import ast # Import the ast module for literal_eval
from datetime import date # Import date
from typing import List

from scout import fetch_headlines, Headline
from analyst import summarize_headlines
from commander import compose_email, generate_chart, send_email, EmailContent

# Import the response type for checking
from mirascope.core.openai import OpenAICallResponse 

# Set logging level to DEBUG to see more details
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    logging.debug(f"Formatted headlines for Analyst:\n{headlines_text}")

    # --- Analyst Phase ---
    logging.info("Sending headlines to Analyst for summarization...")
    raw_content_from_analyst = None # Initialize
    try:
        analyst_response: OpenAICallResponse = await summarize_headlines(headlines_text)
        raw_content_from_analyst = analyst_response.content # Extract the raw content (likely a string)
        
        logging.debug(f"Analyst raw response content type: {type(raw_content_from_analyst)}")
        logging.debug(f"Analyst raw response content value: {raw_content_from_analyst!r}")

        if not raw_content_from_analyst or not isinstance(raw_content_from_analyst, str):
            logging.warning(f"Analyst did not return a non-empty string (received type: {type(raw_content_from_analyst)}). Content: {raw_content_from_analyst!r}. Cannot proceed.")
            return
            
        logging.info(f"Analyst returned raw content successfully.")
        
    except Exception as e:
        logging.error(f"Analyst phase failed unexpectedly: {e}", exc_info=True) 
        return

    # --- Commander Phase ---
    logging.info("Sending raw analyst output string to Commander for email composition...")
    try:
        # Pass the raw string content here.
        # Since compose_email uses response_model=EmailContent, the awaited result
        # IS the EmailContent object directly (or raises error on parse failure).
        email_content: EmailContent = await compose_email(raw_content_from_analyst)
        
        # Validate the type of the direct result.
        if not isinstance(email_content, EmailContent):
            # This case might indicate an unexpected return type or LLM failure 
            # that didn't conform to the Pydantic model despite the response_model hint.
            logging.error(f"Commander call did not return an EmailContent object as expected (received type: {type(email_content)}). Content: {email_content!r}. Cannot proceed.")
            return
            
        logging.info("Commander composed email content successfully.")
        
        # --- Post-process subject line for Date --- 
        today_str = date.today().strftime("%Y-%m-%d") 
        final_subject = email_content.subject.replace("[Current Date]", today_str)
        logging.info(f"Final email subject: {final_subject}")
        # --------------------------------------------

        chart_file = generate_chart(email_content.chart_data)
        
        # Use the final subject with the date included
        send_email(final_subject, email_content.body, chart_file)

        if chart_file and os.path.exists(chart_file):
             try:
                 os.remove(chart_file)
                 logging.info(f"Cleaned up chart file: {chart_file}")
             except OSError as e:
                  logging.warning(f"Could not remove chart file {chart_file}: {e}")

    except Exception as e:
        # This will catch errors during the compose_email call (like parsing failures)
        # or errors during chart generation/sending.
        logging.error(f"Commander phase failed: {e}", exc_info=True) 
        return

    logging.info("Recon Briefing Pipeline finished successfully.")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Please create a .env file with your key or set it manually.")
    else:
        asyncio.run(run_pipeline()) 
