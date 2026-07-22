"""Asset Manager for Imaland Game

Manages loading, caching, and accessing all game assets including:
- Block definitions
- Particle effects
- Sound effects
- NPC configurations
- Animations
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class AssetManager:
    """Centralized asset management system."""

    def __init__(self, assets_dir: str = "assets"):
        """Initialize the asset manager.
        
        Args:
            assets_dir: Root directory for all asset files
        """
        self.assets_dir = Path(assets_dir)
        self.cache: Dict[str, Any] = {}
        self._load_all_assets()

    def _load_all_assets(self) -> None:
        """Load all asset configuration files."""
        asset_files = {
            "blocks": "blocks_config.json",
            "particles": "particles_config.json",
            "sounds": "sounds_config.json",
            "npcs": "npc_config.json",
            "animations": "animations_config.json",
        }

        for asset_type, filename in asset_files.items():
            try:
                self.load_asset_file(asset_type, filename)
                print(f"✓ Loaded {asset_type} assets")
            except Exception as e:
                print(f"✗ Failed to load {asset_type}: {e}")

    def load_asset_file(self, asset_type: str, filename: str) -> None:
        """Load a JSON asset file.
        
        Args:
            asset_type: Type identifier for the asset
            filename: Name of the JSON file to load
        """
        filepath = self.assets_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Asset file not found: {filepath}")

        with open(filepath, "r") as f:
            self.cache[asset_type] = json.load(f)

    def get_block_config(self, block_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific block type.
        
        Args:
            block_type: Type of block (e.g., 'grass', 'sand')
            
        Returns:
            Block configuration dictionary or None if not found
        """
        if "blocks" not in self.cache:
            return None
        return self.cache["blocks"].get("blocks", {}).get(block_type)

    def get_all_blocks(self) -> Dict[str, Any]:
        """Get all block configurations."""
        if "blocks" not in self.cache:
            return {}
        return self.cache["blocks"].get("blocks", {})

    def get_particle_effect(self, effect_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific particle effect.
        
        Args:
            effect_name: Name of the particle effect (e.g., 'rain', 'portal_glow')
            
        Returns:
            Particle effect configuration or None if not found
        """
        if "particles" not in self.cache:
            return None
        return self.cache["particles"].get("particle_effects", {}).get(effect_name)

    def get_sound_effect(self, category: str, effect: str) -> Optional[str]:
        """Get path to a sound effect.
        
        Args:
            category: Sound category (e.g., 'grass', 'portal')
            effect: Effect type (e.g., 'break', 'place')
            
        Returns:
            Path to sound file or None if not found
        """
        if "sounds" not in self.cache:
            return None
        category_sounds = self.cache["sounds"].get("sound_effects", {}).get(category, {})
        return category_sounds.get(effect)

    def get_npc_config(self, npc_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific NPC type.
        
        Args:
            npc_type: Type of NPC (e.g., 'villager', 'animal')
            
        Returns:
            NPC configuration or None if not found
        """
        if "npcs" not in self.cache:
            return None
        return self.cache["npcs"].get("npcs", {}).get(npc_type)

    def get_animation(self, entity_type: str, animation_name: str) -> Optional[Dict[str, Any]]:
        """Get animation configuration.
        
        Args:
            entity_type: Type of entity ('player', 'entities', 'blocks')
            animation_name: Name of the animation
            
        Returns:
            Animation configuration or None if not found
        """
        if "animations" not in self.cache:
            return None
        animations = self.cache["animations"].get("animations", {})
        entity_anims = animations.get(entity_type, {})
        
        # Handle nested animation types (e.g., player.walk)
        parts = animation_name.split(".")
        current = entity_anims
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current if isinstance(current, dict) else None

    def get_block_color(self, block_type: str) -> tuple:
        """Get RGB color for a block type.
        
        Args:
            block_type: Type of block
            
        Returns:
            RGB tuple (r, g, b) or default gray if not found
        """
        config = self.get_block_config(block_type)
        if config and "color" in config:
            color = config["color"]
            return tuple(color)
        return (128, 128, 128)  # Default gray

    def get_block_description(self, block_type: str) -> str:
        """Get description for a block type.
        
        Args:
            block_type: Type of block
            
        Returns:
            Description string or empty string if not found
        """
        config = self.get_block_config(block_type)
        if config:
            return config.get("description", "")
        return ""

    def list_all_blocks(self) -> list:
        """Get list of all available block types."""
        return list(self.get_all_blocks().keys())

    def list_particle_effects(self) -> list:
        """Get list of all available particle effects."""
        if "particles" not in self.cache:
            return []
        return list(self.cache["particles"].get("particle_effects", {}).keys())

    def list_npc_types(self) -> list:
        """Get list of all available NPC types."""
        if "npcs" not in self.cache:
            return []
        return list(self.cache["npcs"].get("npcs", {}).keys())

    def print_asset_summary(self) -> None:
        """Print a summary of all loaded assets."""
        print("\n=== ASSET MANAGER SUMMARY ===")
        print(f"Blocks: {len(self.list_all_blocks())} types")
        print(f"  {', '.join(self.list_all_blocks())}")
        print(f"\nParticle Effects: {len(self.list_particle_effects())} types")
        print(f"  {', '.join(self.list_particle_effects())}")
        print(f"\nNPC Types: {len(self.list_npc_types())} types")
        print(f"  {', '.join(self.list_npc_types())}")
        print("="*30 + "\n")


if __name__ == "__main__":
    # Test the asset manager
    manager = AssetManager()
    manager.print_asset_summary()
    
    # Test specific queries
    print("\nTest: Grass block config")
    grass_config = manager.get_block_config("grass")
    print(json.dumps(grass_config, indent=2))
    
    print("\nTest: Rain particle effect")
    rain_effect = manager.get_particle_effect("rain")
    print(json.dumps(rain_effect, indent=2))
    
    print("\nTest: Block color for ore")
    ore_color = manager.get_block_color("ore")
    print(f"Ore color: {ore_color}")
