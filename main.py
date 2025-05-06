from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time
import sys

# Camera-related variables
camera_pos = (0, 20, 30)
fovY = 60  # Field of view
GRID_LENGTH = 100  # Length of grid lines

# Game parameters
NUM_HOUSES = 8  # Number of houses in the game
MAX_HEALTH = 100  # Maximum health of a house
FIRE_DAMAGE = 0.2  # Fire damage per frame
WATER_HEAL = 2.0  # Water healing per frame
SPRAY_DISTANCE = 15.0  # Maximum distance to spray water
FIRE_PROBABILITY = 0.001  # Increased for more frequent fires
TRUCK_SPEED = 1.0  # Increased speed of the fire truck
WORLD_SIZE = 100  # Size of the game world
WATER_CAPACITY = 1000  # Maximum water capacity
WATER_USAGE_RATE = 2  # Water usage per frame when spraying
WATER_REFILL_RATE = 20  # Increased for faster refilling
COLLISION_DISTANCE = 6.0  # Distance for collision detection

# Game state variables
houses = []
fire_truck = {'position': [0, 0, 0], 'rotation': 0, 'spraying': False, 'water': WATER_CAPACITY}
score = 0
game_over = False
game_time = 0
last_time = 0
houses_saved = 0
game_started = False
water_stations = []  # Water refill stations
hazards = []  # Environmental hazards

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
    
    # Draw grid lines
    glColor3f(0.4, 0.4, 0.4)
    glBegin(GL_LINES)
    for i in range(-WORLD_SIZE, WORLD_SIZE + 1, 10):
        glVertex3f(i, 0.01, -WORLD_SIZE)
        glVertex3f(i, 0.01, WORLD_SIZE)
        glVertex3f(-WORLD_SIZE, 0.01, i)
        glVertex3f(WORLD_SIZE, 0.01, i)
    glEnd()
    glEnable(GL_LIGHTING)
    
    # Draw water stations
    for station in water_stations:
        x, y, z = station['position']
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Base of the water station
        glColor3f(0.0, 0.3, 0.8)  # Blue
        glPushMatrix()
        glScalef(3.0, 1.0, 3.0)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Water tower
        glColor3f(0.0, 0.5, 1.0)  # Light blue
        glPushMatrix()
        glTranslatef(0, 3.0, 0)
        glutSolidSphere(1.5, 12, 12)
        glPopMatrix()
        
        # Tower support
        glColor3f(0.7, 0.7, 0.7)  # Gray
        glPushMatrix()
        glTranslatef(0, 1.5, 0)
        glScalef(0.5, 2.0, 0.5)
        glutSolidCube(1.0)
        glPopMatrix()
        
        glPopMatrix()
    
    # Draw hazards
    for hazard in hazards:
        if hazard['cleared']:
            continue
            
        x, y, z = hazard['position']
        hazard_type = hazard['type']
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        if hazard_type == 0:  # Fallen tree
            # Tree trunk
            glColor3f(0.5, 0.3, 0.0)  # Brown
            glPushMatrix()
            glRotatef(90, 0, 0, 1)  # Lay the tree down
            glutSolidCylinder(1.0, 8.0, 10, 5)
            glPopMatrix()
            
            # Tree foliage
            glColor3f(0.2, 0.5, 0.1)  # Green
            glPushMatrix()
            glTranslatef(4.0, 0, 0)  # Position at one end of trunk
            glutSolidSphere(2.0, 10, 10)
            glPopMatrix()
        
        elif hazard_type == 1:  # Power line
            # Pole 1
            glColor3f(0.3, 0.3, 0.3)  # Dark gray
            glPushMatrix()
            glTranslatef(-3.0, 2.0, 0)
            glScalef(0.5, 4.0, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()
            
            # Pole 2
            glPushMatrix()
            glTranslatef(3.0, 2.0, 0)
            glScalef(0.5, 4.0, 0.5)
            glutSolidCube(1.0)
            glPopMatrix()
        
        else:  # Debris
            # Random debris pile
            glColor3f(0.5, 0.5, 0.5)  # Gray
            for i in range(5):
                glPushMatrix()
                glTranslatef(random.uniform(-1.5, 1.5), random.uniform(0, 1.0), random.uniform(-1.5, 1.5))
                glRotatef(random.uniform(0, 360), random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
                glScalef(random.uniform(0.5, 1.5), random.uniform(0.2, 0.8), random.uniform(0.5, 1.5))
                glutSolidCube(1.0)
                glPopMatrix()
        
        # Warning sign
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.8, 0.0)  # Yellow
        glPushMatrix()
        glTranslatef(0, 5.0, 0)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 1.0, 0)
        glVertex3f(-0.8, -0.5, 0)
        glVertex3f(0.8, -0.5, 0)
        glEnd()
        glPopMatrix()
        glEnable(GL_LIGHTING)
        
        glPopMatrix()
    
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
            # Fire effect - enhanced with larger particles
            glDisable(GL_LIGHTING)
            glPointSize(5.0)  # Increased for better visibility
            glBegin(GL_POINTS)
            
            # More particles for better visibility
            num_particles = int(fire_intensity / 3) + 20
            
            for i in range(num_particles):
                x = fire_intensity/40 * math.sin(time.time() * 5 + i)
                y = random.uniform(0, fire_intensity/20) + 5  # Higher flames
                z = fire_intensity/40 * math.cos(time.time() * 5 + i)
                
                # Fire color (yellow/orange/red)
                t = random.uniform(0, 1)
                glColor3f(1.0, t * 0.7, 0)
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
        spray_start = [2.8 * math.sin(angle_rad), 1.5, 2.8 * math.cos(angle_rad)]
        spray_target = [SPRAY_DISTANCE * math.sin(angle_rad), 1.0, SPRAY_DISTANCE * math.cos(angle_rad)]
        
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
    global game_started, game_over, score, game_time, houses_saved
    
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
        elif key == b'\x1b':  # ESC key
            sys.exit()

