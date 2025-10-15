"""Career Chatbot - Hugging Face Spaces Entry Point"""

import os
import sys
from career_chatbot import CareerChatbot
from models import ChatbotConfig

def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create configuration
    config = ChatbotConfig(
        name="Ryan Griego",
        github_username=os.getenv("GITHUB_USERNAME", "ryan-griego")
    )
    
    # Initialize and launch chatbot
    chatbot = CareerChatbot(config)
    chatbot.launch_interface()

if __name__ == "__main__":
    main()
