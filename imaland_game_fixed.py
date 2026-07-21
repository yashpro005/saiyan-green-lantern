from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math
import json

app = Ursina()

# --- Window & Theme Configuration ---
window.title = 'Imaland: Sands of Redemption'
window.borderless = False
window.color = color.black
window.exit_button.visible = False

# --- Assets & Palettes ---
BLOCKS = {
    'grass':         {'color': color.rgb(45, 90, 45),      'texture': 'white_cube'},
    'sand':          {'color': color.rgb(194, 178, 128),   'texture': 'white_cube'},
    'stone':         {'color': color.rgb(100, 100, 100),   'texture': 'white_cube'},
    'ore':           {'color': color.rgb(150, 0, 255),     'texture': 'white_cube'},
    'water':         {'color': color.rgb(50, 100, 200),    'texture': 'white_cube'},
    'planks':        {'color': color.rgb(120, 80, 50),     'texture': 'white_cube'},
    'brick':         {'color': color.rgb(150, 50, 50),     'texture': 'white_cube'},
    'portal':        {'color': color.rgb(0, 255, 100),     'texture': 'white_cube'},
    'workbench':     {'color': color.rgb(100, 80, 20),     'texture': 'white_cube'},
    'furnace':       {'color': color.rgb(60, 60, 60),      'texture': 'white_cube'},
    'villager':      {'color': color.rgb(200, 150, 120),   'texture': 'white_cube'},
    'animal':        {'color': color.rgb(150, 75, 0),      'texture': 'white_cube'},
    'mythic_entity': {'color': color.rgb(0, 255, 255),     'texture': 'white_cube'},
}

# --- Survival Variables ---
state = {
    'stamina': 100,
    'is_storming': True,
    'selected': 'grass',
    'heat_level': 0.1,
    'teleporting': False
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

# --- The Voxel Logic ---
class Voxel(Button):
    def __init__(self, position=(0,0,0), block_type='grass'):
        super().__init__(
            parent=scene, position=position, model='cube', origin_y=0.5,
            texture=BLOCKS[block_type]['texture'],
            color=BLOCKS[block_type]['color'],
            highlight_color=color.light_gray
        )
        self.block_type = block_type  # Store block type as attribute

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
            if key == 'right mouse down':
                Voxel(position=self.position + mouse.normal, block_type=state['selected'])

# --- NPC Dialogue and Interaction Logic ---
def verbal_interaction(entity_type):
    dialogues = {
        'villager': [
            "Welcome to Imaland, traveler.",
            "The sands are harsh today.",
            "Have you seen the ruins to the North?"
        ],
        'animal': [
            "*The creature tilts its head curiously*",
            "*Soft rustling noises*",
            "*A friendly low growl*"
        ],
        'mythic_entity': [
            "I have seen worlds beyond the portals.",
            "The Tithe-Ore holds secrets of the ancients.",
            "Your stamina is but a flicker in the storm."
        ]
    }
    speech = random.choice(dialogues.get(entity_type, ["..."]))
    print(f"[{entity_type.upper()}]: {speech}")

    # Mythical Blessing
    if entity_type == 'mythic_entity':
        state['stamina'] = min(100, state['stamina'] + 20)
        print("The being grants you a burst of energy!")

# --- Environment: Atmospheric Rain/Fog ---
scene.fog_color = color.rgb(50, 55, 50)
scene.fog_density = 0.05

def create_rain():
    for i in range(100):
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
                        pass  # Skip if out of bounds or error

# --- World Generation (Canyon/Jungle Border) ---
def generate_imaland():
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
    data = {
        'position': (player.x, player.y, player.z),
        'stamina': state['stamina']
    }
    with open('save_data.json', 'w') as f:
        json.dump(data, f)
    print("Game Auto-Saved!")

def check_teleportation():
    """Check if player is near a portal and teleport"""
    if state.get('teleporting'):
        return

    # Simple proximity check for portals
    # In a full implementation, you'd track portal positions
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
        application.quit()

# --- Initialization ---
player = FirstPersonController()
player.cursor.visible = False
generate_imaland()
Sky(color=color.rgb(30, 30, 35))  # Dark, overcast sky

print("Game Started! Use WASD to move, mouse to look. Click to mine, right-click to place blocks.")

app.run()
