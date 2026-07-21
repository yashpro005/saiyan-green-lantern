from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math
import json
import os
import sys
from terabox_sync import TeraboxSync

app = Ursina()

# --- Terabox Cloud Sync Setup ---
TERABOX_ENABLED = False
terabox_sync = None

def initialize_terabox_sync(email: str = None, password: str = None):
    """Initialize Terabox cloud sync"""
    global TERABOX_ENABLED, terabox_sync
    
    try:
        if email and password:
            print("🔐 Attempting Terabox authentication...")
            terabox_sync = TeraboxSync()
            if terabox_sync.authenticate(email, password):
                TERABOX_ENABLED = True
                print("✅ Terabox sync enabled!")
                return True
        print("⚠️  Terabox sync disabled - no credentials provided")
        return False
    except Exception as e:
        print(f"⚠️  Terabox initialization failed: {e}")
        return False

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
    'teleporting': False,
    'playtime': 0,
    'score': 0
}

# --- UI Components (The HUD) ---
hud_panel = Entity(parent=camera.ui, model='quad', scale=(0.4, 0.2), origin=(0.5, -0.5), 
                   position=(0.45, -0.45), color=color.black66)

stamina_bar = Entity(parent=camera.ui, model='quad', color=color.gold, 
                     scale=(0.3, 0.02), position=(0.7, -0.42))

storm_text = Text(text='STORM WARNING [!]', color=color.red, scale=1.5, 
                  position=(0.55, -0.45), origin=(0,0))

# Cloud sync status indicator
cloud_status = Text(text='☁️ Local', color=color.cyan, scale=0.8, 
                    position=(0.7, 0.45), origin=(0,0))

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
        self.block_type = block_type

    def input(self, key):
        if self.hovered:
            if self.block_type in ['villager', 'animal', 'mythic_entity']:
                if key == 'left mouse down':
                    verbal_interaction(self.block_type)
                    return
            
            if key == 'left mouse down':
                destroy(self)
                state['score'] += 10
            if key == 'right mouse down':
                Voxel(position=self.position + mouse.normal, block_type=state['selected'])
                state['score'] += 5

# --- NPC Dialogue and Interaction Logic ---
def verbal_interaction(entity_type):
    dialogues = {
        'villager': [
            "Welcome to Imaland, traveler.",
            "The sands are harsh today.",
            "Have you seen the ruins to the North?",
            "Save your progress to the cloud!"
        ],
        'animal': [
            "*The creature tilts its head curiously*",
            "*Soft rustling noises*",
            "*A friendly low growl*"
        ],
        'mythic_entity': [
            "I have seen worlds beyond the portals.",
            "The Tithe-Ore holds secrets of the ancients.",
            "Your stamina is but a flicker in the storm.",
            "Cloud sync is essential for eternal progress."
        ]
    }
    speech = random.choice(dialogues.get(entity_type, ["..."]))
    print(f"[{entity_type.upper()}]: {speech}")

    if entity_type == 'mythic_entity':
        state['stamina'] = min(100, state['stamina'] + 20)
        print("✨ The being grants you a burst of energy!")

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
                        pass

# --- World Generation ---
def generate_imaland():
    print("🌍 Generating world...")
    for z in range(60):
        for x in range(60):
            y_height = int(random.uniform(-1, 4) + math.sin(x*0.1) * 2)
            y_offset = max(0, y_height)

            is_cave = random.random() > 0.92 and y_offset > 1

            if not is_cave:
                b_type = 'grass' if x < 40 else 'sand'
                Voxel(position=(x, y_offset, z), block_type=b_type)

                if random.random() > 0.995:
                    generate_structure(x, y_offset + 1, z)

                if random.random() > 0.999:
                    for py in range(3):
                        Voxel(position=(x, y_offset+1+py, z), block_type='portal')
                
                if random.random() > 0.997:
                    Voxel(position=(x, y_offset + 1, z), block_type='villager')
                elif random.random() > 0.995:
                    Voxel(position=(x, y_offset + 1, z), block_type='animal')
                elif random.random() > 0.999:
                    Voxel(position=(x, y_offset + 1, z), block_type='mythic_entity')

            if y_offset < 1:
                Voxel(position=(x, 0, z), block_type='water')
    
    print("✅ World generation complete!")

