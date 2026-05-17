"""Check which models are currently loaded in LLM servers (LM Studio or OLLAMA)."""
import requests
import json
import sys

# Server configurations
SERVERS = {
    "LM Studio": "http://127.0.0.1:1234/v1/models",
    "OLLAMA": "http://127.0.0.1:8001/v1/models",
    "OLLAMA (default)": "http://127.0.0.1:11434/v1/models"
}

def check_server(name, url):
    """Check a single server for loaded models."""
    try:
        print(f"\n{'=' * 60}")
        print(f"Checking {name}")
        print(f"{'=' * 60}")
        print(f"URL: {url}")
        print()
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        print("Response:")
        print(json.dumps(data, indent=2))
        print()
        
        if "data" in data:
            models = data["data"]
            print(f"{'=' * 60}")
            print(f"✅ {name} is RUNNING")
            print(f"Found {len(models)} model(s) loaded:")
            print(f"{'=' * 60}")
            
            for i, model in enumerate(models, 1):
                print(f"\n{i}. Model ID: {model.get('id', 'Unknown')}")
                print(f"   Object: {model.get('object', 'Unknown')}")
                print(f"   Created: {model.get('created', 'Unknown')}")
                print(f"   Owned by: {model.get('owned_by', 'Unknown')}")
                
                # Check if this is the 4B or 9B model
                model_id = model.get('id', '').lower()
                if '4b' in model_id:
                    print("   ✅ This is a 4B model (GOOD - fast and efficient)")
                elif '9b' in model_id:
                    print("   ⚠️  This is a 9B model (larger, slower)")
                elif '3b' in model_id:
                    print("   ℹ️  This is a 3B model (very fast, less capable)")
                else:
                    print("   ℹ️  Model size unclear from ID")
            
            return True
        else:
            print("⚠️  No 'data' field in response")
            return False
        
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is NOT RUNNING")
        print(f"   Cannot connect to {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"⏱️  {name} request timed out")
        print(f"   Server may be loading a model")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Check all configured servers."""
    print("\n" + "=" * 60)
    print("LLM Server Model Checker")
    print("=" * 60)
    print("Checking all configured servers...")
    
    running_servers = []
    
    for name, url in SERVERS.items():
        if check_server(name, url):
            running_servers.append(name)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if running_servers:
        print(f"✅ Running servers: {', '.join(running_servers)}")
        print()
        print("To use a specific server, update your .env file:")
        print("  LLM_BASE_URL=http://127.0.0.1:1234/v1  # For LM Studio")
        print("  LLM_BASE_URL=http://127.0.0.1:8001/v1  # For OLLAMA (port 8001)")
        print("  LLM_BASE_URL=http://127.0.0.1:11434/v1 # For OLLAMA (default port)")
    else:
        print("❌ No servers are running")
        print()
        print("To start a server:")
        print("  • LM Studio: Open the app and load a model")
        print("  • OLLAMA: Run 'ollama serve' and load a model")
    
    print()
    print("Recommended model: Qwen3.5-4B-MLX-4bit")
    print("  - Good balance of speed and quality")
    print("  - Works well with reasoning disabled")
    print("  - Fits in ~3GB RAM")
    print()

if __name__ == "__main__":
    main()

# Made with Bob
