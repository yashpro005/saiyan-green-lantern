# Imaland Assets System

Comprehensive asset management system for **Imaland: Sands of Redemption** game.

## Directory Structure

```
assets/
├── blocks_config.json       # Block definitions and properties
├── particles_config.json    # Particle effect definitions
├── sounds_config.json       # Sound effect mappings
├── npc_config.json          # NPC and creature configurations
├── animations_config.json   # Animation definitions
├── asset_manager.py         # Python asset manager class
└── README.md                # This file
```

## Asset Categories

### Blocks (blocks_config.json)
Defines all block types in the game with properties:
- **Color**: RGB values and hex codes
- **Hardness**: Mining difficulty (0.0 = soft, 3.0+ = hard)
- **Harvest Time**: Time to break in seconds
- **Sound Category**: Audio classification
- **Rarity**: Block rarity level
- **Special Properties**: Glow, liquid, animated, interactive

**Available Blocks:**
- `grass` - Soft terrain block
- `sand` - Desert terrain
- `stone` - Hard stone
- `ore` - Rare Tithe-Ore (glowing)
- `water` - Liquid water
- `planks` - Wooden blocks
- `brick` - Crafted brick
- `portal` - Animated portal to other worlds
- `workbench` - Interactive crafting station
- `furnace` - Interactive smelting furnace
- `villager` - NPC entity
- `animal` - Creature entity
- `mythic_entity` - Legendary entity

### Particle Effects (particles_config.json)
Defines visual effects for various game events:
- `rain` - Falling rain particles
- `mining_dust` - Dust cloud when mining
- `portal_glow` - Glowing effect around portals
- `mystical_aura` - Aura around mythical entities
- `magic_burst` - Burst effect for magical events
- `stamina_drain` - Visual effect for stamina loss
- `healing_light` - Visual effect for stamina recovery

Each effect includes:
- Particle count
- Lifetime duration
- Velocity and variance
- Color and alpha
- Animation properties

### Sounds (sounds_config.json)
Audio mappings organized by category:
- **Blocks**: Footsteps, breaking, placing
- **Entities**: NPC and creature sounds
- **UI**: Menu interactions
- **Environment**: Rain, wind, thunder
- **Portal**: Activation and ambient sounds

### NPCs (npc_config.json)
Configuration for interactive entities:
- **Villager**: Friendly NPC with trades and quests
- **Animal**: Passive creatures
- **Mythic Entity**: Legendary being with special interactions

Each NPC includes:
- Dialogue options
- Interaction types
- Behavior AI
- Spawn rates
- Special effects

### Animations (animations_config.json)
Animation definitions for:
- **Player**: Walk, run, jump, mine, place blocks
- **Entities**: Idle, walk, run, talk, communicate
- **Blocks**: Rotation, scaling, pulsing effects

## Using the Asset Manager

### Basic Usage

```python
from assets.asset_manager import AssetManager

# Initialize the asset manager
assets = AssetManager()

# Get block configuration
grass_config = assets.get_block_config('grass')
print(grass_config['color'])  # [45, 90, 45]

# Get block color
ore_color = assets.get_block_color('ore')  # (150, 0, 255)

# Get all blocks
all_blocks = assets.get_all_blocks()

# Get particle effect
rain_effect = assets.get_particle_effect('rain')

# Get NPC configuration
villager_config = assets.get_npc_config('villager')

# List all available assets
blocks = assets.list_all_blocks()
effects = assets.list_particle_effects()
ncps = assets.list_npc_types()
```

### Integration with Game

Update `imaland_game_fixed.py` to use the asset manager:

```python
from assets.asset_manager import AssetManager
from ursina import *

# Initialize asset manager
assets = AssetManager()

# Create blocks with asset config
class Voxel(Button):
    def __init__(self, position=(0,0,0), block_type='grass'):
        config = assets.get_block_config(block_type)
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=config['texture'],
            color=color.rgb(*config['color']),
            highlight_color=color.light_gray
        )
        self.block_type = block_type
        self.config = config
```

## Adding New Assets

### Add a New Block Type

Edit `blocks_config.json` and add to the `blocks` object:

```json
"new_block": {
  "color": [R, G, B],
  "rgb_hex": "#RRGGBB",
  "texture": "white_cube",
  "hardness": 1.5,
  "harvest_time": 1.5,
  "sound_category": "stone",
  "dropable": true,
  "description": "Description of new block"
}
```

### Add a New Particle Effect

Edit `particles_config.json` and add to the `particle_effects` object:

```json
"new_effect": {
  "type": "effect_type",
  "particle_count": 50,
  "lifetime": 2.0,
  "color": [R, G, B],
  "alpha": 200,
  "scale": 0.1
}
```

## Configuration File Format

All asset files use JSON format for easy editing:

```json
{
  "assets_category": {
    "asset_name": {
      "property1": "value1",
      "property2": 123,
      "property3": [1, 2, 3]
    }
  }
}
```

## Best Practices

1. **Color Consistency**: Use RGB values 0-255 for consistency
2. **Naming**: Use snake_case for all asset names
3. **Descriptions**: Add descriptions for complex assets
4. **Organization**: Keep related configs in the same file
5. **Validation**: Test new assets with the asset manager

## Testing Assets

Run the asset manager test:

```bash
python assets/asset_manager.py
```

This will:
1. Load all asset files
2. Print a summary of loaded assets
3. Display sample configurations
4. Validate the asset system

## Performance Notes

- Assets are loaded once on startup and cached in memory
- JSON parsing is fast for the current asset size (~50KB)
- Consider lazy-loading for very large asset collections
- Sound files should be stored separately to keep JSON lightweight

## Future Enhancements

- [ ] Asset hot-reloading for development
- [ ] Asset validation and schema checking
- [ ] Asset compression for distribution
- [ ] Texture atlas generation
- [ ] Audio codec optimization
- [ ] Asset localization support
