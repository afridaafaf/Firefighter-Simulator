from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time
import sys
import numpy as np

# Camera-related variables
camera_pos = (0, 30, 50)  # Increased height and distance
fovY = 60  # Field of view
GRID_LENGTH = 100  # Length of grid lines

# Game parameters
NUM_HOUSES = 8  # Number of houses in the game
MAX_HEALTH = 100  # Maximum health of a house
FIRE_DAMAGE = 0.04  # Fire damage per frame
WATER_HEAL = 3.0  # Reduced water healing to make extinguishing take longer
SPRAY_DISTANCE = 15.0  # Maximum distance to spray water
FIRE_PROBABILITY = 0.001  # Increased for more frequent fires
TRUCK_SPEED = 4.0  # Increased speed of the fire truck
WORLD_SIZE = 100  # Size of the game world
WATER_CAPACITY = 1500  # Maximum water capacity
WATER_USAGE_RATE = 0.8  # Water usage per frame when spraying
WATER_REFILL_RATE = 20  # Increased for faster refilling
COLLISION_DISTANCE = 6.0  # Distance for collision detection
WATER_REFILL_DISTANCE = 5.0  # Distance for automatic water refill
FIRE_POP_INTERVAL = 6.0  # Minimum interval between fire pops in seconds

# Add new constants for roads and water stations
ROAD_WIDTH = 10.0
ROAD_LENGTH = 80.0
WATER_STATION_DISTANCE = 40.0  # Distance between water stations

# New fire simulation parameters
WIND_DIRECTION = [1.0, 0.0, 0.0]  # Initial wind direction
WIND_SPEED = 1.0  # Wind speed multiplier
FIRE_SPREAD_RADIUS = 10.0  # Maximum distance for fire spread
FIRE_SPREAD_PROBABILITY = 0.3  # Probability of fire spreading to nearby objects
SMOKE_DENSITY = 0.5  # Base smoke density
MAX_SMOKE_DENSITY = 1.0  # Maximum smoke density
SMOKE_DISSIPATION_RATE = 0.1  # Rate at which smoke dissipates

# Fire types and their properties
FIRE_TYPES = {
    'CLASS_A': {'color': (1.0, 0.3, 0.0), 'extinguisher': 'water', 'spread_rate': 1.0},
    'CLASS_B': {'color': (1.0, 0.0, 0.0), 'extinguisher': 'foam', 'spread_rate': 1.5},
    'CLASS_C': {'color': (0.0, 0.0, 1.0), 'extinguisher': 'dry_chemical', 'spread_rate': 1.2},
    'CLASS_D': {'color': (1.0, 1.0, 0.0), 'extinguisher': 'dry_powder', 'spread_rate': 0.8}
}

# Game state variables
houses = []
fire_truck = {
    'position': [0, 0, 0],
    'rotation': 0,
    'spraying': False,
    'water': WATER_CAPACITY,
    'equipment': {
        'water_hose': {'condition': 100, 'effectiveness': 1.0},
        'foam_sprayer': {'condition': 100, 'effectiveness': 1.0},
        'dry_chemical': {'condition': 100, 'effectiveness': 1.0},
        'dry_powder': {'condition': 100, 'effectiveness': 1.0}
    }
}
score = 0
game_over = False
game_time = 0
last_time = 0
houses_saved = 0
game_started = False
water_stations = []  # Water refill stations
hazards = []  # Environmental hazards
smoke_particles = []  # Smoke particle system
fire_particles = []  # Fire particle system
wind_particles = []  # Wind visualization particles
last_fire_pop_time = 0  # Track the last time a fire popped up
fires_occurred = False  # Track if any fires have occurred during gameplay

# Add new camera-related variables
view_mode_fps = False  # False for third-person, True for first-person
cam_distance = 30.0  # Distance for third-person view
cam_elevation = 25.0  # Height for third-person view
cam_rotation = 0  # Camera rotation around the truck

