from agent.graph import code_agent


# main.py
def main():
    print("=== CODING AGENT ===\n")
    user_input = input("Enter your coding request:\n> ")
    
    # Pass as 'ticket_text' so nodes can use it
    result = code_agent.invoke({
        "user_query": user_input
    })
    
    print("\n=== AGENT OUTPUT ===")
    print(result["llm_result"])  # assuming your node sets this key


if __name__ == "__main__":
    main()