def specialKeyListener(key, x, y):
    if game_started and not game_over:
        if key == GLUT_KEY_UP:
            # Calculate new position for forward movement
            angle_rad = math.radians(fire_truck['rotation'])
            new_x = fire_truck['position'][0] + TRUCK_SPEED * math.sin(angle_rad)
            new_z = fire_truck['position'][2] + TRUCK_SPEED * math.cos(angle_rad)
            
            # Check for collision before moving
            if not check_collision([new_x, 0, new_z]):
                fire_truck['position'][0] = new_x
                fire_truck['position'][2] = new_z
        
        elif key == GLUT_KEY_DOWN:
            # Calculate new position for backward movement
            angle_rad = math.radians(fire_truck['rotation'])
            new_x = fire_truck['position'][0] - TRUCK_SPEED * math.sin(angle_rad)
            new_z = fire_truck['position'][2] - TRUCK_SPEED * math.cos(angle_rad)
            
            # Check for collision before moving
            if not check_collision([new_x, 0, new_z]):
                fire_truck['position'][0] = new_x
                fire_truck['position'][2] = new_z
        
        elif key == GLUT_KEY_LEFT:
            # Turn left
            fire_truck['rotation'] = (fire_truck['rotation'] - 2) % 360
        
        elif key == GLUT_KEY_RIGHT:
            # Turn right
            fire_truck['rotation'] = (fire_truck['rotation'] + 2) % 360

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
    
    # Calculate camera position (behind and above the truck)
    angle_rad = math.radians(rotation)
    camera_x = x - 20 * math.sin(angle_rad)
    camera_y = 15  # Height
    camera_z = z - 20 * math.cos(angle_rad)
    
    gluLookAt(
        camera_x, camera_y, camera_z,  # Camera position
        x, 0, z,  # Look at point (truck position)
        0, 1, 0   # Up vector
    )

