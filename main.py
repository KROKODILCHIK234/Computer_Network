import uuid
import random
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Set Game Server")


# ==================== Data Models ====================

class Card(BaseModel):
    id: int
    count: int
    shape: int
    fill: int
    color: int


class RegisterRequest(BaseModel):
    nickname: str
    password: str


class CreateRoomRequest(BaseModel):
    accessToken: str


class ListRoomRequest(BaseModel):
    accessToken: str


class EnterRoomRequest(BaseModel):
    accessToken: str
    gameId: int


class FieldRequest(BaseModel):
    accessToken: str


class PickRequest(BaseModel):
    accessToken: str
    cards: List[int]


class AddCardsRequest(BaseModel):
    accessToken: str


class ScoresRequest(BaseModel):
    accessToken: str


class ExceptionResponse(BaseModel):
    message: str


class BaseResponse(BaseModel):
    success: bool
    exception: Optional[ExceptionResponse] = None


# ==================== Game Logic ====================

class GameRoom:
    def __init__(self, game_id: int):
        self.game_id = game_id
        self.deck: List[Card] = []
        self.field: List[Card] = []
        self.players: Dict[str, int] = {}  # accessToken -> score
        self.status = "ongoing"
        self._initialize_deck()
        self._deal_initial_cards()

    def _initialize_deck(self):
        """Create a full deck of 81 Set cards."""
        card_id = 0
        for color in [1, 2, 3]:
            for shape in [1, 2, 3]:
                for fill in [1, 2, 3]:
                    for count in [1, 2, 3]:
                        self.deck.append(Card(
                            id=card_id,
                            color=color,
                            shape=shape,
                            fill=fill,
                            count=count
                        ))
                        card_id += 1
        random.shuffle(self.deck)

    def _deal_initial_cards(self):
        """Deal 12 cards to the field initially."""
        for _ in range(12):
            if self.deck:
                self.field.append(self.deck.pop())

    def add_player(self, access_token: str):
        """Add a player to the game."""
        if access_token not in self.players:
            self.players[access_token] = 0

    def get_card_by_id(self, card_id: int) -> Optional[Card]:
        """Find a card on the field by ID."""
        for card in self.field:
            if card.id == card_id:
                return card
        return None

    def is_valid_set(self, c1: Card, c2: Card, c3: Card) -> bool:
        """Check if three cards form a valid set."""
        def check_property(v1, v2, v3):
            return (v1 == v2 == v3) or (v1 != v2 and v1 != v3 and v2 != v3)

        return (check_property(c1.color, c2.color, c3.color) and
                check_property(c1.shape, c2.shape, c3.shape) and
                check_property(c1.fill, c2.fill, c3.fill) and
                check_property(c1.count, c2.count, c3.count))

    def pick_set(self, access_token: str, card_ids: List[int]) -> tuple[bool, int]:
        """
        Attempt to pick a set.
        Returns: (is_valid_set, new_score)
        """
        if len(card_ids) != 3:
            return False, self.players[access_token]

        cards = [self.get_card_by_id(cid) for cid in card_ids]
        if None in cards:
            return False, self.players[access_token]

        is_set = self.is_valid_set(cards[0], cards[1], cards[2])

        if is_set:
            # Remove cards from field
            for card in cards:
                self.field.remove(card)

            # Add points
            self.players[access_token] += 1

            # Replace cards if deck has cards and field < 12
            while len(self.field) < 12 and self.deck:
                self.field.append(self.deck.pop())

            # Check if game ended
            if not self.deck and len(self.field) < 3:
                self.status = "ended"
        else:
            # Penalty for wrong set
            self.players[access_token] -= 1

        return is_set, self.players[access_token]

    def add_cards(self):
        """Add 3 more cards to the field."""
        for _ in range(3):
            if self.deck:
                self.field.append(self.deck.pop())


# ==================== Server State ====================

class ServerState:
    def __init__(self):
        self.users: Dict[str, Dict] = {}  # accessToken -> {nickname, password, current_game_id}
        self.games: Dict[int, GameRoom] = {}  # gameId -> GameRoom
        self.next_game_id = 0

    def register_user(self, nickname: str, password: str) -> str:
        """Register a new user and return access token."""
        access_token = self._generate_token()
        self.users[access_token] = {
            "nickname": nickname,
            "password": password,
            "current_game_id": None
        }
        return access_token

    def verify_token(self, access_token: str) -> bool:
        """Check if access token is valid."""
        return access_token in self.users

    def create_game(self) -> int:
        """Create a new game room and return game ID."""
        game_id = self.next_game_id
        self.next_game_id += 1
        self.games[game_id] = GameRoom(game_id)
        return game_id

    def enter_game(self, access_token: str, game_id: int) -> bool:
        """Enter a game room."""
        if game_id not in self.games:
            return False
        self.users[access_token]["current_game_id"] = game_id
        self.games[game_id].add_player(access_token)
        return True

    def get_user_game(self, access_token: str) -> Optional[GameRoom]:
        """Get the game room the user is currently in."""
        game_id = self.users[access_token].get("current_game_id")
        if game_id is None:
            return None
        return self.games.get(game_id)

    @staticmethod
    def _generate_token() -> str:
        """Generate a 16-character access token."""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return ''.join(random.choice(chars) for _ in range(16))