def pop_random_fire():
    global fires_occurred
    # Find houses that are not on fire and not destroyed
    valid_houses = [h for h in houses if not h['on_fire'] and h['health'] > 0]
    
    if valid_houses:
        # Select a random house to set on fire
        house = random.choice(valid_houses)
        house['on_fire'] = True
        house['fire_intensity'] = 0.3  # Start with moderate intensity
        house['fire_type'] = random.choice(list(FIRE_TYPES.keys()))
        fires_occurred = True
        print(f"Fire started at house at position {house['position']}")

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_road():
    glDisable(GL_LIGHTING)
    # Main road (horizontal)
    glColor3f(0.3, 0.3, 0.3)  # Dark gray for road
    glBegin(GL_QUADS)
    glVertex3f(-ROAD_LENGTH, 0.01, -ROAD_WIDTH/2)
    glVertex3f(ROAD_LENGTH, 0.01, -ROAD_WIDTH/2)
    glVertex3f(ROAD_LENGTH, 0.01, ROAD_WIDTH/2)
    glVertex3f(-ROAD_LENGTH, 0.01, ROAD_WIDTH/2)
    glEnd()
    
    # Vertical road
    glBegin(GL_QUADS)
    glVertex3f(-ROAD_WIDTH/2, 0.01, -ROAD_LENGTH)
    glVertex3f(ROAD_WIDTH/2, 0.01, -ROAD_LENGTH)
    glVertex3f(ROAD_WIDTH/2, 0.01, ROAD_LENGTH)
    glVertex3f(-ROAD_WIDTH/2, 0.01, ROAD_LENGTH)
    glEnd()
    
    # Road markings
    glColor3f(1.0, 1.0, 1.0)  # White for road markings
    # Horizontal center line
    glBegin(GL_QUADS)
    glVertex3f(-ROAD_LENGTH, 0.02, -0.2)
    glVertex3f(ROAD_LENGTH, 0.02, -0.2)
    glVertex3f(ROAD_LENGTH, 0.02, 0.2)
    glVertex3f(-ROAD_LENGTH, 0.02, 0.2)
    glEnd()
    
    # Vertical center line
    glBegin(GL_QUADS)
    glVertex3f(-0.2, 0.02, -ROAD_LENGTH)
    glVertex3f(0.2, 0.02, -ROAD_LENGTH)
    glVertex3f(0.2, 0.02, ROAD_LENGTH)
    glVertex3f(-0.2, 0.02, ROAD_LENGTH)
    glEnd()
    
    glEnable(GL_LIGHTING)

