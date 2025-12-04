"""
Automated test script for Set Game Server
Tests all protocol requirements:
1. User registration
2. Game room creation and listing
3. Entering a game
4. Getting field cards
5. Picking sets
6. Viewing scores
"""

import requests
import json
from typing import Dict, List

BASE_URL = "http://127.0.0.1:8000"


def print_test(name: str):
    """Print test section header."""
    print(f"\n{'=' * 60}")
    print(f"TEST: {name}")
    print('=' * 60)


def print_result(success: bool, message: str):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")


def test_registration():
    """Test user registration."""
    print_test("User Registration")
    
    # Register first player
    response = requests.post(f"{BASE_URL}/user/register", json={
        "nickname": "Alice",
        "password": "password123"
    })
    data = response.json()
    
    if data.get("success") and data.get("accessToken") and data.get("nickname") == "Alice":
        print_result(True, f"Alice registered with token: {data['accessToken'][:8]}...")
        alice_token = data["accessToken"]
    else:
        print_result(False, "Alice registration failed")
        return None, None
    
    # Register second player
    response = requests.post(f"{BASE_URL}/user/register", json={
        "nickname": "Bob",
        "password": "password456"
    })
    data = response.json()
    
    if data.get("success") and data.get("accessToken") and data.get("nickname") == "Bob":
        print_result(True, f"Bob registered with token: {data['accessToken'][:8]}...")
        bob_token = data["accessToken"]
    else:
        print_result(False, "Bob registration failed")
        return alice_token, None
    
    return alice_token, bob_token


def test_game_creation(token: str):
    """Test game room creation."""
    print_test("Game Room Creation")
    
    response = requests.post(f"{BASE_URL}/set/room/create", json={
        "accessToken": token
    })
    data = response.json()
    
    if data.get("success") and "gameId" in data:
        game_id = data["gameId"]
        print_result(True, f"Game room created with ID: {game_id}")
        return game_id
    else:
        print_result(False, "Game room creation failed")
        return None


def test_game_list(token: str):
    """Test listing game rooms."""
    print_test("Game Room Listing")
    
    response = requests.post(f"{BASE_URL}/set/room/list", json={
        "accessToken": token
    })
    data = response.json()
    
    if data.get("success") and "games" in data:
        games = data["games"]
        print_result(True, f"Found {len(games)} game(s): {games}")
        return True
    else:
        print_result(False, "Game listing failed")
        return False


def test_enter_game(token: str, game_id: int, player_name: str):
    """Test entering a game room."""
    print_test(f"Entering Game ({player_name})")
    
    response = requests.post(f"{BASE_URL}/set/room/enter", json={
        "accessToken": token,
        "gameId": game_id
    })
    data = response.json()
    
    if data.get("success") and data.get("gameId") == game_id:
        print_result(True, f"{player_name} entered game {game_id}")
        return True
    else:
        print_result(False, f"{player_name} failed to enter game")
        return False


def test_get_field(token: str, player_name: str):
    """Test getting field cards."""
    print_test(f"Getting Field Cards ({player_name})")
    
    response = requests.post(f"{BASE_URL}/set/field", json={
        "accessToken": token
    })
    data = response.json()
    
    if data.get("success") and "cards" in data:
        cards = data["cards"]
        status = data.get("status")
        score = data.get("score")
        print_result(True, f"Field has {len(cards)} cards, status: {status}, score: {score}")
        print(f"   Sample cards: {cards[:3]}")
        return cards
    else:
        print_result(False, "Failed to get field cards")
        return None


def find_valid_set(cards: List[Dict]) -> List[int]:
    """
    Try to find a valid set from the cards.
    This is a brute-force check of all 3-card combinations.
    """
    def is_valid_set(c1, c2, c3):
        def check_prop(v1, v2, v3):
            return (v1 == v2 == v3) or (v1 != v2 and v1 != v3 and v2 != v3)
        
        return (check_prop(c1["color"], c2["color"], c3["color"]) and
                check_prop(c1["shape"], c2["shape"], c3["shape"]) and
                check_prop(c1["fill"], c2["fill"], c3["fill"]) and
                check_prop(c1["count"], c2["count"], c3["count"]))
    
    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            for k in range(j + 1, len(cards)):
                if is_valid_set(cards[i], cards[j], cards[k]):
                    return [cards[i]["id"], cards[j]["id"], cards[k]["id"]]
    return None