# --- Save/Load System with Cloud Sync ---
def save_game_data():
    """Save game data locally and optionally to cloud"""
    data = {
        'position': (player.x, player.y, player.z),
        'stamina': state['stamina'],
        'score': state['score'],
        'playtime': state['playtime'],
        'timestamp': datetime.now().isoformat()
    }
    
    with open('save_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("💾 Game saved locally!")
    
    # Upload to Terabox if enabled
    if TERABOX_ENABLED and terabox_sync:
        if terabox_sync.upload_save('save_data.json'):
            cloud_status.text = '☁️ Cloud Synced ✅'
            cloud_status.color = color.green
            print("☁️ Uploaded to Terabox cloud!")
        else:
            cloud_status.text = '☁️ Sync Failed ❌'
            cloud_status.color = color.red

def load_game_data():
    """Load game data from local storage"""
    if os.path.exists('save_data.json'):
        try:
            with open('save_data.json', 'r') as f:
                data = json.load(f)
            
            player.position = tuple(data['position'])
            state['stamina'] = data['stamina']
            state['score'] = data['score']
            state['playtime'] = data['playtime']
            
            print("✅ Game data loaded!")
            return True
        except Exception as e:
            print(f"⚠️  Error loading save: {e}")
            return False
    return False

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
    map_player_dot.x = (player.x / 60) - 0.5
    map_player_dot.y = (player.z / 60) - 0.5

def check_teleportation():
    if state.get('teleporting'):
        return

    if player.y > 5:
        player.position = (0, 10, 0)
        print("🌀 Teleported to a New World!")

# --- Main Game Loop ---
save_timer = 0
cloud_sync_timer = 0
from datetime import datetime

def update():
    global save_timer, cloud_sync_timer
    
    state['playtime'] += time.dt
    
    handle_stamina_drain()
    pulse_storm_warning()
    spawn_rain_particles()
    update_map()
    
    # Auto-save every 30 seconds
    save_timer += time.dt
    if save_timer >= 30:
        save_game_data()
        save_timer = 0
    
    # Cloud sync every 60 seconds
    if TERABOX_ENABLED:
        cloud_sync_timer += time.dt
        if cloud_sync_timer >= 60:
            print("🔄 Attempting cloud sync...")
            save_game_data()
            cloud_sync_timer = 0
    
    check_teleportation()
    
    # Game Over condition
    if state['stamina'] <= 0:
        print("💀 GAME OVER: Stamina depleted!")
        print(f"📊 Final Score: {state['score']}")
        save_game_data()
        application.quit()

# --- Initialization ---
def main():
    global TERABOX_ENABLED, terabox_sync
    
    print("=" * 60)
    print("🎮 Imaland: Sands of Redemption")
    print("=" * 60)
    
    # Check for Terabox credentials
    terabox_email = os.getenv('TERABOX_EMAIL')
    terabox_password = os.getenv('TERABOX_PASSWORD')
    
    if terabox_email and terabox_password:
        initialize_terabox_sync(terabox_email, terabox_password)
    else:
        print("\n💡 Tip: Set TERABOX_EMAIL and TERABOX_PASSWORD environment variables")
        print("   to enable cloud storage sync for your game saves!\n")
    
    # Initialize player and world
    player = FirstPersonController()
    player.cursor.visible = False
    generate_imaland()
    Sky(color=color.rgb(30, 30, 35))
    
    # Load previous save if exists
    if os.path.exists('save_data.json'):
        if load_game_data():
            print("✨ Previous progress restored!")
    
    print("\n📋 Controls:")
    print("  • WASD - Move")
    print("  • Mouse - Look around")
    print("  • Left Click - Mine blocks")
    print("  • Right Click - Place blocks")
    print("  • ESC - Quit")
    
    if TERABOX_ENABLED:
        print("  • ☁️  Cloud syncing enabled!")
    
    print("\n🎮 Game Started!\n")

# Run initialization
main()

# Start game loop
app.run()