def idle():
    global game_over, score, last_time, game_time, houses_saved, game_started
    
    current_time = time.time()
    if last_time == 0:
        last_time = current_time
        return
    
    delta_time = current_time - last_time
    last_time = current_time
    
    if game_started and not game_over:
        game_time += delta_time
        
        # Update houses - start fires, update health, structural integrity
        houses_alive = 0
        houses_burning = 0
        damaged_houses = 0
        
        for house in houses:
            if house['health'] <= 0:
                damaged_houses += 1
                continue
            
            houses_alive += 1
            
            # Check if house is on fire
            if house['on_fire']:
                houses_burning += 1
                
                # Increase fire intensity over time
                house['fire_intensity'] = min(100, house['fire_intensity'] + delta_time * 5)
                
                # Decrease health for burning houses
                fire_damage_rate = FIRE_DAMAGE * (1 + house['fire_intensity'] * 0.02)
                house['health'] -= fire_damage_rate * delta_time * 60
                
                # Decrease structural integrity based on fire intensity and duration
                structural_damage_rate = FIRE_DAMAGE * 0.5 * (1 + house['fire_intensity'] * 0.01)
                house['structural_integrity'] -= structural_damage_rate * delta_time * 60
                
                # Update collapse risk
                house['collapse_risk'] = 100 - house['structural_integrity']
                
                # Check if house is destroyed
                if house['health'] <= 0:
                    house['health'] = 0
                    house['on_fire'] = False
                    damaged_houses += 1
                
                # Check if house has collapsed
                if house['structural_integrity'] <= 0:
                    house['structural_integrity'] = 0
                    house['health'] = 0
                    house['on_fire'] = False
                    damaged_houses += 1
                
                # Check if the truck is close enough and spraying water
                if fire_truck['spraying'] and fire_truck['water'] > 0:
                    # Calculate distance to the house
                    house_pos = house['position']
                    truck_pos = fire_truck['position']
                    dx = house_pos[0] - truck_pos[0]
                    dz = house_pos[2] - truck_pos[2]
                    distance = math.sqrt(dx**2 + dz**2)
                    
                    # Calculate angle to the house
                    angle_to_house = math.degrees(math.atan2(dx, dz))
                    truck_angle = fire_truck['rotation']
                    
                    # Normalize the angle difference to [-180, 180]
                    angle_diff = (angle_to_house - truck_angle) % 360
                    if angle_diff > 180:
                        angle_diff -= 360
                    
                    # Check if house is within spray range and angle
                    if distance <= SPRAY_DISTANCE and abs(angle_diff) < 30:
                        # Reduce fire intensity
                        house['fire_intensity'] = max(0, house['fire_intensity'] - delta_time * 20)
                        
                        # Heal the house
                        house['health'] += WATER_HEAL * delta_time * 60
                        
                        # Cap health at max
                        if house['health'] > MAX_HEALTH:
                            house['health'] = MAX_HEALTH
                        
                        # If fire intensity is low enough, extinguish the fire
                        if house['fire_intensity'] < 10:
                            if house['on_fire'] and not house['saved']:
                                house['saved'] = True
                                house['on_fire'] = False
                                houses_saved += 1
                                score += 100  # Fixed score for saving a house
            else:
                # Randomly start fires in houses that aren't burning
                fire_prob = FIRE_PROBABILITY * delta_time * 60
                
                if random.random() < fire_prob:
                    house['on_fire'] = True
                    house['fire_intensity'] = 10  # Start with low intensity
                    house['fire_time'] = game_time
            
            # Fire can spread between houses based on proximity
            if house['on_fire'] and house['fire_intensity'] > 50:
                for other_house in houses:
                    if other_house != house and not other_house['on_fire'] and other_house['health'] > 0:
                        # Calculate distance between houses
                        dx = other_house['position'][0] - house['position'][0]
                        dz = other_house['position'][2] - house['position'][2]
                        distance = math.sqrt(dx**2 + dz**2)
                        
                        # Chance of fire spreading based on distance and fire intensity
                        spread_chance = (house['fire_intensity'] / 100) / (distance / 10)
                        
                        if distance < 20 and random.random() < spread_chance * delta_time:
                            other_house['on_fire'] = True
                            other_house['fire_intensity'] = 10  # Start with low intensity
                            other_house['fire_time'] = game_time
        
        # Update fire truck water level
        if fire_truck['spraying'] and fire_truck['water'] > 0:
            fire_truck['water'] -= WATER_USAGE_RATE * delta_time * 60
            if fire_truck['water'] < 0:
                fire_truck['water'] = 0
                fire_truck['spraying'] = False  # Stop spraying when out of water
        
        # Check if truck is at a water station for refill
        for station in water_stations:
            station_pos = station['position']
            truck_pos = fire_truck['position']
            dx = station_pos[0] - truck_pos[0]
            dz = station_pos[2] - truck_pos[2]
            distance = math.sqrt(dx**2 + dz**2)
            
            if distance < 10:  # Increased refill radius
                fire_truck['water'] += WATER_REFILL_RATE * delta_time * 60
                if fire_truck['water'] > WATER_CAPACITY:
                    fire_truck['water'] = WATER_CAPACITY
        
        # Game over conditions:
        # 1. If all houses are destroyed
        # 2. If more than 50% of houses are damaged
        if houses_alive == 0 or damaged_houses > NUM_HOUSES / 2:
            game_over = True
    
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    setupCamera()
    
    # Draw all game elements
    draw_shapes()
    
    # Draw game info
    if game_over:
        draw_text(400, 400, f"GAME OVER!")
        draw_text(400, 370, f"Final Score: {int(score)}")
        draw_text(400, 340, f"Houses Saved: {houses_saved}/{NUM_HOUSES}")
        draw_text(400, 310, f"Time Survived: {int(game_time)} seconds")
        draw_text(400, 280, f"Press 'R' to restart")
    else:
        if not game_started:
            draw_text(350, 400, f"FIRE FIGHTER 3D")
            draw_text(350, 370, f"Press SPACE to start the game")
            draw_text(350, 340, f"Arrow keys to move, SPACE to spray water")
            draw_text(350, 280, f"Visit water stations (blue towers) to refill water")
        else:
            draw_text(10, 780, f"Score: {int(score)}")
            draw_text(10, 760, f"Houses Saved: {houses_saved}/{NUM_HOUSES}")
            draw_text(10, 740, f"Time: {int(game_time)} seconds")
            draw_text(10, 720, f"Water: {int(fire_truck['water'])}/{WATER_CAPACITY}")
            
            # Show refill notification
            for station in water_stations:
                station_pos = station['position']
                truck_pos = fire_truck['position']
                dx = station_pos[0] - truck_pos[0]
                dz = station_pos[2] - truck_pos[2]
                distance = math.sqrt(dx**2 + dz**2)
                
                if distance < 10:  # Match the same distance as in idle()
                    draw_text(400, 740, "REFILLING WATER...", GLUT_BITMAP_HELVETICA_18)
                    break
            
            # Show warning for low water
            if fire_truck['water'] < WATER_CAPACITY * 0.2:
                draw_text(400, 780, f"LOW WATER WARNING! Find a water station to refill!")
    
    glutSwapBuffers()

