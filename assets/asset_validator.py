"""Asset Validator for Imaland Game

Validates all asset configurations for consistency, completeness, and correctness.
Ensures no broken references and provides detailed reports.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import sys


class AssetValidator:
    """Validates asset configurations and identifies issues."""

    def __init__(self, assets_dir: str = "assets"):
        """Initialize the asset validator.
        
        Args:
            assets_dir: Root directory for asset files
        """
        self.assets_dir = Path(assets_dir)
        self.assets: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self._load_all_assets()

    def _load_all_assets(self) -> None:
        """Load all asset files."""
        asset_files = {
            "blocks": "blocks_config.json",
            "particles": "particles_config.json",
            "sounds": "sounds_config.json",
            "npcs": "npc_config.json",
            "animations": "animations_config.json",
            "items": "items_config.json",
            "crafting": "crafting_config.json",
        }

        for asset_type, filename in asset_files.items():
            try:
                filepath = self.assets_dir / filename
                if filepath.exists():
                    with open(filepath, "r") as f:
                        self.assets[asset_type] = json.load(f)
                else:
                    self.warnings.append(f"Asset file not found: {filename}")
            except json.JSONDecodeError as e:
                self.errors.append(f"Invalid JSON in {filename}: {e}")
            except Exception as e:
                self.errors.append(f"Error loading {filename}: {e}")

    def validate_blocks(self) -> None:
        """Validate block configurations."""
        if "blocks" not in self.assets:
            self.errors.append("Blocks asset file not loaded")
            return

        blocks = self.assets["blocks"].get("blocks", {})
        
        if not blocks:
            self.errors.append("No blocks defined in blocks_config.json")
            return

        self.info.append(f"✓ Found {len(blocks)} block types")

        required_fields = {"color", "texture", "hardness", "harvest_time", "sound_category"}
        
        for block_name, block_config in blocks.items():
            # Check required fields
            missing = required_fields - set(block_config.keys())
            if missing:
                self.warnings.append(
                    f"Block '{block_name}' missing fields: {', '.join(missing)}"
                )

            # Validate color format
            if "color" in block_config:
                color = block_config["color"]
                if not isinstance(color, list) or len(color) != 3:
                    self.errors.append(
                        f"Block '{block_name}': Invalid color format. Expected [R, G, B]"
                    )
                elif not all(0 <= c <= 255 for c in color):
                    self.errors.append(
                        f"Block '{block_name}': Color values must be 0-255"
                    )

            # Validate numeric fields
            if "hardness" in block_config:
                if not isinstance(block_config["hardness"], (int, float)):
                    self.errors.append(
                        f"Block '{block_name}': Hardness must be numeric"
                    )

    def validate_items(self) -> None:
        """Validate item configurations."""
        if "items" not in self.assets:
            self.warnings.append("Items asset file not found")
            return

        items = self.assets["items"].get("items", {})
        
        if not items:
            self.warnings.append("No items defined in items_config.json")
            return

        self.info.append(f"✓ Found {len(items)} item types")

        required_fields = {"name", "rarity", "max_stack", "weight", "description"}
        
        for item_name, item_config in items.items():
            missing = required_fields - set(item_config.keys())
            if missing:
                self.warnings.append(
                    f"Item '{item_name}' missing fields: {', '.join(missing)}"
                )

            # Validate max_stack
            if "max_stack" in item_config:
                if not isinstance(item_config["max_stack"], int) or item_config["max_stack"] < 1:
                    self.errors.append(
                        f"Item '{item_name}': Invalid max_stack value"
                    )

    def validate_crafting(self) -> None:
        """Validate crafting recipes and references to items."""
        if "crafting" not in self.assets:
            self.warnings.append("Crafting asset file not found")
            return

        recipes = self.assets["crafting"].get("crafting_recipes", {})
        items = self.assets["items"].get("items", {}) if "items" in self.assets else {}

        if not recipes:
            self.warnings.append("No crafting recipes defined")
            return

        self.info.append(f"✓ Found {len(recipes)} crafting recipes")

        for recipe_name, recipe in recipes.items():
            # Validate inputs
            if "input" in recipe:
                for ingredient in recipe["input"]:
                    item_name = ingredient.get("item")
                    if item_name and items and item_name not in items:
                        self.warnings.append(
                            f"Recipe '{recipe_name}': Input item '{item_name}' not found in items"
                        )

            # Validate outputs
            if "output" in recipe:
                output = recipe["output"]
                item_name = output.get("item")
                if item_name and items and item_name not in items:
                    self.warnings.append(
                        f"Recipe '{recipe_name}': Output item '{item_name}' not found in items"
                    )

    def validate_particles(self) -> None:
        """Validate particle effect configurations."""
        if "particles" not in self.assets:
            self.warnings.append("Particles asset file not found")
            return

        effects = self.assets["particles"].get("particle_effects", {})
        
        if not effects:
            self.warnings.append("No particle effects defined")
            return

        self.info.append(f"✓ Found {len(effects)} particle effects")

        for effect_name, effect in effects.items():
            if "color" in effect:
                color = effect["color"]
                if not isinstance(color, list) or len(color) != 3:
                    self.errors.append(
                        f"Particle '{effect_name}': Invalid color format"
                    )

    def validate_animations(self) -> None:
        """Validate animation configurations."""
        if "animations" not in self.assets:
            self.warnings.append("Animations asset file not found")
            return

        animations = self.assets["animations"].get("animations", {})
        
        if not animations:
            self.warnings.append("No animations defined")
            return

        self.info.append(f"✓ Found animation definitions")

    def validate_references(self) -> None:
        """Validate cross-references between assets."""
        blocks = self.assets.get("blocks", {}).get("blocks", {})
        items = self.assets.get("items", {}).get("items", {})
        
        # Check item "obtained_from" references blocks
        for item_name, item in items.items():
            if "obtained_from" in item:
                for block_ref in item["obtained_from"]:
                    if block_ref not in blocks:
                        self.warnings.append(
                            f"Item '{item_name}': Block reference '{block_ref}' not found"
                        )

    def run_all_validations(self) -> None:
        """Run all validation checks."""
        self.validate_blocks()
        self.validate_items()
        self.validate_crafting()
        self.validate_particles()
        self.validate_animations()
        self.validate_references()

    def print_report(self) -> None:
        """Print validation report."""
        print("\n" + "="*50)
        print("ASSET VALIDATION REPORT")
        print("="*50)
        
        if self.info:
            print("\n✓ INFO:")
            for msg in self.info:
                print(f"  {msg}")
        
        if self.warnings:
            print("\n⚠ WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.errors:
            print("\n✗ ERRORS:")
            for msg in self.errors:
                print(f"  {msg}")
        
        print("\n" + "="*50)
        status = "✗ FAILED" if self.errors else ("⚠ PASSED (with warnings)" if self.warnings else "✓ PASSED")
        print(f"Status: {status}")
        print(f"Errors: {len(self.errors)} | Warnings: {len(self.warnings)} | Info: {len(self.info)}")
        print("="*50 + "\n")

    def get_status(self) -> Tuple[bool, int, int]:
        """Get validation status.
        
        Returns:
            Tuple of (is_valid, error_count, warning_count)
        """
        return (len(self.errors) == 0, len(self.errors), len(self.warnings))


if __name__ == "__main__":
    validator = AssetValidator()
    validator.run_all_validations()
    validator.print_report()
    
    is_valid, errors, warnings = validator.get_status()
    sys.exit(0 if is_valid else 1)
