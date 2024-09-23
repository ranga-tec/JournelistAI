import autogen
import streamlit as st
from textwrap import dedent
import requests
import json
import os
from typing import Tuple, Dict,Optional, Any
import datetime

# Set up the Streamlit app
st.set_page_config(page_title="AI Journalist Agent", page_icon="🗞️", layout="wide")
st.title("AI Journalist Agent 🗞️")
st.caption("Generate high-quality articles with AI Journalist using GPT-3.5-turbo and AutoGen")

# Sidebar for API keys
with st.sidebar:
    st.header("API Configuration")
    serp_api_key = st.text_input("Serper API Key", value=' ', type="password")

# Configuration for AutoGen
config_list = [{"model": "gpt-3.5-turbo", "api_key": os.environ.get("OPENAI_API_KEY")}]

def extract_content(chat_result: Any) -> Tuple[str, str]:
    """
    Extract the article content and editor feedback from the chat result.

    Args:
    chat_result (Any): The result object from the chat, containing chat history.

    Returns:
    Tuple[str, str]: A tuple containing the article content and editor feedback.
    """
    article_content: str = ""
    editor_feedback: str = ""
    for message in chat_result.chat_history:
        if isinstance(message, Dict):
            if message.get('name') == 'Writer' and 'content' in message:
                article_content = message['content']
            elif message.get('name') == 'Editor' and 'content' in message:
                editor_feedback = message['content']
                break  # Stop after getting editor's feedback
    return article_content, editor_feedback


def create_markdown_file(
    title: str,
    content: str,
    feedback: Optional[str] = None,
    output_dir: str = "generated_articles"
) -> str:
    """
    Create a Markdown file with the given title, content, and optional feedback.

    Args:
    title (str): The title of the article.
    content (str): The main content of the article.
    feedback (Optional[str]): The editor's feedback on the article. Defaults to None.
    output_dir (str): The directory where the file will be saved. Defaults to "generated_articles".

    Returns:
    str: The full path of the created Markdown file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() else "_" for c in title)
    filename = f"{safe_title}_{timestamp}.md"
    full_path = os.path.join(output_dir, filename)

    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("## Article Content\n\n")
        f.write(content)
        if feedback:
            f.write("\n\n## Editor's Feedback\n\n")
            f.write(feedback)

    return full_path

def search_google(query: str, num_results: int = 5):
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": num_results})
    headers = {
        'X-API-KEY': serp_api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        results = response.json()
        
        return [
            {
                "title": result['title'],
                "link": result['link'],
                "snippet": result.get('snippet', '')
            } 
            for result in results.get('organic', [])[:num_results]
        ]
    except requests.RequestException:
        return []

# Create AutoGen agents
user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    llm_config={"config_list": config_list},
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
    code_execution_config={"work_dir": "coding", "use_docker": False},
)


researcher = autogen.AssistantAgent(
    name="Researcher",
    llm_config={"config_list": config_list},
    system_message=dedent("""
    As an expert researcher:
    1. Generate 3-5 focused search queries based on the given topic.
    2. Use the search_google function to find relevant information.
    3. Analyze search results to identify the most relevant and credible sources.
    4. Summarize key findings and provide a list of the top 5 most relevant URLs.
    5. Highlight any potential controversies or multiple perspectives on the topic.
    Ensure all information is current and from reputable sources.
    After providing your research, end your message with: "RESEARCH COMPLETE"
    """)
)

writer = autogen.AssistantAgent(
    name="Writer",
    llm_config={"config_list": config_list},
    system_message=dedent("""
    As a senior journalist, craft a compelling, well-researched article:
    1. Synthesize information from the provided sources into a cohesive narrative.
    2. Structure with a strong lead, well-developed body, and impactful conclusion.
    3. Incorporate diverse perspectives and expert opinions.
    4. Use clear, engaging language suitable for a general audience.
    5. Ensure factual accuracy and provide proper attribution.
    6. Aim for 1500-2000 words, maintaining depth and engagement throughout.
    Adhere to the highest standards of journalistic integrity and quality.
    After writing the article, end your message with: "ARTICLE COMPLETE"
    """)
)

editor = autogen.AssistantAgent(
    name="Editor",
    llm_config={"config_list": config_list},
    system_message=dedent("""
    As the chief editor, ensure the article meets the highest journalistic standards:
    1. Evaluate structure, flow, and coherence.
    2. Verify multiple perspectives are fairly represented.
    3. Check factual accuracy and proper use of sources.
    4. Refine language for clarity, impact, and engagement.
    5. Ensure adherence to style guide and ethical standards.
    6. Provide constructive feedback for necessary revisions.
    7. Make the final decision on readiness for publication.
    Produce an informative, thought-provoking, and impactful article.
    After providing your feedback, end your message with: "FEEDBACK COMPLETE"
    """)
)

autogen.register_function(search_google, caller=researcher, executor=user_proxy, description="Search Google for information.")
autogen.register_function(create_markdown_file , caller=user_proxy, executor=user_proxy, description="create markdown file from the extracted content .")

autogen.register_function(extract_content , caller=user_proxy, executor=user_proxy, description="extract content from the editers content .")


# Create GroupChat and GroupChatManager
groupchat = autogen.GroupChat(
    agents=[user_proxy, researcher, writer, editor],
    messages=[],
    max_round=5,
    send_introductions=True,
    speaker_selection_method="round_robin",
)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})

# Streamlit UI
query = st.text_area("What topic would you like the AI journalist to write about?", value="latest ML news", height=100)

if st.button("Generate Article") and query and serp_api_key:
    with st.spinner("Researching and writing your article..."):
        chat_result = user_proxy.initiate_chat(manager, message=f"Write an article about {query}.")
        article_content, editor_feedback = extract_content(chat_result)

        if article_content:
            st.subheader("Generated Article:")
            st.markdown(article_content)
            
            st.download_button(
                label="Download Article",
                data=article_content,
                file_name="ai_generated_article.md",
                mime="text/markdown"
            )

            if editor_feedback:
                st.subheader("Editor's Feedback:")
                st.markdown(editor_feedback)
        else:
            st.error("An error occurred while generating the article. Please try again.")


# Add footer
st.markdown("---")
st.caption("Powered by AutoGen and GPT-3.5-turbo. Use responsibly and verify information independently.")