# Helper functions
def init_houses():
    global houses
    houses = []
    house_positions = set()
    
    while len(houses) < NUM_HOUSES:
        # Generate grid-based positions for houses
        x = random.randint(-WORLD_SIZE//2 + 10, WORLD_SIZE//2 - 10)
        z = random.randint(-WORLD_SIZE//2 + 10, WORLD_SIZE//2 - 10)
        
        # Round to grid
        x = round(x / 10) * 10
        z = round(z / 10) * 10
        
        pos = (x, z)
        if pos not in house_positions:
            house_positions.add(pos)
            houses.append({
                'position': [x, 0, z],
                'health': MAX_HEALTH,
                'structural_integrity': MAX_HEALTH,
                'on_fire': False,
                'saved': False,
                'fire_time': 0,
                'fire_intensity': 0,  # 0-100 scale
                'fire_type': random.randint(0, 3),  # 0: Class A, 1: Class B, 2: Class C, 3: Class D
                'collapse_risk': 0  # 0-100 scale
            })

def init_water_stations():
    global water_stations
    water_stations = []
    
    # Add water stations at strategic locations
    water_stations.append({'position': [WORLD_SIZE//4, 0, WORLD_SIZE//4], 'capacity': WATER_CAPACITY})
    water_stations.append({'position': [-WORLD_SIZE//4, 0, -WORLD_SIZE//4], 'capacity': WATER_CAPACITY})
    water_stations.append({'position': [WORLD_SIZE//4, 0, -WORLD_SIZE//4], 'capacity': WATER_CAPACITY})
    water_stations.append({'position': [-WORLD_SIZE//4, 0, WORLD_SIZE//4], 'capacity': WATER_CAPACITY})

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
    
    # Check collision with hazards
    for hazard in hazards:
        if not hazard['cleared']:
            hazard_pos = hazard['position']
            dx = new_pos[0] - hazard_pos[0]
            dz = new_pos[2] - hazard_pos[2]
            distance = math.sqrt(dx**2 + dz**2)
            
            if distance < COLLISION_DISTANCE:
                return True
    
    # Check world boundaries
    if (abs(new_pos[0]) > WORLD_SIZE - 5 or 
        abs(new_pos[2]) > WORLD_SIZE - 5):
        return True
    
    return False

def main():
    global last_time
    
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
    
    # Register callbacks
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    last_time = time.time()
    
    glutMainLoop()

if __name__ == "__main__":
    main()
