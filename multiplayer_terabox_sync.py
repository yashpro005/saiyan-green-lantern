"""
Multiplayer Terabox Cloud Sync
Synchronizes multiplayer game state to Terabox cloud storage
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from multiplayer_session import WorldState, BlockChange, PlayerSession


class MultiplayerTeraboxSync:
    """Manages cloud synchronization of multiplayer world state to Terabox"""
    
    def __init__(self, game_save_dir: str = "."):
        """
        Initialize multiplayer Terabox sync
        
        Args:
            game_save_dir: Directory containing game files
        """
        self.game_save_dir = game_save_dir
        self.world_state_file = "world_state.json"
        self.changes_log_file = "world_changes.json"
        self.metadata_file = ".terabox_mp_metadata.json"
        
        # Terabox paths for multiplayer
        self.remote_base = "/imaland_multiplayer"
        self.remote_world_path = f"{self.remote_base}/worlds"
        self.remote_changes_path = f"{self.remote_base}/changes"
        
        self.local_metadata = self._load_metadata()
        self.authenticated = False
    
    def _load_metadata(self) -> Dict:
        """Load local file metadata for change tracking"""
        metadata_path = os.path.join(self.game_save_dir, self.metadata_file)
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save file metadata"""
        metadata_path = os.path.join(self.game_save_dir, self.metadata_file)
        with open(metadata_path, 'w') as f:
            json.dump(self.local_metadata, f, indent=2)
    
    def _get_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        if not os.path.exists(filepath):
            return ""
        
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _has_file_changed(self, filename: str) -> bool:
        """Check if a file has changed since last sync"""
        filepath = os.path.join(self.game_save_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        current_hash = self._get_file_hash(filepath)
        previous_hash = self.local_metadata.get(filename, {}).get("hash")
        
        return current_hash != previous_hash
    
    def check_terabox_cli(self) -> bool:
        """Check if terabox-cli is installed"""
        try:
            result = subprocess.run(['terabox', '--version'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def install_terabox_cli(self) -> bool:
        """Install terabox-cli if not present"""
        print("📦 Installing terabox-cli...")
        try:
            subprocess.run(['pip', 'install', 'terabox-cli', '-q'], 
                         check=True,
                         timeout=60)
            print("✅ terabox-cli installed successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to install terabox-cli: {e}")
            return False
    
    def authenticate(self, email: str, password: str) -> bool:
        """
        Authenticate with Terabox
        
        Args:
            email: Terabox email
            password: Terabox password
            
        Returns:
            bool: True if authentication successful
        """
        if not self.check_terabox_cli():
            print("⚠️  terabox-cli not found. Installing...")
            if not self.install_terabox_cli():
                return False
        
        print("🔐 Authenticating with Terabox...")
        try:
            result = subprocess.run(['terabox', 'login', 
                                   '--username', email,
                                   '--password', password],
                                  capture_output=True,
                                  text=True,
                                  timeout=30)
            
            if result.returncode == 0:
                print("✅ Successfully authenticated with Terabox!")
                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            return False
    
    def upload_world_state(self) -> bool:
        """Upload current world state to Terabox"""
        filepath = os.path.join(self.game_save_dir, self.world_state_file)
        
        if not os.path.exists(filepath):
            print(f"❌ World state file not found: {filepath}")
            return False
        
        if not self._has_file_changed(self.world_state_file):
            print(f"⏭️  World state unchanged, skipping upload")
            return True
        
        print(f"📤 Uploading world state to Terabox...")
        try:
            # Create world directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            remote_file = f"{self.remote_world_path}/world_state_{timestamp}.json"
            
            result = subprocess.run(['terabox', 'upload', 
                                   filepath,
                                   self.remote_world_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=60)
            
            if result.returncode == 0:
                file_hash = self._get_file_hash(filepath)
                self.local_metadata[self.world_state_file] = {
                    "hash": file_hash,
                    "last_synced": datetime.now().isoformat(),
                    "size": os.path.getsize(filepath),
                    "remote_path": remote_file
                }
                self._save_metadata()
                print(f"✅ World state uploaded successfully")
                return True
            else:
                print(f"❌ Upload failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error uploading world state: {e}")
            return False
    
    def upload_changes_log(self) -> bool:
        """Upload recent block changes to Terabox"""
        filepath = os.path.join(self.game_save_dir, self.changes_log_file)
        
        if not os.path.exists(filepath):
            print(f"⏭️  Changes log empty, skipping upload")
            return True
        
        print(f"📤 Uploading changes log to Terabox...")
        try:
            result = subprocess.run(['terabox', 'upload', 
                                   filepath,
                                   self.remote_changes_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=60)
            
            if result.returncode == 0:
                file_hash = self._get_file_hash(filepath)
                self.local_metadata[self.changes_log_file] = {
                    "hash": file_hash,
                    "last_synced": datetime.now().isoformat(),
                    "size": os.path.getsize(filepath)
                }
                self._save_metadata()
                print(f"✅ Changes log uploaded successfully")
                return True
            else:
                print(f"❌ Upload failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error uploading changes: {e}")
            return False
    
    def download_world_state(self, overwrite: bool = False) -> bool:
        """
        Download latest world state from Terabox
        
        Args:
            overwrite: Whether to overwrite local file
            
        Returns:
            bool: True if successful
        """
        local_path = os.path.join(self.game_save_dir, self.world_state_file)
        
        if os.path.exists(local_path) and not overwrite:
            print(f"⏭️  Local world state exists, skipping download")
            return True
        
        print(f"📥 Downloading world state from Terabox...")
        try:
            # Download the most recent world state
            remote_file = f"{self.remote_world_path}/world_state.json"
            
            result = subprocess.run(['terabox', 'download',
                                   remote_file,
                                   local_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=60)
            
            if result.returncode == 0:
                file_hash = self._get_file_hash(local_path)
                self.local_metadata[self.world_state_file] = {
                    "hash": file_hash,
                    "last_synced": datetime.now().isoformat(),
                    "size": os.path.getsize(local_path)
                }
                self._save_metadata()
                print(f"✅ World state downloaded successfully")
                return True
            else:
                print(f"❌ Download failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error downloading world state: {e}")
            return False
    
    def download_changes_log(self) -> bool:
        """Download recent changes from Terabox"""
        local_path = os.path.join(self.game_save_dir, self.changes_log_file)
        remote_file = f"{self.remote_changes_path}/world_changes.json"
        
        print(f"📥 Downloading changes log from Terabox...")
        try:
            result = subprocess.run(['terabox', 'download',
                                   remote_file,
                                   local_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=60)
            
            if result.returncode == 0:
                print(f"✅ Changes downloaded successfully")
                return True
            else:
                # Changes might not exist yet
                print(f"⏭️  No remote changes found")
                return True
        except Exception as e:
            print(f"⚠️  Error downloading changes: {e}")
            return True  # Don't fail if changes don't exist
    
    def sync_world_state(self, world_state: WorldState) -> bool:
        """
        Sync world state with cloud
        
        Args:
            world_state: Current world state to sync
            
        Returns:
            bool: True if successful
        """
        if not self.authenticated:
            print("❌ Not authenticated with Terabox")
            return False
        
        # Save world state locally
        filepath = os.path.join(self.game_save_dir, self.world_state_file)
        try:
            with open(filepath, 'w') as f:
                json.dump(world_state.to_dict(), f, indent=2)
        except Exception as e:
            print(f"❌ Error saving world state: {e}")
            return False
        
        # Upload to Terabox
        return self.upload_world_state()
    
    def sync_block_changes(self, changes: List[BlockChange]) -> bool:
        """
        Sync block changes with cloud
        
        Args:
            changes: List of block changes to sync
            
        Returns:
            bool: True if successful
        """
        if not self.authenticated:
            print("❌ Not authenticated with Terabox")
            return False
        
        # Save changes locally
        filepath = os.path.join(self.game_save_dir, self.changes_log_file)
        try:
            with open(filepath, 'w') as f:
                json.dump([change.to_dict() for change in changes], f, indent=2)
        except Exception as e:
            print(f"❌ Error saving changes: {e}")
            return False
        
        # Upload to Terabox
        return self.upload_changes_log()
    
    def full_sync(self, world_state: WorldState) -> bool:
        """
        Perform full bidirectional sync
        
        Args:
            world_state: Current world state
            
        Returns:
            bool: True if successful
        """
        print("\n🔄 Starting full multiplayer sync with Terabox...")
        
        success = True
        
        # Upload local state
        if not self.sync_world_state(world_state):
            success = False
        
        # Upload block changes
        recent_changes = world_state.get_recent_changes(limit=1000)
        if recent_changes and not self.sync_block_changes(recent_changes):
            success = False
        
        print("✅ Full sync completed!\n")
        return success
    
    def list_remote_worlds(self) -> Optional[List[str]]:
        """List all world saves on Terabox"""
        print(f"📋 Listing remote worlds...")
        try:
            result = subprocess.run(['terabox', 'ls', self.remote_world_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=30)
            
            if result.returncode == 0:
                worlds = result.stdout.strip().split('\n')
                for world in worlds:
                    print(f"  • {world}")
                return worlds
            else:
                print(f"⚠️  No worlds found yet")
                return None
        except Exception as e:
            print(f"❌ Error listing worlds: {e}")
            return None
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        status = {
            "authenticated": self.authenticated,
            "last_synced": None,
            "files": {}
        }
        
        for filename in [self.world_state_file, self.changes_log_file]:
            filepath = os.path.join(self.game_save_dir, filename)
            if os.path.exists(filepath):
                metadata = self.local_metadata.get(filename, {})
                status["files"][filename] = {
                    "synced": bool(metadata),
                    "last_synced": metadata.get("last_synced"),
                    "size": os.path.getsize(filepath),
                    "remote_path": metadata.get("remote_path", "N/A")
                }
        
        return status


def setup_multiplayer_terabox_sync(email: str, password: str) -> Optional[MultiplayerTeraboxSync]:
    """
    Setup and authenticate multiplayer Terabox sync
    
    Args:
        email: Terabox email
        password: Terabox password
        
    Returns:
        MultiplayerTeraboxSync instance if successful, None otherwise
    """
    sync = MultiplayerTeraboxSync()
    
    if sync.authenticate(email, password):
        print("\n📊 Sync Status:")
        status = sync.get_sync_status()
        print(f"  Authenticated: {status['authenticated']}")
        for filename, info in status["files"].items():
            print(f"  • {filename}: {'✅ Synced' if info['synced'] else '❌ Not synced'}")
        
        return sync
    else:
        print("❌ Failed to setup multiplayer Terabox sync")
        return False


if __name__ == "__main__":
    # Example usage
    print("🎮 Imaland Multiplayer - Terabox Cloud Sync Setup\n")
    
    # Get credentials
    email = input("Enter your Terabox email: ")
    password = input("Enter your Terabox password: ")
    
    # Setup sync
    sync = setup_multiplayer_terabox_sync(email, password)
    
    if sync:
        print("\n📋 Remote Worlds:")
        sync.list_remote_worlds()