state = ServerState()


# ==================== API Endpoints ====================

@app.post("/user/register")
def register(req: RegisterRequest):
    """Register a new user with nickname and password."""
    try:
        access_token = state.register_user(req.nickname, req.password)
        return {
            "success": True,
            "exception": None,
            "nickname": req.nickname,
            "accessToken": access_token
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.post("/set/room/create")
def create_room(req: CreateRoomRequest):
    """Create a new game room."""
    try:
        if not state.verify_token(req.accessToken):
            return {
                "success": False,
                "exception": {
                    "message": "Invalid access token"
                }
            }

        game_id = state.create_game()
        return {
            "success": True,
            "exception": None,
            "gameId": game_id
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.post("/set/room/list")
def list_rooms(req: ListRoomRequest):
    """Get list of all game rooms."""
    try:
        if not state.verify_token(req.accessToken):
            return {
                "success": False,
                "exception": {
                    "message": "Invalid access token"
                }
            }

        games = [{"id": game_id} for game_id in state.games.keys()]
        return {
            "success": True,
            "exception": None,
            "games": games
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.post("/set/room/enter")
def enter_room(req: EnterRoomRequest):
    """Enter a game room."""
    try:
        if not state.verify_token(req.accessToken):
            return {
                "success": False,
                "exception": {
                    "message": "Invalid access token"
                }
            }

        success = state.enter_game(req.accessToken, req.gameId)
        if not success:
            return {
                "success": False,
                "exception": {
                    "message": "Game not found"
                }
            }

        return {
            "success": True,
            "exception": None,
            "gameId": req.gameId
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.post("/set/field")
def get_field(req: FieldRequest):
    """Get the current field (cards on the table) for the user's game."""
    try:
        if not state.verify_token(req.accessToken):
            return {
                "success": False,
                "exception": {
                    "message": "Invalid access token"
                }
            }

        game = state.get_user_game(req.accessToken)
        if not game:
            return {
                "success": False,
                "exception": {
                    "message": "User is not in a game"
                }
            }

        score = game.players.get(req.accessToken, 0)
        return {
            "success": True,
            "exception": None,
            "cards": game.field,
            "status": game.status,
            "score": score
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.post("/set/pick")
def pick_set(req: PickRequest):
    """Attempt to pick a set from the field."""
    try:
        if not state.verify_token(req.accessToken):
            return {
                "success": False,
                "exception": {
                    "message": "Invalid access token"
                }
            }

        game = state.get_user_game(req.accessToken)
        if not game:
            return {
                "success": False,
                "exception": {
                    "message": "User is not in a game"
                }
            }

        is_set, new_score = game.pick_set(req.accessToken, req.cards)
        return {
            "success": True,
            "exception": None,
            "isSet": is_set,
            "score": new_score
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.post("/set/add")
def add_cards(req: AddCardsRequest):
    """Add 3 more cards to the field."""
    try:
        if not state.verify_token(req.accessToken):
            return {
                "success": False,
                "exception": {
                    "message": "Invalid access token"
                }
            }

        game = state.get_user_game(req.accessToken)
        if not game:
            return {
                "success": False,
                "exception": {
                    "message": "User is not in a game"
                }
            }

        game.add_cards()
        return {
            "success": True,
            "exception": None
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.post("/set/scores")
def get_scores(req: ScoresRequest):
    """Get scores of all players in the current game."""
    try:
        if not state.verify_token(req.accessToken):
            return {
                "success": False,
                "exception": {
                    "message": "Invalid access token"
                }
            }

        game = state.get_user_game(req.accessToken)
        if not game:
            return {
                "success": False,
                "exception": {
                    "message": "User is not in a game"
                }
            }

        users = []
        for token, score in game.players.items():
            nickname = state.users[token]["nickname"]
            users.append({
                "name": nickname,
                "score": score
            })

        # Sort by score descending
        users.sort(key=lambda x: x["score"], reverse=True)

        return {
            "success": True,
            "exception": None,
            "users": users
        }
    except Exception as e:
        return {
            "success": False,
            "exception": {
                "message": str(e)
            }
        }


@app.get("/")
def root():
    """Root endpoint with basic info."""
    return {
        "message": "Set Game Server",
        "docs": "/docs",
        "endpoints": [
            "POST /user/register",
            "POST /set/room/create",
            "POST /set/room/list",
            "POST /set/room/enter",
            "POST /set/field",
            "POST /set/pick",
            "POST /set/add",
            "POST /set/scores"
        ]
    }
