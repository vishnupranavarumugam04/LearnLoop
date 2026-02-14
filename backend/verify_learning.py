import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
USER_NAME = f"testuser_{int(time.time())}"

def test_settings_persistence():
    print("Testing Settings Persistence...")
    # 1. Update settings
    settings = {"dark_mode": False, "high_contrast": True}
    res = requests.patch(f"{BASE_URL}/profile/{USER_NAME}", json={"settings": settings})
    print(f"PATCH Response ({res.status_code}): {res.text}")
    assert res.status_code == 200
    
    # 2. Verify retrieval
    res = requests.get(f"{BASE_URL}/profile/{USER_NAME}")
    data = res.json()
    print(f"Retrieved Settings: {data.get('settings')}")
    assert data['settings']['dark_mode'] == False
    assert data['settings']['high_contrast'] == True
    print("✅ Settings Persistence Works!")

def test_learning_flow():
    print("Testing Learning Flow...")
    # 1. Ensure user exists
    requests.get(f"{BASE_URL}/profile/{USER_NAME}")
    
    # 2. Upload a test material
    print("Uploading test material...")
    with open("test_v.txt", "w") as f:
        f.write("The capital of France is Paris. The solar system has 8 planets. Photosynthesis is the process by which plants make food.")
    
    with open("test_v.txt", "rb") as f:
        res = requests.post(f"{BASE_URL}/material/upload?user_id={USER_NAME}", files={"file": f})
    
    print(f"Upload Response: {res.status_code}")
    assert res.status_code == 200
    
    # 3. Verify 0 XP for generic chat
    res = requests.post(f"{BASE_URL}/buddy/chat", json={
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
        "user_id": USER_NAME
    })
    data = res.json()
    assert data['xp_gained'] == 0
    print("✅ Generic Chat gives 0 XP")

    # 4. Buddy Teach (Interaction about material)
    res = requests.post(f"{BASE_URL}/buddy/chat", json={
        "messages": [{"role": "user", "content": "Teach me about my material."}],
        "user_id": USER_NAME,
        "context": "test_v.txt"
    })
    data = res.json()
    print(f"Buddy Teach Response (+{data.get('xp_gained')} XP): {data['content'][:100]}...")
    assert data['xp_gained'] == 15
    print("✅ Buddy Teaching gives 15 XP")
    
    # 5. User Teaches Back (Reverse Learning)
    res = requests.post(f"{BASE_URL}/buddy/chat", json={
        "messages": [
            {"role": "user", "content": "I'll teach you. Basically, this concept is about how systems integrate with each other through well-defined interfaces and protocols, ensuring data consistency and reliability across the network."},
        ],
        "user_id": USER_NAME,
        "context": "test.txt" # Assuming a material was uploaded with this name
    })
    data = res.json()
    # Note: This might fail if no material found, but the logic should still award XP if detection works
    print(f"User Teach Response: {data['content']} (Gained: {data['xp_gained']} XP)")

if __name__ == "__main__":
    try:
        test_settings_persistence()
        test_learning_flow()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
