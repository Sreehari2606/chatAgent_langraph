from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key="AIzaSyDJUeiaChgjI39eQbQEMhmV3ETG8A4iwOg", temperature=0.2)

def llm_invoke(prompt: str) -> dict:
    try:
        response = llm.invoke(prompt)
        return {"generate": response.content.strip()}
    except Exception as e:
        return {"generate": f"Error: {e}"}
