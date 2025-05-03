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
import numpy as np # Import numpy for range

load_dotenv() # Load API keys and SMTP config from .env

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Pydantic Model for Structured LLM Output (Simplified) ---
class EmailContent(BaseModel):
    subject: str = Field(..., description="A concise and informative email subject line including the [Current Date] placeholder.")
    body: str = Field(..., description="The main email body formatted in Markdown, including all summaries.")
    # chart_data field removed

# --- LLM Call for Email Composition (Simplified) ---
@openai.call(model="gpt-4o-mini", response_model=EmailContent)
async def compose_email(summaries: List[str]) -> EmailContent:
    """
    OBJECTIVE: Compose a mission-brief style email summarizing the provided intelligence summaries.

    INPUT SUMMARIES (as a Python list of strings):
    The input is a list where each string element represents a topic cluster summary 
    containing multiple bullet points (using \n for newlines).
    ```
    {summaries}
    ```

    TASK:
    1. Review the provided list of summary strings.
    2. Create a concise overall subject line (e.g., "Daily Recon Briefing - [Current Date]"). Ensure you include the exact placeholder "[Current Date]".
    3. Write an engaging email body in Markdown format:
        - Start with a brief intro (e.g., "Good morning, here is today's intelligence briefing:").
        - For each summary string in the input list, format it clearly in the email body, perhaps with a heading like "Topic Cluster X:".
        - Add a brief concluding sentence.
    4. Return ONLY the subject (containing the '[Current Date]' placeholder) and body,
       strictly conforming to the simplified `EmailContent` Pydantic model.
    """
    pass # Decorator handles the implementation


# --- Chart Generation ---
def generate_chart(cluster_sizes: List[int], output_path: str = "recon_chart.png") -> Optional[str]:
    """Generates a scatter plot of headlines per cluster and saves it."""
    if not cluster_sizes or not isinstance(cluster_sizes, list) or not all(isinstance(size, int) and size >= 0 for size in cluster_sizes):
        logging.warning(f"Invalid cluster_sizes data received: {cluster_sizes}. Skipping chart.")
        return None
    
    num_clusters = len(cluster_sizes)
    cluster_indices = np.arange(1, num_clusters + 1) # X-axis: 1, 2, 3...
    headline_counts = np.array(cluster_sizes)         # Y-axis: Counts per cluster

    logging.info(f"Generating scatter plot for {num_clusters} clusters with sizes: {headline_counts}...")
    
    try:
        fig, ax = plt.subplots(figsize=(max(6, num_clusters * 0.5), 5)) # Adjust width based on cluster count
        ax.scatter(cluster_indices, headline_counts, s=100) # Use scatter plot, s is marker size
        
        ax.set_xlabel("Cluster Index")
        ax.set_ylabel("Number of Headlines")
        ax.set_title("Recon Briefing: Headlines per Cluster")
        
        # Ensure x-axis shows integer ticks for each cluster index
        ax.set_xticks(cluster_indices)
        ax.set_xlim(0.5, num_clusters + 0.5)
        
        # Ensure y-axis starts at 0 and shows integer ticks if max count is small
        ax.set_ylim(bottom=0)
        if headline_counts.max() <= 10:
             ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close(fig) 
        logging.info(f"Scatter plot saved to {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Failed to generate scatter plot: {e}", exc_info=True)
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

    msg.attach(MIMEText(body_html.replace("\n", "<br>"), 'html'))

    if chart_path and os.path.exists(chart_path):
        logging.info(f"Attaching chart image: {chart_path}")
        try:
            with open(chart_path, 'rb') as fp:
                img = MIMEImage(fp.read())
            img.add_header('Content-ID', '<recon_chart>') 
            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(chart_path))
            msg.attach(img)
        except Exception as e:
            logging.error(f"Error attaching chart image {chart_path}: {e}")

    try:
        logging.info(f"Connecting to SMTP server {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() 
            server.login(smtp_user, smtp_password)
            logging.info(f"Sending email to {', '.join(recipient_emails)}")
            server.sendmail(smtp_user, recipient_emails, msg.as_string())
            logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email via SMTP: {e}")


# Example usage for standalone testing
async def main():
    # Use a list of strings for testing now
    sample_summaries = [
        "- Summary 1, point 1\n- Summary 1, point 2",
        "- Summary 2, point A\n- Summary 2, point B"
    ]
    logging.info("Commander composing email from sample summaries list...")
    try:
        # Since response_model is used, the awaited result *is* the model instance
        email_content: EmailContent = await compose_email(sample_summaries)

        if not isinstance(email_content, EmailContent):
            logging.error(f"Commander test did not return valid EmailContent object (received type: {type(email_content)}). Content: {email_content!r}.")
            return

        print("\n--- Generated Email Content (from LLM) ---")
        print(f"Subject: {email_content.subject}")
        print(f"Body:\n{email_content.body}")

        # Post-process subject for date (Example for testing)
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d")
        final_subject = email_content.subject.replace("[Current Date]", today_str)
        print(f"Final Subject: {final_subject}")

        # Manually create chart data for testing chart generation
        test_cluster_sizes = [5, 3] # Example sizes matching sample_summaries length
        print(f"Test Cluster Sizes: {test_cluster_sizes}")
        chart_file = generate_chart(test_cluster_sizes)

        send_email(final_subject, email_content.body, chart_file)

    except Exception as e:
        logging.error(f"Error during email composition or sending: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 
