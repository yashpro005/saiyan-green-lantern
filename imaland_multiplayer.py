"""
Imaland Multiplayer Game
Integrated multiplayer game client with Terabox cloud sync
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math
import json
import os
import threading
import time
from datetime import datetime
from multiplayer_session import MultiplayerSessionManager, PlayerSession, BlockChange
from multiplayer_terabox_sync import MultiplayerTeraboxSync, setup_multiplayer_terabox_sync

app = Ursina()

# --- Multiplayer Configuration ---
MULTIPLAYER_ENABLED = False
TERABOX_ENABLED = False
session_manager = None
terabox_sync = None
other_players = {}  # Dict of other player models
sync_thread = None
should_sync = False
last_sync_time = 0
SYNC_INTERVAL = 30  # Sync every 30 seconds

# --- Window & Theme Configuration ---
window.title = 'Imaland: Sands of Redemption - Multiplayer'
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

# Multiplayer status indicator
mp_status = Text(text='🎮 Single Player', color=color.yellow, scale=0.8, 
                 position=(0.7, 0.45), origin=(0,0))

# Cloud sync status indicator
cloud_status = Text(text='☁️ Local', color=color.cyan, scale=0.8, 
                    position=(0.7, 0.40), origin=(0,0))

# Player count
player_count_text = Text(text='👥 Players: 1', color=color.white, scale=0.8, 
                         position=(0.7, 0.35), origin=(0,0))

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
                # Record block change if multiplayer enabled
                if session_manager:
                    session_manager.record_block_change(
                        self.position, 'destroy', self.block_type
                    )
            if key == 'right mouse down':
                Voxel(position=self.position + mouse.normal, block_type=state['selected'])
                state['score'] += 5
                # Record block change if multiplayer enabled
                if session_manager:
                    session_manager.record_block_change(
                        self.position + mouse.normal, 'place', state['selected']
                    )

# --- NPC Dialogue and Interaction Logic ---
def verbal_interaction(entity_type):
    dialogues = {
        'villager': [
            "Welcome to Imaland, traveler.",
            "The sands are harsh today.",
            "Have you seen the ruins to the North?",
            "I see other adventurers here!"
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
            "Multiplayer brings new dimensions to this realm."
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

# --- Multiplayer Functions ---
def create_player_model(player_id: str, player_name: str, position: tuple):
    """Create a visual representation of another player"""
    player_model = Entity(
        model='cube',
        color=color.random_color(),
        scale=(0.5, 1.5, 0.5),
        position=position
    )
    # Add player name label
    name_label = Text(text=player_name, origin=(0, 0), scale=1, 
                     parent=player_model, y=1)
    
    return {'model': player_model, 'label': name_label, 'name': player_name}

def update_other_players():
    """Update positions of other players"""
    if not session_manager:
        return
    
    all_players = session_manager.get_all_players()
    current_player_id = session_manager.current_player_id
    
    # Update existing players
    for player_id, player_session in all_players.items():
        if player_id == current_player_id:
            continue
        
        if player_id not in other_players:
            # Create new player model
            other_players[player_id] = create_player_model(
                player_id, player_session.player_name, player_session.position
            )
        else:
            # Update position
            other_players[player_id]['model'].position = player_session.position
    
    # Remove disconnected players
    disconnected = [pid for pid in other_players if pid not in all_players]
    for player_id in disconnected:
        destroy(other_players[player_id]['model'])
        destroy(other_players[player_id]['label'])
        del other_players[player_id]
    
    # Update player count
    total_players = len(all_players)
    player_count_text.text = f'👥 Players: {total_players}'

def sync_thread_func():
    """Background thread for cloud synchronization"""
    global last_sync_time, TERABOX_ENABLED
    
    while should_sync:
        try:
            current_time = time.time()
            if current_time - last_sync_time >= SYNC_INTERVAL:
                if TERABOX_ENABLED and terabox_sync:
                    world_state = session_manager.world_state
                    terabox_sync.full_sync(world_state)
                    last_sync_time = current_time
                    cloud_status.text = '☁️ Cloud Synced ✅'
                    cloud_status.color = color.green
                else:
                    cloud_status.text = '☁️ Local Only'
                    cloud_status.color = color.cyan
        except Exception as e:
            print(f"⚠️  Sync error: {e}")
            cloud_status.text = '☁️ Sync Error ❌'
            cloud_status.color = color.red
        
        time.sleep(5)  # Check every 5 seconds

def start_sync_thread():
    """Start background sync thread"""
    global sync_thread, should_sync
    should_sync = True
    sync_thread = threading.Thread(target=sync_thread_func, daemon=True)
    sync_thread.start()

def stop_sync_thread():
    """Stop background sync thread"""
    global should_sync
    should_sync = False

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

def check_teleportation():
    if state.get('teleporting'):
        return
    if player.y > 5:
        player.position = (0, 10, 0)
        print("🌀 Teleported to a New World!")

# --- Main Game Loop ---
save_timer = 0

def update():
    global save_timer
    
    state['playtime'] += time.dt
    
    handle_stamina_drain()
    pulse_storm_warning()
    spawn_rain_particles()
    update_map()
    update_other_players()
    
    # Update session manager with current player position
    if session_manager:
        session_manager.update_current_player_position((player.x, player.y, player.z))
        session_manager.update_current_player_stats(state['stamina'], state['score'])
    
    # Auto-save locally every 30 seconds
    save_timer += time.dt
    if save_timer >= 30:
        if session_manager:
            session_manager._save_world_state()
        save_timer = 0
    
    check_teleportation()
    
    # Game Over condition
    if state['stamina'] <= 0:
        print("💀 GAME OVER: Stamina depleted!")
        print(f"📊 Final Score: {state['score']}")
        if session_manager:
            session_manager._save_world_state()
        stop_sync_thread()
        application.quit()

# --- Initialization ---
def initialize_multiplayer(player_name: str, enable_terabox: bool = True):
    """Initialize multiplayer session"""
    global MULTIPLAYER_ENABLED, TERABOX_ENABLED, session_manager, terabox_sync
    
    print("\n" + "="*60)
    print("🎮 Imaland: Sands of Redemption - Multiplayer Edition")
    print("="*60)
    
    # Initialize session manager
    session_manager = MultiplayerSessionManager()
    session = session_manager.create_player_session(player_name)
    MULTIPLAYER_ENABLED = True
    mp_status.text = '🎮 Multiplayer ✅'
    mp_status.color = color.green
    
    # Setup Terabox sync if enabled
    if enable_terabox:
        print("\n💡 Setting up Terabox cloud sync...")
        terabox_email = "yashpro005@gmail.com"
        terabox_password = os.getenv('TERABOX_PASSWORD')
        
        if terabox_password:
            terabox_sync = setup_multiplayer_terabox_sync(terabox_email, terabox_password)
            if terabox_sync:
                TERABOX_ENABLED = True
                print("✅ Terabox sync initialized!")
                start_sync_thread()
        else:
            print("\n💡 Tip: Set TERABOX_PASSWORD environment variable")
            print("   to enable cloud storage sync!")
    
    print("\n📋 Controls:")
    print("  • WASD - Move")
    print("  • Mouse - Look around")
    print("  • Left Click - Mine blocks")
    print("  • Right Click - Place blocks")
    print("  • ESC - Quit")
    
    if MULTIPLAYER_ENABLED:
        print("  • 👥 Multiplayer enabled!")
    if TERABOX_ENABLED:
        print("  • ☁️  Cloud syncing enabled!")
    
    print("\n🎮 Game Started!\n")

def main():
    global player
    
    # Initialize game
    player = FirstPersonController()
    player.cursor.visible = False
    generate_imaland()
    Sky(color=color.rgb(30, 30, 35))
    
    # Start multiplayer with your player name
    player_name = os.getenv('PLAYER_NAME', 'Saiyan Warrior')
    initialize_multiplayer(player_name, enable_terabox=True)

# Run initialization
main()

# Start game loop
app.run()
