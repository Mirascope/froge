# commander.py
import asyncio
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import List, Dict, Any, Optional
from mirascope.core import openai # Use specific provider module
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv() # Load API keys and SMTP config from .env

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Pydantic Model for Structured LLM Output ---
class EmailContent(BaseModel):
    subject: str = Field(..., description="A concise and informative email subject line.")
    body: str = Field(..., description="The main email body formatted in Markdown, including all summaries.")
    chart_data: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Data for chart generation. Expected format: {'summary_count': <integer>}"
    )

# --- LLM Call for Email Composition ---
# Update signature to accept raw_summaries_string: str
@openai.call(model="gpt-4o-mini", response_model=EmailContent)
async def compose_email(raw_summaries_string: str) -> EmailContent:
    """
    OBJECTIVE: Compose a mission-brief style email summarizing the provided intelligence summaries.

    INPUT SUMMARIES (as a string potentially representing a Python list):
    The following string contains multiple summaries, likely formatted as a Python list of strings.
    Each element represents a topic cluster with bullet points (using \n for newlines).
    You need to parse/interpret this string to extract the individual summaries.
    ```
    {raw_summaries_string}
    ```

    TASK:
    1. Interpret the input string to identify each distinct summary cluster.
    2. Create a concise overall subject line (e.g., "Daily Recon Briefing - [Current Date]"). Ensure you include the exact placeholder "[Current Date]".
    3. Write an engaging email body in Markdown format:
        - Start with a brief intro (e.g., "Good morning, here is today's intelligence briefing:").
        - For each distinct summary identified from the input string, format it clearly in the email body, perhaps with a heading like "Topic Cluster X:".
        - Add a brief concluding sentence.
    4. Count the total number of distinct summary clusters you identified from the input string.
    5. Return the subject (containing the '[Current Date]' placeholder), body, and chart data (containing the summary count) 
       according to the `EmailContent` Pydantic model.
       Example chart_data: {{"summary_count": 3}}
    """
    pass # Decorator handles the implementation


# --- Chart Generation ---
def generate_chart(chart_data: Dict[str, Any], output_path: str = "recon_chart.png") -> Optional[str]:
    """Generates a simple bar chart and saves it."""
    summary_count = chart_data.get("summary_count", 0)
    if not isinstance(summary_count, int) or summary_count <= 0:
        logging.warning(f"Invalid or missing 'summary_count' in chart_data: {chart_data}. Skipping chart.")
        return None
    
    logging.info(f"Generating chart for {summary_count} summary clusters...")
    try:
        fig, ax = plt.subplots()
        # Simple chart: bar showing the number of clusters/summaries
        ax.bar(["Summary Clusters"], [summary_count]) 
        ax.set_ylabel("Count")
        ax.set_title("Recon Briefing: Summary Volume")
        # Ensure y-axis starts at 0 and has integer ticks if count is small
        ax.set_ylim(bottom=0)
        if summary_count <= 10:
             ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close(fig) # Close the plot to free memory
        logging.info(f"Chart saved to {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Failed to generate chart: {e}")
        return None

# --- Email Sending ---
def send_email(subject: str, body_html: str, chart_path: Optional[str]):
    """Sends the email using SMTP settings from .env"""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_emails_str = os.getenv("RECIPIENT_EMAILS", "")
    
    if not all([smtp_server, smtp_user, smtp_password, recipient_emails_str]):
        logging.warning("SMTP configuration incomplete in .env. Printing email to console instead.")
        print("\n--- Email Content ---")
        print(f"Subject: {subject}")
        print("\n--- Body ---")
        # Basic conversion from Markdown (or just print the raw string from LLM)
        print(body_html) 
        if chart_path:
             print(f"\n(Chart generated at: {chart_path})")
        print("\n--- End Email Content ---")
        return

    recipient_emails = [email.strip() for email in recipient_emails_str.split(',')]
    if not recipient_emails:
         logging.warning("No recipient emails found in .env configuration.")
         return

    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = ", ".join(recipient_emails)

    # Attach HTML body
    # Assume LLM returns Markdown; basic conversion or send as plain text if needed
    # For simplicity, we'll embed the Markdown directly as HTML body content
    # A proper solution might use a Markdown-to-HTML library
    msg.attach(MIMEText(body_html.replace("\n", "<br>"), 'html')) # Simple newline->br conversion

    # Attach chart image
    if chart_path and os.path.exists(chart_path):
        logging.info(f"Attaching chart image: {chart_path}")
        try:
            with open(chart_path, 'rb') as fp:
                img = MIMEImage(fp.read())
            img.add_header('Content-ID', '<recon_chart>') # Referenced in HTML if needed
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(chart_path))
            msg.attach(img)
        except Exception as e:
            logging.error(f"Error attaching chart image {chart_path}: {e}")
            # Optionally add a note about the missing chart to the body

    # Send the email
    try:
        logging.info(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() # Enable security
            server.login(smtp_user, smtp_password)
            logging.info(f"Sending email to {', '.join(recipient_emails)}")
            server.sendmail(smtp_user, recipient_emails, msg.as_string())
            logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email via SMTP: {e}")


# Example usage for standalone testing
async def main():
    # Simulate the raw string output from Analyst
    # Note: Ensure quotes within the string are handled if testing complex cases
    sample_raw_summaries_string = '''[
        "- Market reached a new record high today.\n- Tech stocks led the surge.\n- Economic optimism fueled the rally.",
        "- A new AI chip was announced, promising significant performance gains."
    ]'''
    logging.info("Commander composing email from sample raw string...")
    try:
        # Call returns a response object
        from mirascope.core.openai import OpenAICallResponse
        commander_response: OpenAICallResponse = await compose_email(sample_raw_summaries_string)
        email_content: EmailContent = commander_response.content # Extract the Pydantic model

        # Validate the extracted content
        if not isinstance(email_content, EmailContent):
            logging.error(f"Commander test did not return valid EmailContent object (received type: {type(email_content)}). Content: {email_content!r}.")
            return

        print("\n--- Generated Email Content (from LLM) ---")
        print(f"Subject: {email_content.subject}")
        print(f"Body:\n{email_content.body}")
        print(f"Chart Data: {email_content.chart_data}")

        # Post-process subject for date (Example for testing)
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")
        final_subject = email_content.subject.replace("[Current Date]", today_str)
        print(f"Final Subject: {final_subject}")

        chart_file = generate_chart(email_content.chart_data)
        send_email(final_subject, email_content.body, chart_file)

        if chart_file and os.path.exists(chart_file):
             try:
                 os.remove(chart_file)
                 logging.info(f"Cleaned up chart file: {chart_file}")
             except OSError as e:
                  logging.warning(f"Could not remove chart file {chart_file}: {e}")

    except Exception as e:
        logging.error(f"Error during email composition or sending: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 
