# AI Journalist Agent

This project implements an AI-powered journalist agent using AutoGen and GPT-3.5-turbo to generate high-quality articles on various topics.

## Features

- Automated article generation on any given topic
- Uses a team of AI agents: Researcher, Writer, and Editor
- Integrates with Google Search API for up-to-date information
- Streamlit-based user interface for easy interaction
- Generates downloadable Markdown files of the articles

## Prerequisites

- Python 3.7+
- OpenAI API key
- Serper API key (for Google Search integration)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ai-journalist-agent.git
   cd ai-journalist-agent
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     SERPAPI_API_KEY=your_serper_api_key_here
     ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run news_reporter.py
   ```

2. Open your web browser and go to the URL provided by Streamlit (usually `http://localhost:8501`)

3. Enter a topic in the text area and click "Generate Article"

4. Wait for the AI to research, write, and edit the article

5. Once complete, you can view the article in the browser and download it as a Markdown file

## Project Structure

- `news_reporter.py`: Main script containing the Streamlit app and AI agent logic
- `requirements.txt`: List of Python package dependencies
- `generated_articles/`: Directory where generated Markdown files are saved

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
