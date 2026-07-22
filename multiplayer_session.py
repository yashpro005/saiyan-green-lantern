"""
Multiplayer Session Management
Handles player sessions, synchronization, and state management for Imaland
"""

import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class PlayerSession:
    """Represents a single player's session in the multiplayer game"""
    
    def __init__(self, player_name: str, player_id: str = None):
        self.player_id = player_id or str(uuid.uuid4())
        self.player_name = player_name
        self.position = (0, 0, 0)  # x, y, z
        self.stamina = 100
        self.score = 0
        self.playtime = 0
        self.last_update = datetime.now().isoformat()
        self.is_active = True
        self.blocks_placed = 0
        self.blocks_destroyed = 0
    
    def to_dict(self) -> Dict:
        """Convert session to JSON-serializable dict"""
        return {
            'player_id': self.player_id,
            'player_name': self.player_name,
            'position': self.position,
            'stamina': self.stamina,
            'score': self.score,
            'playtime': self.playtime,
            'last_update': self.last_update,
            'is_active': self.is_active,
            'blocks_placed': self.blocks_placed,
            'blocks_destroyed': self.blocks_destroyed
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'PlayerSession':
        """Create session from dict"""
        session = PlayerSession(data['player_name'], data['player_id'])
        session.position = tuple(data.get('position', (0, 0, 0)))
        session.stamina = data.get('stamina', 100)
        session.score = data.get('score', 0)
        session.playtime = data.get('playtime', 0)
        session.last_update = data.get('last_update', datetime.now().isoformat())
        session.is_active = data.get('is_active', True)
        session.blocks_placed = data.get('blocks_placed', 0)
        session.blocks_destroyed = data.get('blocks_destroyed', 0)
        return session


class BlockChange:
    """Represents a block modification in the world"""
    
    def __init__(self, position: Tuple, action: str, block_type: str, 
                 player_id: str, timestamp: str = None):
        """
        action: 'place' or 'destroy'
        block_type: type of block (grass, sand, stone, etc.)
        """
        self.position = position
        self.action = action
        self.block_type = block_type
        self.player_id = player_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.change_id = hashlib.md5(
            f"{position}{action}{timestamp}".encode()
        ).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'position': self.position,
            'action': self.action,
            'block_type': self.block_type,
            'player_id': self.player_id,
            'timestamp': self.timestamp,
            'change_id': self.change_id
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'BlockChange':
        return BlockChange(
            tuple(data['position']),
            data['action'],
            data['block_type'],
            data['player_id'],
            data.get('timestamp', datetime.now().isoformat())
        )


class WorldState:
    """Tracks the complete multiplayer world state"""
    
    def __init__(self):
        self.active_players: Dict[str, PlayerSession] = {}
        self.block_changes: List[BlockChange] = []  # Change log (immutable)
        self.last_sync = datetime.now().isoformat()
        self.version = 1
    
    def add_player(self, session: PlayerSession) -> bool:
        """Add a new player to the session"""
        if session.player_id in self.active_players:
            return False
        self.active_players[session.player_id] = session
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from active sessions"""
        if player_id in self.active_players:
            self.active_players[player_id].is_active = False
            del self.active_players[player_id]
            return True
        return False
    
    def update_player_position(self, player_id: str, position: Tuple) -> bool:
        """Update a player's position"""
        if player_id in self.active_players:
            self.active_players[player_id].position = position
            self.active_players[player_id].last_update = datetime.now().isoformat()
            return True
        return False
    
    def update_player_stats(self, player_id: str, stamina: float, score: int) -> bool:
        """Update player stats"""
        if player_id in self.active_players:
            self.active_players[player_id].stamina = stamina
            self.active_players[player_id].score = score
            self.active_players[player_id].last_update = datetime.now().isoformat()
            return True
        return False
    
    def record_block_change(self, change: BlockChange) -> bool:
        """Record a block change to the change log"""
        self.block_changes.append(change)
        return True
    
    def get_player_session(self, player_id: str) -> Optional[PlayerSession]:
        """Get a specific player's session"""
        return self.active_players.get(player_id)
    
    def get_all_players(self) -> Dict[str, PlayerSession]:
        """Get all active players"""
        return self.active_players.copy()
    
    def get_recent_changes(self, limit: int = 100) -> List[BlockChange]:
        """Get the most recent block changes"""
        return self.block_changes[-limit:]
    
    def to_dict(self) -> Dict:
        return {
            'active_players': {pid: session.to_dict() 
                             for pid, session in self.active_players.items()},
            'block_changes': [change.to_dict() for change in self.block_changes],
            'last_sync': self.last_sync,
            'version': self.version
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'WorldState':
        world = WorldState()
        world.active_players = {
            pid: PlayerSession.from_dict(sess_data)
            for pid, sess_data in data.get('active_players', {}).items()
        }
        world.block_changes = [
            BlockChange.from_dict(change_data)
            for change_data in data.get('block_changes', [])
        ]
        world.last_sync = data.get('last_sync', datetime.now().isoformat())
        world.version = data.get('version', 1)
        return world


class MultiplayerSessionManager:
    """Manages multiplayer sessions and state synchronization"""
    
    def __init__(self, local_dir: str = "."):
        self.local_dir = local_dir
        self.world_state_file = os.path.join(local_dir, "world_state.json")
        self.current_player_id = None
        self.world_state = self._load_world_state()
    
    def _load_world_state(self) -> WorldState:
        """Load world state from local cache"""
        if os.path.exists(self.world_state_file):
            try:
                with open(self.world_state_file, 'r') as f:
                    data = json.load(f)
                return WorldState.from_dict(data)
            except Exception as e:
                print(f"⚠️  Error loading world state: {e}")
                return WorldState()
        return WorldState()
    
    def _save_world_state(self):
        """Save world state to local cache"""
        try:
            with open(self.world_state_file, 'w') as f:
                json.dump(self.world_state.to_dict(), f, indent=2)
        except Exception as e:
            print(f"❌ Error saving world state: {e}")
    
    def create_player_session(self, player_name: str) -> PlayerSession:
        """Create a new player session"""
        session = PlayerSession(player_name)
        self.world_state.add_player(session)
        self.current_player_id = session.player_id
        self._save_world_state()
        print(f"✅ Player '{player_name}' joined with ID: {session.player_id}")
        return session
    
    def join_existing_session(self, player_id: str) -> Optional[PlayerSession]:
        """Rejoin an existing player session"""
        session = self.world_state.get_player_session(player_id)
        if session:
            session.is_active = True
            self.current_player_id = player_id
            self._save_world_state()
            print(f"✅ Rejoined as '{session.player_name}'")
            return session
        return None
    
    def disconnect_player(self, player_id: str):
        """Disconnect a player"""
        self.world_state.remove_player(player_id)
        self._save_world_state()
        print(f"👋 Player {player_id} disconnected")
    
    def update_current_player_position(self, position: Tuple):
        """Update current player's position"""
        if self.current_player_id:
            self.world_state.update_player_position(self.current_player_id, position)
    
    def update_current_player_stats(self, stamina: float, score: int):
        """Update current player's stats"""
        if self.current_player_id:
            self.world_state.update_player_stats(self.current_player_id, stamina, score)
    
    def record_block_change(self, position: Tuple, action: str, 
                           block_type: str, player_id: str = None):
        """Record a block change"""
        if player_id is None:
            player_id = self.current_player_id
        
        change = BlockChange(position, action, block_type, player_id)
        self.world_state.record_block_change(change)
    
    def get_all_players(self) -> Dict[str, PlayerSession]:
        """Get all active players"""
        return self.world_state.get_all_players()
    
    def get_recent_changes(self, limit: int = 100) -> List[BlockChange]:
        """Get recent block changes"""
        return self.world_state.get_recent_changes(limit)
    
    def sync_state(self) -> Dict:
        """Get current state for sync"""
        return self.world_state.to_dict()


if __name__ == "__main__":
    # Test multiplayer session management
    manager = MultiplayerSessionManager()
    
    # Create players
    player1 = manager.create_player_session("Goku")
    player2 = manager.create_player_session("Vegeta")
    
    print(f"\n👥 Active players: {list(manager.get_all_players().keys())}")
    
    # Simulate gameplay
    manager.current_player_id = player1.player_id
    manager.update_current_player_position((10, 5, 20))
    manager.record_block_change((10, 5, 20), 'place', 'brick')
    
    manager.current_player_id = player2.player_id
    manager.update_current_player_position((15, 3, 25))
    manager.record_block_change((15, 3, 25), 'destroy', 'grass')
    
    # Show state
    print(f"\n📊 Recent changes: {len(manager.get_recent_changes())}")
    for change in manager.get_recent_changes():
        print(f"  • {change.player_id}: {change.action} {change.block_type} at {change.position}")