def test_pick_set(token: str, cards: List[Dict], player_name: str):
    """Test picking a set."""
    print_test(f"Picking a Set ({player_name})")
    
    # Try to find a valid set
    valid_set = find_valid_set(cards)
    
    if valid_set:
        print(f"   Found valid set: {valid_set}")
        response = requests.post(f"{BASE_URL}/set/pick", json={
            "accessToken": token,
            "cards": valid_set
        })
        data = response.json()
        
        if data.get("success"):
            is_set = data.get("isSet")
            score = data.get("score")
            print_result(is_set, f"Set validation: isSet={is_set}, new score={score}")
            return is_set
        else:
            print_result(False, "Failed to pick set")
            return False
    else:
        # Try an invalid set for testing
        print("   No valid set found, testing with invalid set")
        invalid_set = [cards[0]["id"], cards[1]["id"], cards[2]["id"]]
        print(f"   Invalid set: {invalid_set}")
        
        response = requests.post(f"{BASE_URL}/set/pick", json={
            "accessToken": token,
            "cards": invalid_set
        })
        data = response.json()
        
        if data.get("success"):
            is_set = data.get("isSet")
            score = data.get("score")
            print_result(not is_set, f"Invalid set correctly rejected: isSet={is_set}, score={score}")
            return True
        else:
            print_result(False, "Failed to test invalid set")
            return False


def test_add_cards(token: str, player_name: str):
    """Test adding cards to field."""
    print_test(f"Adding Cards to Field ({player_name})")
    
    response = requests.post(f"{BASE_URL}/set/add", json={
        "accessToken": token
    })
    data = response.json()
    
    if data.get("success"):
        print_result(True, "Successfully added 3 cards to field")
        return True
    else:
        print_result(False, "Failed to add cards")
        return False


def test_scores(token: str):
    """Test getting scores."""
    print_test("Getting Scores")
    
    response = requests.post(f"{BASE_URL}/set/scores", json={
        "accessToken": token
    })
    data = response.json()
    
    if data.get("success") and "users" in data:
        users = data["users"]
        print_result(True, f"Retrieved scores for {len(users)} player(s)")
        for user in users:
            print(f"   {user['name']}: {user['score']} points")
        return True
    else:
        print_result(False, "Failed to get scores")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" SET GAME SERVER - AUTOMATED TEST SUITE")
    print("=" * 60)
    print(f"Testing server at: {BASE_URL}")
    
    try:
        # Test 1: Registration
        alice_token, bob_token = test_registration()
        if not alice_token or not bob_token:
            print("\n❌ Registration failed, cannot continue tests")
            return
        
        # Test 2: Game creation
        game_id = test_game_creation(alice_token)
        if game_id is None:
            print("\n❌ Game creation failed, cannot continue tests")
            return
        
        # Test 3: Game listing
        test_game_list(alice_token)
        
        # Test 4: Enter game (both players)
        if not test_enter_game(alice_token, game_id, "Alice"):
            print("\n❌ Alice failed to enter game, cannot continue tests")
            return
        test_enter_game(bob_token, game_id, "Bob")
        
        # Test 5: Get field cards
        cards = test_get_field(alice_token, "Alice")
        if not cards:
            print("\n❌ Failed to get cards, cannot continue tests")
            return
        
        # Test 6: Pick a set
        test_pick_set(alice_token, cards, "Alice")
        
        # Test 7: Add cards
        test_add_cards(alice_token, "Alice")
        
        # Test 8: Get updated field
        cards = test_get_field(alice_token, "Alice")
        
        # Test 9: Bob picks a set
        if cards:
            test_pick_set(bob_token, cards, "Bob")
        
        # Test 10: Get scores
        test_scores(alice_token)
        
        print("\n" + "=" * 60)
        print(" TEST SUITE COMPLETED")
        print("=" * 60)
        print("\n✅ All core functionality has been tested!")
        print("   Check the results above for details.\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn main:app --reload\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")


if __name__ == "__main__":
    main()
