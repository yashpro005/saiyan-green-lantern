"""Imaland: Sands of Redemption - Enhanced with Asset Manager

Integrates the AssetManager for centralized asset management.
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from assets.asset_manager import AssetManager
import random
import math
import json

app = Ursina()

# --- Initialize Asset Manager ---
try:
    assets = AssetManager(assets_dir="assets")
    print("✓ Asset Manager loaded successfully")
except Exception as e:
    print(f"✗ Failed to load Asset Manager: {e}")
    assets = None

# --- Window & Theme Configuration ---
window.title = 'Imaland: Sands of Redemption'
window.borderless = False
window.color = color.black
window.exit_button.visible = False

# --- Survival Variables ---
state = {
    'stamina': 100,
    'is_storming': True,
    'selected': 'grass',
    'heat_level': 0.1,
    'teleporting': False,
    'inventory': {}
}

# --- UI Components (The HUD) ---
hud_panel = Entity(parent=camera.ui, model='quad', scale=(0.4, 0.2), origin=(0.5, -0.5), 
                   position=(0.45, -0.45), color=color.black66)

stamina_bar = Entity(parent=camera.ui, model='quad', color=color.gold, 
                     scale=(0.3, 0.02), position=(0.7, -0.42))

storm_text = Text(text='STORM WARNING [!]', color=color.red, scale=1.5, 
                  position=(0.55, -0.45), origin=(0,0))

# Mini-Map UI
mini_map = Entity(parent=camera.ui, model='quad', scale=(0.15, 0.15),
                  position=(-0.7, 0.4), color=color.rgba(0,0,0,150))
map_player_dot = Entity(parent=mini_map, model='circle', scale=(0.05, 0.05), color=color.red)

# Selected block indicator
selected_block_text = Text(text='Selected: Grass', color=color.white, scale=1, 
                           position=(0.55, -0.35), origin=(0,0))

# --- The Voxel Logic with Asset Integration ---
class Voxel(Button):
    def __init__(self, position=(0,0,0), block_type='grass'):
        # Get block config from asset manager
        if assets:
            config = assets.get_block_config(block_type)
            if config:
                color_rgb = tuple(config['color'])
                texture = config.get('texture', 'white_cube')
            else:
                color_rgb = (128, 128, 128)
                texture = 'white_cube'
        else:
            color_rgb = (128, 128, 128)
            texture = 'white_cube'

        super().__init__(
            parent=scene, position=position, model='cube', origin_y=0.5,
            texture=texture,
            color=color.rgb(*color_rgb),
            highlight_color=color.light_gray
        )
        self.block_type = block_type
        if assets:
            self.config = assets.get_block_config(block_type)
        else:
            self.config = {}

    def input(self, key):
        if self.hovered:
            # Check for NPC interaction
            if self.block_type in ['villager', 'animal', 'mythic_entity']:
                if key == 'left mouse down':
                    verbal_interaction(self.block_type)
                    return  # Don't destroy NPCs
            
            # Standard block destruction/creation
            if key == 'left mouse down':
                destroy(self)
                # Add block to inventory
                if assets:
                    block_config = assets.get_block_config(self.block_type)
                    if block_config and block_config.get('dropable'):
                        add_to_inventory(self.block_type)
            
            if key == 'right mouse down':
                Voxel(position=self.position + mouse.normal, block_type=state['selected'])

# --- Inventory System ---
def add_to_inventory(item_name, count=1):
    """Add item to player inventory."""
    if item_name not in state['inventory']:
        state['inventory'][item_name] = 0
    state['inventory'][item_name] += count
    print(f"[Inventory] +{count}x {item_name}")

def get_inventory_item(item_name):
    """Get count of item in inventory."""
    return state['inventory'].get(item_name, 0)

def remove_from_inventory(item_name, count=1):
    """Remove item from inventory."""
    if item_name in state['inventory']:
        state['inventory'][item_name] = max(0, state['inventory'][item_name] - count)

# --- NPC Dialogue and Interaction Logic ---
def verbal_interaction(entity_type):
    if not assets:
        print(f"[{entity_type.upper()}]: ...")
        return

    npc_config = assets.get_npc_config(entity_type)
    if not npc_config:
        print(f"[{entity_type.upper()}]: ...")
        return

    dialogues = npc_config.get('dialogues', ["..."])
    speech = random.choice(dialogues)
    print(f"[{entity_type.upper()}]: {speech}")

    # Mythical Blessing
    if entity_type == 'mythic_entity':
        state['stamina'] = min(100, state['stamina'] + 20)
        print("The being grants you a burst of energy!")

# --- Block Selection System ---
def get_block_list():
    """Get list of available blocks from asset manager."""
    if assets:
        return assets.list_all_blocks()
    return ['grass', 'sand', 'stone', 'ore', 'water', 'planks', 'brick', 'portal']

def cycle_selected_block(direction=1):
    """Cycle through available blocks."""
    blocks = get_block_list()
    current_index = blocks.index(state['selected']) if state['selected'] in blocks else 0
    current_index = (current_index + direction) % len(blocks)
    state['selected'] = blocks[current_index]
    
    # Update UI
    if assets:
        description = assets.get_block_description(state['selected'])
        selected_block_text.text = f"Selected: {state['selected']} - {description}"
    else:
        selected_block_text.text = f"Selected: {state['selected']}"

# --- Environment: Atmospheric Rain/Fog ---
scene.fog_color = color.rgb(50, 55, 50)
scene.fog_density = 0.05

def create_rain():
    """Create rain particle effect using asset config."""
    count = 100
    if assets:
        rain_config = assets.get_particle_effect('rain')
        if rain_config:
            count = rain_config.get('particle_count', 100)
    
    for i in range(count):
        Particle(
            position=(random.uniform(-20, 20), 20, random.uniform(-20, 20)),
            velocity=(0, -random.uniform(10, 20), 0),
            color=color.rgba(200, 200, 255, 100),
            scale=0.05,
            lifetime=2
        )

# --- Structure Generation ---
def generate_structure(x, y, z):
    """Simple ruin/room generator"""
    for dx in range(3):
        for dz in range(3):
            for dy in range(3):
                if dy == 0 or (dx % 2 == 0 or dz % 2 == 0):
                    try:
                        Voxel(position=(x+dx, y+dy, z+dz), block_type='brick')
                    except:
                        pass

# --- World Generation (Canyon/Jungle Border) ---
def generate_imaland():
    """Generate the Imaland world using asset-defined block types."""
    for z in range(60):
        for x in range(60):
            # Terrain and Caves
            y_height = int(random.uniform(-1, 4) + math.sin(x*0.1) * 2)
            y_offset = max(0, y_height)

            # Sub-surface caves
            is_cave = random.random() > 0.92 and y_offset > 1

            if not is_cave:
                b_type = 'grass' if x < 40 else 'sand'
                Voxel(position=(x, y_offset, z), block_type=b_type)

                # Rare Civilization Outposts
                if random.random() > 0.995:
                    generate_structure(x, y_offset + 1, z)

                # Portals to New Worlds
                if random.random() > 0.999:
                    for py in range(3):
                        Voxel(position=(x, y_offset+1+py, z), block_type='portal')
                
                # Population Logic
                if random.random() > 0.997:
                    Voxel(position=(x, y_offset + 1, z), block_type='villager')
                elif random.random() > 0.995:
                    Voxel(position=(x, y_offset + 1, z), block_type='animal')
                elif random.random() > 0.999:
                    Voxel(position=(x, y_offset + 1, z), block_type='mythic_entity')

            # Underwater logic / Caves
            if y_offset < 1:
                Voxel(position=(x, 0, z), block_type='water')

# --- Save/Load System ---
def save_game():
    """Save game state with inventory."""
    data = {
        'position': (player.x, player.y, player.z),
        'stamina': state['stamina'],
        'selected': state['selected'],
        'inventory': state['inventory']
    }
    with open('save_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Game Auto-Saved!")

def load_game():
    """Load game state from save file."""
    try:
        with open('save_data.json', 'r') as f:
            data = json.load(f)
        state['stamina'] = data.get('stamina', 100)
        state['selected'] = data.get('selected', 'grass')
        state['inventory'] = data.get('inventory', {})
        print("Game Loaded!")
        return True
    except FileNotFoundError:
        print("No save file found. Starting new game.")
        return False

def check_teleportation():
    """Check if player is near a portal and teleport"""
    if state.get('teleporting'):
        return

    if player.y > 5:
        player.position = (0, 10, 0)
        print("Teleported to a New World!")

# --- Game Loop Helper Functions ---
def handle_stamina_drain():
    if state['stamina'] > 0:
        state['stamina'] -= time.dt * state['heat_level']
        stamina_bar.scale_x = (state['stamina'] / 100) * 0.3

def pulse_storm_warning():
    storm_text.alpha = (sin(time.time() * 5) + 1) / 2

def spawn_rain_particles():
    if state['is_storming'] and random.random() > 0.8:
        create_rain()

def update_map():
    """Update mini-map player position"""
    map_player_dot.x = (player.x / 60) - 0.5
    map_player_dot.y = (player.z / 60) - 0.5

# --- Input Handling ---
def input_handler(key):
    """Handle user input."""
    if key == 'e':  # Cycle through blocks
        cycle_selected_block(1)
    elif key == 'q':  # Reverse cycle
        cycle_selected_block(-1)
    elif key == 'i':  # Show inventory
        print_inventory()
    elif key == 'escape':  # Save and quit
        save_game()
        application.quit()

def print_inventory():
    """Print current inventory."""
    if not state['inventory']:
        print("[Inventory] Empty")
        return
    print("[Inventory]")
    for item, count in state['inventory'].items():
        print(f"  {item}: {count}")

# --- Main Game Loop (Survival Logic) ---
save_timer = 0

def update():
    global save_timer
    
    handle_stamina_drain()
    pulse_storm_warning()
    spawn_rain_particles()
    update_map()
    
    # Auto-save every 30 seconds
    save_timer += time.dt
    if save_timer >= 30:
        save_game()
        save_timer = 0
    
    check_teleportation()
    
    # Game Over condition
    if state['stamina'] <= 0:
        print("GAME OVER: Stamina depleted!")
        save_game()
        application.quit()

# --- Initialization ---
player = FirstPersonController()
player.cursor.visible = False

# Print asset summary if available
if assets:
    assets.print_asset_summary()

generate_imaland()
Sky(color=color.rgb(30, 30, 35))

print("\\n=== CONTROLS ===\")
print("WASD - Move")
print("Mouse - Look")
print("Left Click - Mine Block")
print("Right Click - Place Block")
print("E - Next Block Type")
print("Q - Previous Block Type")
print("I - Show Inventory")
print("ESC - Save & Quit")
print(\"=\"*30 + \"\\n\")

# Load previous save if available
load_game()

app.run()
