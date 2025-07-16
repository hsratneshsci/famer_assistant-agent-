import requests
import argparse
import sys

DEFAULT_LLM_ENDPOINT = "http://172.19.25.17:1234/v1/chat/completions"
DEFAULT_SMART_CHAT_ENDPOINT = "http://localhost:8000/smart-chat"
DEFAULT_MODEL = "Hemanth-thunder/Tamil-Mistral-7B-Instruct-v0.1"


def main():
    parser = argparse.ArgumentParser(description="Connect to LM Studio LLM or backend smart-chat and get a response.")
    parser.add_argument('--endpoint', type=str, help='API endpoint URL (overrides default)')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, help='Model name (as recognized by LM Studio)')
    parser.add_argument('--prompt', type=str, help='Prompt to send to the LLM')
    parser.add_argument('--system', type=str, help='System prompt to set behavior/context for the LLM')
    parser.add_argument('--max_tokens', type=int, default=256, help='Maximum tokens in the response')
    parser.add_argument('--smart', action='store_true', help='Use backend /smart-chat endpoint instead of direct LLM API')
    args = parser.parse_args()

    if not args.prompt:
        try:
            args.prompt = input("Enter your prompt: ")
        except KeyboardInterrupt:
            print("\nPrompt input cancelled.")
            sys.exit(0)
        if not args.prompt:
            print("Prompt is required.")
            sys.exit(1)

    if args.smart:
        endpoint = args.endpoint or DEFAULT_SMART_CHAT_ENDPOINT
        payload = {
            "prompt": args.prompt,
            "system": args.system,
            "max_tokens": args.max_tokens
        }
        print(f"Using backend smart-chat endpoint: {endpoint}")
    else:
        endpoint = args.endpoint or DEFAULT_LLM_ENDPOINT
        messages = []
        if args.system:
            messages.append({"role": "system", "content": args.system})
        messages.append({"role": "user", "content": args.prompt})
        payload = {
            "model": args.model,
            "messages": messages,
            "max_tokens": args.max_tokens
        }
        print(f"Using direct LLM endpoint: {endpoint}")

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if args.smart:
            print("\nSmart Chat Response:\n" + data.get('response', str(data)))
        else:
            if 'choices' in data and len(data['choices']) > 0:
                print("\nLLM Response:\n" + data['choices'][0]['message']['content'])
            else:
                print("No response from LLM.")
    except Exception as e:
        print(f"Error communicating with endpoint: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 