def draw_water_extension_station(position):
    x, y, z = position
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Base platform
    glColor3f(0.2, 0.2, 0.2)  # Dark gray
    glPushMatrix()
    glScalef(6.0, 0.5, 6.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Water tank
    glColor3f(0.0, 0.5, 1.0)  # Light blue
    glPushMatrix()
    glTranslatef(0, 3.0, 0)
    glutSolidSphere(2.0, 16, 16)
    glPopMatrix()
    
    # Support structure
    glColor3f(0.7, 0.7, 0.7)  # Gray
    glPushMatrix()
    glTranslatef(0, 1.5, 0)
    glScalef(0.5, 3.0, 0.5)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Water hose connection
    glColor3f(0.3, 0.3, 0.3)  # Dark gray
    glPushMatrix()
    glTranslatef(2.0, 1.0, 0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.3, 1.0, 8, 8)
    glPopMatrix()
    
    # Refill zone indicator
    glDisable(GL_LIGHTING)
    glColor4f(0.0, 1.0, 0.0, 0.3)  # Semi-transparent green
    glPushMatrix()
    glTranslatef(0, 0.1, 0)
    glBegin(GL_QUADS)
    glVertex3f(-3.0, 0, -3.0)
    glVertex3f(3.0, 0, -3.0)
    glVertex3f(3.0, 0, 3.0)
    glVertex3f(-3.0, 0, 3.0)
    glEnd()
    glPopMatrix()
    glEnable(GL_LIGHTING)
    
    glPopMatrix()

def draw_shapes():
    # Draw the ground
    glDisable(GL_LIGHTING)
    glColor3f(0.3, 0.7, 0.3)  # Green ground
    
    # Draw ground plane
    glBegin(GL_QUADS)
    glVertex3f(-WORLD_SIZE, 0, -WORLD_SIZE)
    glVertex3f(WORLD_SIZE, 0, -WORLD_SIZE)
    glVertex3f(WORLD_SIZE, 0, WORLD_SIZE)
    glVertex3f(-WORLD_SIZE, 0, WORLD_SIZE)
    glEnd()
    
    # Draw roads
    draw_road()
    
    # Draw water stations
    for station in water_stations:
        draw_water_extension_station(station['position'])
    
    # Draw houses
    for house in houses:
        x, y, z = house['position']
        health = house['health']
        structural_integrity = house['structural_integrity']
        on_fire = house['on_fire']
        fire_intensity = house['fire_intensity']
        
        # Calculate health percentage for color
        health_pct = health / MAX_HEALTH
        structural_pct = structural_integrity / MAX_HEALTH
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Draw house body with structural damage visualization
        if on_fire:
            # House on fire is reddish
            glColor3f(min(1.0, 1.0 - health_pct + 0.5), health_pct * 0.5, health_pct * 0.3)
        else:
            if health_pct < 0.5:
                # Damaged house (not on fire) is gray/black
                glColor3f(health_pct * 0.5, health_pct * 0.5, health_pct * 0.5)
            else:
                # Normal house color based on health
                glColor3f(health_pct, health_pct, health_pct)
        
        # House body with deformation based on structural integrity
        glPushMatrix()
        # Apply deformation based on structural damage
        if structural_pct < 0.5:
            # Tilt the house as it becomes more damaged
            tilt_angle = (1 - structural_pct) * 15
            glRotatef(tilt_angle, 1, 0, 1)
        
        glScalef(4.0, 4.0 * structural_pct, 4.0)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Roof (pyramidal)
        glPushMatrix()
        glTranslatef(0, 3 * structural_pct, 0)
        glColor3f(0.7 * health_pct, 0.3 * health_pct, 0.3 * health_pct)  # Roof color
        
        glBegin(GL_TRIANGLES)
        # Front face of roof
        glVertex3f(0, 2, 0)  # Top point
        glVertex3f(-2, 0, -2)  # Bottom left
        glVertex3f(2, 0, -2)  # Bottom right
        
        # Back face of roof
        glVertex3f(0, 2, 0)  # Top point
        glVertex3f(-2, 0, 2)  # Bottom left
        glVertex3f(2, 0, 2)  # Bottom right
        
        # Left face of roof
        glVertex3f(0, 2, 0)  # Top point
        glVertex3f(-2, 0, -2)  # Bottom front
        glVertex3f(-2, 0, 2)  # Bottom back
        
        # Right face of roof
        glVertex3f(0, 2, 0)  # Top point
        glVertex3f(2, 0, -2)  # Bottom front
        glVertex3f(2, 0, 2)  # Bottom back
        glEnd()
        
        glPopMatrix()
        
        # Draw fire if house is on fire
        if on_fire:
            # Enhanced fire effect
            glDisable(GL_LIGHTING)
            glPointSize(8.0)  # Increased point size for better visibility
            glBegin(GL_POINTS)
            
            # More particles for better visibility
            num_particles = int(fire_intensity * 50) + 30  # Increased number of particles
            
            for i in range(num_particles):
                # Create a more dynamic fire effect
                x = fire_intensity * math.sin(time.time() * 3 + i) * 2
                y = random.uniform(0, fire_intensity * 3) + 3  # Higher flames
                z = fire_intensity * math.cos(time.time() * 3 + i) * 2
                
                # Fire color (yellow/orange/red)
                t = random.uniform(0, 1)
                if t < 0.3:
                    glColor3f(1.0, 1.0, 0.0)  # Yellow
                elif t < 0.7:
                    glColor3f(1.0, 0.5, 0.0)  # Orange
                else:
                    glColor3f(1.0, 0.0, 0.0)  # Red
                
                glVertex3f(x, y, z)
            
            glEnd()
            
            # Add some larger fire particles
            glPointSize(12.0)
            glBegin(GL_POINTS)
            for i in range(10):
                x = random.uniform(-2, 2)
                y = random.uniform(3, 6)
                z = random.uniform(-2, 2)
                glColor3f(1.0, random.uniform(0.3, 0.7), 0.0)
                glVertex3f(x, y, z)
            glEnd()
            
            glEnable(GL_LIGHTING)
        
        # Health bar above the house
        glTranslatef(0, 7, 0)
        
        # Background of health bar
        glColor3f(0.2, 0.2, 0.2)
        glPushMatrix()
        glScalef(4.0, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Health bar
        health_pct = health / MAX_HEALTH
        
        # Health bar color (green to red)
        if health_pct > 0.6:
            glColor3f(0.0, 1.0, 0.0)  # Green
        elif health_pct > 0.3:
            glColor3f(1.0, 1.0, 0.0)  # Yellow
        else:
            glColor3f(1.0, 0.0, 0.0)  # Red
        
        glPushMatrix()
        glTranslatef((health_pct - 1.0) * 2, 0, 0)  # Adjust position based on health
        glScalef(4.0 * health_pct, 0.25, 0.25)  # Adjust width based on health
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Structural integrity bar (below health bar)
        glTranslatef(0, -0.4, 0)
        
        # Background of structural bar
        glColor3f(0.2, 0.2, 0.2)
        glPushMatrix()
        glScalef(4.0, 0.3, 0.3)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Structural bar
        structural_pct = structural_integrity / MAX_HEALTH
        
        # Structural bar color (blue to purple)
        if structural_pct > 0.6:
            glColor3f(0.0, 0.5, 1.0)  # Blue
        elif structural_pct > 0.3:
            glColor3f(0.5, 0.0, 1.0)  # Purple
        else:
            glColor3f(1.0, 0.0, 0.5)  # Magenta
        
        glPushMatrix()
        glTranslatef((structural_pct - 1.0) * 2, 0, 0)  # Adjust position based on structural integrity
        glScalef(4.0 * structural_pct, 0.25, 0.25)  # Adjust width based on structural integrity
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPopMatrix()
    
    # Draw fire truck
    x, y, z = fire_truck['position']
    rotation = fire_truck['rotation']
    
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(rotation, 0, 1, 0)
    
    # Truck body
    glColor3f(1.0, 0.0, 0.0)  # Red truck
    glPushMatrix()
    glScalef(4.0, 2.0, 2.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Truck cabin
    glColor3f(0.8, 0.8, 0.8)  # Light gray
    glPushMatrix()
    glTranslatef(-1.0, 1.5, 0)
    glScalef(2.0, 1.0, 1.8)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Water tank
    glColor3f(0.0, 0.0, 0.7)  # Dark blue
    glPushMatrix()
    glTranslatef(1.0, 1.0, 0)
    glScalef(2.0, 1.0, 1.6)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Wheels
    glColor3f(0.2, 0.2, 0.2)  # Dark gray
    
    # Front left wheel
    glPushMatrix()
    glTranslatef(-1.5, -0.6, 1.2)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.4, 0.6, 8, 8)
    glPopMatrix()
    
    # Front right wheel
    glPushMatrix()
    glTranslatef(-1.5, -0.6, -1.2)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.4, 0.6, 8, 8)
    glPopMatrix()
    
    # Back left wheel
    glPushMatrix()
    glTranslatef(1.5, -0.6, 1.2)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.4, 0.6, 8, 8)
    glPopMatrix()
    
    # Back right wheel
    glPushMatrix()
    glTranslatef(1.5, -0.6, -1.2)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.4, 0.6, 8, 8)
    glPopMatrix()
    
    # Water cannon
    glColor3f(0.5, 0.5, 0.5)  # Gray
    glPushMatrix()
    glTranslatef(1.0, 2.0, 0)
    glRotatef(-30, 0, 0, 1)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.3, 2.0, 10, 5)
    glPopMatrix()
    
    # Nozzle tip - clearly visible
    glColor3f(0.3, 0.3, 0.3)  # Darker gray
    glPushMatrix()
    glTranslatef(1.0 + 1.73, 2.0 - 1.0, 0)  # Position at end of hose
    glRotatef(-30, 0, 0, 1)
    glRotatef(90, 0, 1, 0)
    glutSolidCone(0.4, 0.8, 10, 5)  # Conical nozzle
    glPopMatrix()
    
    # If the truck is spraying water, draw water spray
    if fire_truck['spraying'] and fire_truck['water'] > 0:
        # Draw water spray
        glDisable(GL_LIGHTING)
        glPointSize(4.0)  # Increased point size for better visibility
        glBegin(GL_POINTS)
        
        # Calculate water spray target (in front of the truck)
        angle_rad = math.radians(rotation)
        spray_start = [1.0 * math.sin(1), 1.5, 1.0 * math.cos(1)]
        spray_target = [SPRAY_DISTANCE * math.sin(1), 1.0, SPRAY_DISTANCE * math.cos(1)]
        
        # Direction vector
        direction = [
            spray_target[0] - spray_start[0],
            spray_target[1] - spray_start[1],
            spray_target[2] - spray_start[2]
        ]
        
        # Normalize direction
        length = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
        if length > 0:
            direction = [direction[0]/length, direction[1]/length, direction[2]/length]
        
        
        # Water particles
        particles = 100  # More particles for better visibility
        
        for i in range(particles):
            # Position along the spray path
            t = random.uniform(0, 1)
            x_p = spray_start[0] + direction[0] * SPRAY_DISTANCE * t
            y_p = spray_start[1] + direction[1] * SPRAY_DISTANCE * t - 0.5 * 9.8 * t**2  # Simple gravity arc
            z_p = spray_start[2] + direction[2] * SPRAY_DISTANCE * t
            
            # Small random offset for spray width
            x_p += random.uniform(-0.2, 0.2)
            y_p += random.uniform(-0.2, 0.2)
            z_p += random.uniform(-0.2, 0.2)
            
            # Water color (brighter blue)
            glColor3f(0.0, 0.7, 1.0)
            glVertex3f(x_p, y_p, z_p)
        
        glEnd()
        glEnable(GL_LIGHTING)
    
    # Water level indicator on the truck
    water_pct = fire_truck['water'] / WATER_CAPACITY
    
    glPushMatrix()
    glTranslatef(0, 3.0, 0)
    
    # Water level background
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glScalef(3.0, 0.3, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Water level foreground
    if water_pct > 0.6:
        glColor3f(0.0, 0.0, 1.0)  # Blue
    elif water_pct > 0.3:
        glColor3f(0.0, 0.5, 1.0)  # Light blue
    else:
        glColor3f(1.0, 0.0, 0.0)  # Red (low water)
    
    glPushMatrix()
    glTranslatef((water_pct - 1.0) * 1.5, 0, 0)  # Adjust position based on water level
    glScalef(3.0 * water_pct, 0.25, 0.25)  # Adjust width based on water level
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix()
    
    glPopMatrix()

def keyboardListener(key, x, y):
    global game_started, game_over, score, game_time, houses_saved, fire_truck
    global view_mode_fps, cam_rotation, cam_distance, cam_elevation, last_time
    
    if game_over:
        if key == b'r' or key == b'R':
            # Restart the game
            init_houses()
            init_water_stations()
            init_hazards()
            fire_truck['position'] = [0, 0, 0]
            fire_truck['rotation'] = 0
            fire_truck['spraying'] = False
            fire_truck['water'] = WATER_CAPACITY
            score = 0
            game_time = 0
            houses_saved = 0
            game_over = False
            game_started = False
    else:
        if key == b' ':  # Space bar
            if not game_started:
                game_started = True
                last_time = time.time()
                init_houses()
                init_water_stations()
                init_hazards()
            else:
                fire_truck['spraying'] = not fire_truck['spraying']
        elif key == b'v' or key == b'V':  # Toggle view mode
            view_mode_fps = not view_mode_fps
        elif key == b'\x1b':  # ESC key
            sys.exit()
    
    # Force screen update
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global fire_truck, cam_rotation, cam_distance, cam_elevation
    
    if game_started and not game_over:
        if not view_mode_fps:  # Third-person view controls
            if key == GLUT_KEY_UP:
                cam_elevation = max(10.0, cam_elevation - 2.0)
                cam_distance = max(20.0, cam_distance - 2.0)
            elif key == GLUT_KEY_DOWN:
                cam_elevation = min(50.0, cam_elevation + 2.0)
                cam_distance = min(60.0, cam_distance + 2.0)
            elif key == GLUT_KEY_LEFT:
                cam_rotation = (cam_rotation - 5) % 360
            elif key == GLUT_KEY_RIGHT:
                cam_rotation = (cam_rotation + 5) % 360
        
        # Movement controls (same for both views)
        if key == GLUT_KEY_UP:
            # Calculate movement based on current rotation
            angle_rad = math.radians(fire_truck['rotation'])
            # Move forward
            new_x = fire_truck['position'][0] + TRUCK_SPEED * math.sin(angle_rad)
            new_z = fire_truck['position'][2] + TRUCK_SPEED * math.cos(angle_rad)
            
            if not check_collision([new_x, 0, new_z]):
                print("up collision")
                fire_truck['position'][0] = new_x
                fire_truck['position'][2] = new_z
        
        elif key == GLUT_KEY_DOWN:
            
            # Calculate movement based on current rotation
            angle_rad = math.radians(fire_truck['rotation'])
            # Move backward
            new_x = fire_truck['position'][0] - TRUCK_SPEED * math.sin(angle_rad)
            new_z = fire_truck['position'][2] - TRUCK_SPEED * math.cos(angle_rad)
            
            if not check_collision([new_x, 0, new_z]):
                print("down collision")
                fire_truck['position'][0] = new_x
                fire_truck['position'][2] = new_z
        
        elif key == GLUT_KEY_LEFT:
            # Turn left
            fire_truck['rotation'] = (fire_truck['rotation'] + 5) % 360
        
        elif key == GLUT_KEY_RIGHT:
            # Turn right
            fire_truck['rotation'] = (fire_truck['rotation'] - 5) % 360
        
        glutPostRedisplay()

def mouseListener(button, state, x, y):
    pass

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Camera position based on fire truck
    x, y, z = fire_truck['position']
    rotation = fire_truck['rotation']
    
    if view_mode_fps:
        # First-person view - camera in driver's seat
        angle_rad = math.radians(rotation)
        eye_x = x + 2.0 * math.sin(angle_rad)  # Position in driver's seat
        eye_y = y + 1.5  # Eye level height
        eye_z = z + 2.0 * math.cos(angle_rad)
        
        # Look in the direction the truck is facing
        target_x = x + 10.0 * math.sin(angle_rad)
        target_y = eye_y  # Keep same height
        target_z = z + 10.0 * math.cos(angle_rad)
        
        gluLookAt(
            eye_x, eye_y, eye_z,  # Camera position
            target_x, target_y, target_z,  # Look at point
            0, 1, 0   # Up vector
        )
    else:
        # Third-person view - camera follows behind truck
        angle_rad = math.radians(rotation)
        
        # Calculate camera position behind the truck
        cam_x = x - cam_distance * math.sin(angle_rad)
        cam_y = y + cam_elevation
        cam_z = z - cam_distance * math.cos(angle_rad)
        
        gluLookAt(
            cam_x, cam_y, cam_z,  # Camera position
            x, y + 2.0, z,  # Look at truck
            0, 1, 0   # Up vector
        )

def idle():
    global game_time, last_time, houses_saved, game_over, fire_truck, last_fire_pop_time
    
    # Calculate delta time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    if not game_over and game_started:
        game_time += delta_time
        
        # Update wind
        update_wind()
        
        # Update fire spread and structural integrity
        update_fire_spread()
        update_structural_integrity()
        
        # Update particles
        update_particles()
        
        # Random fire popping with minimum interval
        if current_time - last_fire_pop_time >= FIRE_POP_INTERVAL:
            if random.random() < 0.1:  # 10% chance to start a new fire
                pop_random_fire()
                last_fire_pop_time = current_time
        
        # Update fire truck water level if spraying
        if fire_truck['spraying'] and fire_truck['water'] > 0:
            fire_truck['water'] = max(0, fire_truck['water'] - WATER_USAGE_RATE)
            
            # Check for houses in range to extinguish
            for house in houses:
                if house['on_fire']:
                    dx = house['position'][0] - fire_truck['position'][0]
                    dz = house['position'][2] - fire_truck['position'][2]
                    distance = math.sqrt(dx*dx + dz*dz)
                    
                    
                    if distance < SPRAY_DISTANCE:
                        # Calculate water spray direction
                        angle_rad = math.radians(fire_truck['rotation'])
                        spray_dir_x = math.sin(angle_rad)
                        spray_dir_z = math.cos(angle_rad)
                        # Check if water is aimed at the house
                        house_dir_x = dx / distance if distance > 0 else 0
                        house_dir_z = dz / distance if distance > 0 else 0
                        
                        # Calculate dot product to check if truck is facing the house
                        dot_product = house_dir_x * spray_dir_x + house_dir_z * spray_dir_z
                        
                        # If water is aimed at the house (dot product > 0.7 means angle < ~45 degrees)
                        if dot_product > 0.7:
                            # Check if we're using the correct extinguisher
                            current_equipment = 'water_hose'  # Default to water hose
                            if fire_truck['equipment'][current_equipment]['condition'] > 0:
                                # Reduce fire intensity more slowly
                                house['fire_intensity'] = max(0, house['fire_intensity'] - WATER_HEAL * delta_time * 0.5)
                                
                                # If fire is extinguished
                                if house['fire_intensity'] <= 0:
                                    house['on_fire'] = False
                                    house['fire_intensity'] = 0
                                    houses_saved += 1
                                
                                # Degrade equipment
                                fire_truck['equipment'][current_equipment]['condition'] -= 0.1
                                if fire_truck['equipment'][current_equipment]['condition'] <= 0:
                                    fire_truck['equipment'][current_equipment]['effectiveness'] = 0
        
        # Automatic water refill when near water stations
        for station in water_stations:
            dx = station['position'][0] - fire_truck['position'][0]
            dz = station['position'][2] - fire_truck['position'][2]
            distance = math.sqrt(dx*dx + dz*dz)
            
            if distance < WATER_REFILL_DISTANCE:
                fire_truck['water'] = WATER_CAPACITY  # Instantly refill to full
                break
        
        # Check for game over condition
        # Check for game over condition
        houses_on_fire = sum(1 for house in houses if house['on_fire'])
        houses_destroyed = sum(1 for house in houses if house['health'] <= 0)

    
        # Game over if more than 50% houses are burnt/destroyed
        if houses_destroyed > NUM_HOUSES / 2:
            game_over = True

    
    glutPostRedisplay()

def showScreen():
    global camera_pos
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Setup camera
    setupCamera()
    
    # Draw the scene
    draw_shapes()
    
    # Draw particles
    draw_particles()
    
    # Draw HUD
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw game stats
    draw_text(10, 780, f"Time: {int(game_time)}s")
    draw_text(10, 750, f"Houses Saved: {houses_saved}/{NUM_HOUSES}")
    draw_text(10, 720, f"Water: {int(fire_truck['water'])}/{WATER_CAPACITY}")
    
    # Draw wind indicator
    wind_text = f"Wind: {WIND_DIRECTION[0]:.1f}, {WIND_DIRECTION[2]:.1f} ({WIND_SPEED:.1f})"
    draw_text(10, 690, wind_text)
    
    # Draw equipment status
    y = 660
    for equipment, status in fire_truck['equipment'].items():
        draw_text(10, y, f"{equipment}: {int(status['condition'])}%")
        y -= 30
    
    # Draw controls
    draw_text(10, 100, "Controls:")
    draw_text(10, 80, "Arrow Keys: Move/Turn")
    draw_text(10, 60, "Space: Toggle water spray")
    draw_text(10, 40, "V: Toggle view mode (FPS/Third-person)")
    
    if not game_started:
        draw_text(400, 400, "Press SPACE to start the game", GLUT_BITMAP_TIMES_ROMAN_24)
    elif game_over:
        if houses_saved == NUM_HOUSES:
            draw_text(400, 400, "Victory! All houses saved!", GLUT_BITMAP_TIMES_ROMAN_24)
        else:
            draw_text(400, 400, "Game Over!", GLUT_BITMAP_TIMES_ROMAN_24)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

# Helper functions
def init_houses():
    global houses
    houses = []
    
    # House positions along the roads
    house_positions = [
        # Houses along horizontal road
        (-60, -15), (-40, -15), (-20, -15), (20, -15), (40, -15), (60, -15),  # Left side
        (-60, 15), (-40, 15), (-20, 15), (20, 15), (40, 15), (60, 15),  # Right side
        
        # Houses along vertical road
        (-15, -60), (-15, -40), (-15, -20), (-15, 20), (-15, 40), (-15, 60),  # Bottom side
        (15, -60), (15, -40), (15, -20), (15, 20), (15, 40), (15, 60),  # Top side
    ]
    
    # Select random positions for the initial houses
    selected_positions = random.sample(house_positions, NUM_HOUSES)
    
    for i, (x, z) in enumerate(selected_positions):
        # Random fire type for the house
        fire_type = random.choice(list(FIRE_TYPES.keys()))
        
        # Start with no houses on fire
        house = {
            'position': [x, 0, z],
            'health': MAX_HEALTH,
            'structural_integrity': MAX_HEALTH,
            'on_fire': False,  # Start with no houses on fire
            'fire_intensity': 0,
            'fire_type': fire_type,
            'smoke_level': 0,
            'flammability': random.uniform(0.5, 1.0),
            'fire_spread_timer': 0,
            'fire_spread_cooldown': random.uniform(1.0, 3.0),
            'collapse_risk': 0
        }
        houses.append(house)

def init_water_stations():
    global water_stations
    water_stations = []
    
    # Add water stations at intersections
    water_stations.append({'position': [0, 0, 0], 'capacity': WATER_CAPACITY})  # Center
    water_stations.append({'position': [WATER_STATION_DISTANCE, 0, WATER_STATION_DISTANCE], 'capacity': WATER_CAPACITY})  # Top right
    water_stations.append({'position': [-WATER_STATION_DISTANCE, 0, WATER_STATION_DISTANCE], 'capacity': WATER_CAPACITY})  # Top left
    water_stations.append({'position': [WATER_STATION_DISTANCE, 0, -WATER_STATION_DISTANCE], 'capacity': WATER_CAPACITY})  # Bottom right
    water_stations.append({'position': [-WATER_STATION_DISTANCE, 0, -WATER_STATION_DISTANCE], 'capacity': WATER_CAPACITY})  # Bottom left

def init_hazards():
    global hazards
    hazards = []
    
    # Add fallen trees, power lines, etc.
    for _ in range(5):
        x = random.randint(-WORLD_SIZE//2 + 5, WORLD_SIZE//2 - 5)
        z = random.randint(-WORLD_SIZE//2 + 5, WORLD_SIZE//2 - 5)
        hazard_type = random.randint(0, 2)  # 0: fallen tree, 1: power line, 2: debris
        hazards.append({'position': [x, 0, z], 'type': hazard_type, 'cleared': False})

def check_collision(new_pos):
    # Check collision with houses
    for house in houses:
        if house['health'] > 0:  # Only consider standing houses
            house_pos = house['position']
            dx = new_pos[0] - house_pos[0]
            dz = new_pos[2] - house_pos[2]
            distance = math.sqrt(dx**2 + dz**2)
            
            if distance < COLLISION_DISTANCE:
                return True
    
    
    # Check world boundaries
    if (abs(new_pos[0]) > WORLD_SIZE - 5 or 
        abs(new_pos[2]) > WORLD_SIZE - 5):
        return True
    
    return False

def create_fire_particle(position, fire_type):
    return {
        'position': list(position),
        'velocity': [
            random.uniform(-0.1, 0.1) + WIND_DIRECTION[0] * WIND_SPEED,
            random.uniform(0.1, 0.3),
            random.uniform(-0.1, 0.1) + WIND_DIRECTION[2] * WIND_SPEED
        ],
        'size': random.uniform(0.1, 0.3),
        'life': 1.0,
        'color': FIRE_TYPES[fire_type]['color'],
        'type': fire_type
    }

def create_smoke_particle(position):
    return {
        'position': list(position),
        'velocity': [
            random.uniform(-0.05, 0.05) + WIND_DIRECTION[0] * WIND_SPEED,
            random.uniform(0.05, 0.15),
            random.uniform(-0.05, 0.05) + WIND_DIRECTION[2] * WIND_SPEED
        ],
        'size': random.uniform(0.2, 0.4),
        'life': 1.0,
        'density': random.uniform(0.3, 0.7)
    }

def update_particles():
    global fire_particles, smoke_particles
    
    # Update fire particles
    new_fire_particles = []
    for particle in fire_particles:
        particle['life'] -= 0.02
        if particle['life'] > 0:
            # Update position
            for i in range(3):
                particle['position'][i] += particle['velocity'][i]
            new_fire_particles.append(particle)
    fire_particles = new_fire_particles
    
    # Update smoke particles
    new_smoke_particles = []
    for particle in smoke_particles:
        particle['life'] -= 0.01
        if particle['life'] > 0:
            # Update position
            for i in range(3):
                particle['position'][i] += particle['velocity'][i]
            # Update density
            particle['density'] -= SMOKE_DISSIPATION_RATE
            if particle['density'] > 0:
                new_smoke_particles.append(particle)
    smoke_particles = new_smoke_particles

def draw_particles():
    # Draw fire particles
    glDisable(GL_LIGHTING)
    for particle in fire_particles:
        glPushMatrix()
        glTranslatef(*particle['position'])
        
        # Set color with alpha based on life
        r, g, b = particle['color']
        glColor4f(r, g, b, particle['life'])
        
        # Draw particle as a billboard
        size = particle['size']
        glBegin(GL_QUADS)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)
        glEnd()
        
        glPopMatrix()
    
    # Draw smoke particles
    for particle in smoke_particles:
        glPushMatrix()
        glTranslatef(*particle['position'])
        
        # Set color with alpha based on life and density
        alpha = particle['life'] * particle['density']
        glColor4f(0.3, 0.3, 0.3, alpha)
        
        # Draw particle as a billboard
        size = particle['size']
        glBegin(GL_QUADS)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)
        glEnd()
        
        glPopMatrix()
    glEnable(GL_LIGHTING)

def update_wind():
    global WIND_DIRECTION, WIND_SPEED
    # Randomly change wind direction and speed
    if random.random() < 0.01:  # 1% chance per frame
        angle = random.uniform(-math.pi/4, math.pi/4)
        WIND_DIRECTION = [
            WIND_DIRECTION[0] * math.cos(angle) - WIND_DIRECTION[2] * math.sin(angle),
            0,
            WIND_DIRECTION[0] * math.sin(angle) + WIND_DIRECTION[2] * math.cos(angle)
        ]
        # Normalize direction
        length = math.sqrt(sum(x*x for x in WIND_DIRECTION))
        WIND_DIRECTION = [x/length for x in WIND_DIRECTION]
        
        # Randomly change wind speed
        WIND_SPEED = random.uniform(0.5, 2.0)

def update_fire_spread():
    global houses, fire_particles, smoke_particles
    
    for house in houses:
        if house['on_fire']:
            # Update fire intensity - make it grow over time
            house['fire_intensity'] = min(1.0, house['fire_intensity'] + 0.001)
            
            # Generate more fire and smoke particles
            if random.random() < 0.5:  # Increased chance for particles
                fire_particles.append(create_fire_particle(
                    [house['position'][0] + random.uniform(-2, 2),
                     house['position'][1] + random.uniform(2, 4),
                     house['position'][2] + random.uniform(-2, 2)],
                    house['fire_type']
                ))
            
            if random.random() < 0.3:  # Increased chance for smoke
                smoke_particles.append(create_smoke_particle(
                    [house['position'][0] + random.uniform(-2, 2),
                     house['position'][1] + random.uniform(3, 5),
                     house['position'][2] + random.uniform(-2, 2)]
                ))
            
            # Update smoke level
            house['smoke_level'] = min(MAX_SMOKE_DENSITY, house['smoke_level'] + 0.01)
            
            # Try to spread fire to nearby houses
            house['fire_spread_timer'] += 1
            if house['fire_spread_timer'] >= house['fire_spread_cooldown']:
                house['fire_spread_timer'] = 0
                
                for other_house in houses:
                    if other_house != house and not other_house['on_fire']:
                        # Calculate distance between houses
                        dx = other_house['position'][0] - house['position'][0]
                        dz = other_house['position'][2] - house['position'][2]
                        distance = math.sqrt(dx*dx + dz*dz)
                        
                        if distance < FIRE_SPREAD_RADIUS:
                            # Calculate spread probability based on distance, wind, and flammability
                            wind_factor = (dx * WIND_DIRECTION[0] + dz * WIND_DIRECTION[2]) / distance
                            spread_prob = (FIRE_SPREAD_PROBABILITY * 
                                         (1 - distance/FIRE_SPREAD_RADIUS) * 
                                         (1 + wind_factor) * 
                                         other_house['flammability'])
                            
                            if random.random() < spread_prob:
                                other_house['on_fire'] = True
                                other_house['fire_intensity'] = 0.1
                                other_house['fire_type'] = house['fire_type']

def update_structural_integrity():
    for house in houses:
        if house['on_fire']:
            # Reduce structural integrity based on fire intensity
            damage = FIRE_DAMAGE * house['fire_intensity']
            house['structural_integrity'] = max(0, house['structural_integrity'] - damage)
            
            # If structural integrity is too low, house collapses
            if house['structural_integrity'] < 20:
                house['health'] = 0
                house['on_fire'] = False
                house['fire_intensity'] = 0
                house['smoke_level'] = 0

def main():
    global last_time, last_fire_pop_time, fires_occurred
    
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Fire Fighter 3D")
    
    # Set up OpenGL
    glClearColor(0.53, 0.81, 0.92, 1.0)  # Sky blue background
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Set up light position
    glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 10.0, 10.0, 1.0])
    
    # Initialize game objects
    init_houses()
    init_water_stations()
    init_hazards()
    
    # Initialize timers and flags
    last_time = time.time()
    last_fire_pop_time = time.time()
    fires_occurred = False
    
    # Register callbacks
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    # Enable key repeat
    glutSetKeyRepeat(GLUT_KEY_REPEAT_ON)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
