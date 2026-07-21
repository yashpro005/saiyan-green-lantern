"""
Terabox Cloud Storage Integration for Imaland Game
Syncs game save data to Terabox cloud storage
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class TeraboxSync:
    def __init__(self, game_save_dir: str = "."):
        """
        Initialize Terabox sync manager
        
        Args:
            game_save_dir: Directory containing game save files
        """
        self.game_save_dir = game_save_dir
        self.save_file = "save_data.json"
        self.metadata_file = ".terabox_metadata.json"
        self.remote_path = "/imaland_saves"
        self.local_metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load local file metadata for change tracking"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save file metadata for change tracking"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.local_metadata, f, indent=2)
    
    def _get_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
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
                return True
            else:
                print(f"❌ Authentication failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            return False
    
    def upload_save(self, filename: str = None) -> bool:
        """
        Upload game save to Terabox
        
        Args:
            filename: Specific file to upload (default: save_data.json)
            
        Returns:
            bool: True if upload successful
        """
        if filename is None:
            filename = self.save_file
        
        filepath = os.path.join(self.game_save_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False
        
        # Check if file has changed
        if not self._has_file_changed(filename):
            print(f"⏭️  File unchanged, skipping upload: {filename}")
            return True
        
        print(f"📤 Uploading {filename} to Terabox...")
        try:
            result = subprocess.run(['terabox', 'upload', 
                                   filepath,
                                   self.remote_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=60)
            
            if result.returncode == 0:
                # Update metadata
                file_hash = self._get_file_hash(filepath)
                self.local_metadata[filename] = {
                    "hash": file_hash,
                    "last_synced": datetime.now().isoformat(),
                    "size": os.path.getsize(filepath)
                }
                self._save_metadata()
                print(f"✅ Successfully uploaded {filename}")
                return True
            else:
                print(f"❌ Upload failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error during upload: {e}")
            return False
    
    def download_save(self, filename: str = None, overwrite: bool = False) -> bool:
        """
        Download game save from Terabox
        
        Args:
            filename: File to download (default: save_data.json)
            overwrite: Whether to overwrite local file if it exists
            
        Returns:
            bool: True if download successful
        """
        if filename is None:
            filename = self.save_file
        
        local_path = os.path.join(self.game_save_dir, filename)
        remote_file = f"{self.remote_path}/{filename}"
        
        # Check if local file exists and overwrite is False
        if os.path.exists(local_path) and not overwrite:
            print(f"⏭️  Local file already exists, skipping: {filename}")
            return True
        
        print(f"📥 Downloading {filename} from Terabox...")
        try:
            result = subprocess.run(['terabox', 'download',
                                   remote_file,
                                   local_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=60)
            
            if result.returncode == 0:
                # Update metadata
                file_hash = self._get_file_hash(local_path)
                self.local_metadata[filename] = {
                    "hash": file_hash,
                    "last_synced": datetime.now().isoformat(),
                    "size": os.path.getsize(local_path)
                }
                self._save_metadata()
                print(f"✅ Successfully downloaded {filename}")
                return True
            else:
                print(f"❌ Download failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error during download: {e}")
            return False
    
    def sync_bidirectional(self) -> bool:
        """
        Sync local and remote saves bidirectionally
        Uploads local changes and downloads remote updates
        
        Returns:
            bool: True if sync successful
        """
        print("🔄 Starting bidirectional sync with Terabox...")
        
        # Upload local changes
        success = True
        for filename in [self.save_file]:
            if os.path.exists(os.path.join(self.game_save_dir, filename)):
                if not self.upload_save(filename):
                    success = False
        
        print("✅ Sync completed!")
        return success
    
    def list_remote_saves(self) -> Optional[list]:
        """List all saves in Terabox"""
        print(f"📋 Listing remote saves in {self.remote_path}...")
        try:
            result = subprocess.run(['terabox', 'ls', self.remote_path],
                                  capture_output=True,
                                  text=True,
                                  timeout=30)
            
            if result.returncode == 0:
                print(result.stdout)
                return result.stdout
            else:
                print(f"❌ Failed to list files: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return None
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        status = {
            "last_synced": None,
            "files": {}
        }
        
        for filename in [self.save_file]:
            filepath = os.path.join(self.game_save_dir, filename)
            if os.path.exists(filepath):
                metadata = self.local_metadata.get(filename, {})
                status["files"][filename] = {
                    "synced": bool(metadata),
                    "last_synced": metadata.get("last_synced"),
                    "size": os.path.getsize(filepath),
                    "remote_path": f"{self.remote_path}/{filename}"
                }
        
        return status


def setup_terabox_sync(email: str, password: str) -> Optional[TeraboxSync]:
    """
    Setup and authenticate Terabox sync
    
    Args:
        email: Terabox email
        password: Terabox password
        
    Returns:
        TeraboxSync instance if successful, None otherwise
    """
    sync = TeraboxSync()
    
    if sync.authenticate(email, password):
        print("\n📊 Sync Status:")
        status = sync.get_sync_status()
        for filename, info in status["files"].items():
            print(f"  • {filename}: {'✅ Synced' if info['synced'] else '❌ Not synced'}")
        
        return sync
    else:
        print("❌ Failed to setup Terabox sync")
        return None


if __name__ == "__main__":
    # Example usage
    import sys
    
    print("🎮 Imaland Game - Terabox Cloud Sync Setup\n")
    
    # Get credentials
    email = input("Enter your Terabox email: ")
    password = input("Enter your Terabox password: ")
    
    # Setup sync
    sync = setup_terabox_sync(email, password)
    
    if sync:
        print("\n🔄 Syncing game save data...")
        sync.sync_bidirectional()
        
        print("\n📋 Remote Files:")
        sync.list_remote_saves()
