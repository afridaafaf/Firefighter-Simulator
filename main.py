import sys
import random
import math
import time
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np

# Game parameters
NUM_HOUSES = 8  # Number of houses in the game
MAX_HEALTH = 100  # Maximum health of a house
FIRE_DAMAGE = 0.2  # Fire damage per frame
WATER_HEAL = 2.0  # Water healing per frame
SPRAY_DISTANCE = 5.0  # Maximum distance to spray water
FIRE_PROBABILITY = 0.0005  # Probability of fire starting in a house per frame
TRUCK_SPEED = 0.1  # Speed of the fire truck
WORLD_SIZE = 30  # Size of the game world

# Game state variables
houses = []
fire_truck = {'position': [0, 0, 0], 'rotation': 0, 'spraying': False}
score = 0
game_over = False
game_time = 0
last_time = 0
houses_saved = 0
game_started = False

# Initialize the window
def init():
    glClearColor(0.53, 0.81, 0.92, 1.0)  # Sky blue background
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Set up light position
    glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 10.0, 10.0, 1.0])
    
    # Initialize houses
    init_houses()

# Initialize houses in random positions
def init_houses():
    global houses
    houses = []
    house_positions = set()
    
    while len(houses) < NUM_HOUSES:
        # Generate grid-based positions for houses
        x = random.randint(-WORLD_SIZE//2 + 5, WORLD_SIZE//2 - 5)
        z = random.randint(-WORLD_SIZE//2 + 5, WORLD_SIZE//2 - 5)
        
        # Round to grid
        x = round(x / 5) * 5
        z = round(z / 5) * 5
        
        pos = (x, z)
        if pos not in house_positions:
            house_positions.add(pos)
            houses.append({
                'position': [x, 0, z],
                'health': MAX_HEALTH,
                'on_fire': False,
                'saved': False,
                'fire_time': 0
            })

# Draw a simple house
def draw_house(position, health, on_fire):
    x, y, z = position
    
    # Calculate health percentage for color
    health_pct = health / MAX_HEALTH
    
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Draw house body
    if on_fire:
        # House on fire is reddish
        glColor3f(min(1.0, 1.0 - health_pct + 0.5), health_pct * 0.5, health_pct * 0.3)
    else:
        # Normal house color based on health
        glColor3f(health_pct, health_pct, health_pct)
    
    # House body
    glPushMatrix()
    glScalef(2.0, 2.0, 2.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Roof (pyramidal)
    glPushMatrix()
    glTranslatef(0, 1.5, 0)
    glColor3f(0.7 * health_pct, 0.3 * health_pct, 0.3 * health_pct)  # Roof color
    glBegin(GL_TRIANGLES)
    
    # Front face of roof
    glVertex3f(0, 1, 0)    # Top point
    glVertex3f(-1, 0, -1)  # Bottom left
    glVertex3f(1, 0, -1)   # Bottom right
    
    # Back face of roof
    glVertex3f(0, 1, 0)    # Top point
    glVertex3f(-1, 0, 1)   # Bottom left
    glVertex3f(1, 0, 1)    # Bottom right
    
    # Left face of roof
    glVertex3f(0, 1, 0)    # Top point
    glVertex3f(-1, 0, -1)  # Bottom front
    glVertex3f(-1, 0, 1)   # Bottom back
    
    # Right face of roof
    glVertex3f(0, 1, 0)    # Top point
    glVertex3f(1, 0, -1)   # Bottom front
    glVertex3f(1, 0, 1)    # Bottom back
    
    glEnd()
    glPopMatrix()
    
    # Draw fire if house is on fire
    if on_fire:
        draw_fire()
    
    # Health bar above the house
    draw_health_bar(health)
    
    glPopMatrix()

# Draw fire particles
def draw_fire():
    glPushMatrix()
    glTranslatef(0, 2.5, 0)
    
    # Disable lighting for particles
    glDisable(GL_LIGHTING)
    
    # Draw fire particles
    glPointSize(3.0)
    glBegin(GL_POINTS)
    
    for i in range(20):
        x = 0.5 * math.sin(time.time() * 5 + i)
        y = random.uniform(0, 1.5)
        z = 0.5 * math.cos(time.time() * 5 + i)
        
        # Fire color (yellow/orange/red)
        t = random.uniform(0, 1)
        glColor3f(1.0, t * 0.7, 0)
        
        glVertex3f(x, y, z)
    
    glEnd()
    
    # Re-enable lighting
    glEnable(GL_LIGHTING)
    glPopMatrix()

# Draw water spray
def draw_water_spray(start_pos, target_pos):
    glPushMatrix()
    
    # Disable lighting for particles
    glDisable(GL_LIGHTING)
    
    # Draw water particles
    glPointSize(2.0)
    glBegin(GL_POINTS)
    
    # Direction vector
    direction = [target_pos[0] - start_pos[0], 
                 target_pos[1] - start_pos[1], 
                 target_pos[2] - start_pos[2]]
    
    # Normalize direction
    length = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
    if length > 0:
        direction = [direction[0]/length, direction[1]/length, direction[2]/length]
    
    for i in range(50):
        # Position along the spray path
        t = random.uniform(0, 1)
        x = start_pos[0] + direction[0] * SPRAY_DISTANCE * t
        y = start_pos[1] + direction[1] * SPRAY_DISTANCE * t - 0.5 * 9.8 * t**2  # Simple gravity arc
        z = start_pos[2] + direction[2] * SPRAY_DISTANCE * t
        
        # Small random offset for spray width
        x += random.uniform(-0.2, 0.2)
        y += random.uniform(-0.2, 0.2)
        z += random.uniform(-0.2, 0.2)
        
        # Water color (blue)
        glColor3f(0.0, 0.7, 1.0)
        
        glVertex3f(x, y, z)
    
    glEnd()
    
    # Re-enable lighting
    glEnable(GL_LIGHTING)
    glPopMatrix()

# Draw health bar above house
def draw_health_bar(health):
    glPushMatrix()
    glTranslatef(0, 3.5, 0)
    
    # Background of health bar
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glScalef(2.0, 0.2, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Colored health portion
    health_pct = health / MAX_HEALTH
    
    # Health bar color (green to red)
    if health_pct > 0.6:
        glColor3f(0.0, 1.0, 0.0)  # Green
    elif health_pct > 0.3:
        glColor3f(1.0, 1.0, 0.0)  # Yellow
    else:
        glColor3f(1.0, 0.0, 0.0)  # Red
    
    glPushMatrix()
    glTranslatef((health_pct - 1.0), 0, 0)  # Adjust position based on health
    glScalef(2.0 * health_pct, 0.15, 0.15)  # Adjust width based on health
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix()

# Draw the fire truck
def draw_fire_truck():
    x, y, z = fire_truck['position']
    rotation = fire_truck['rotation']
    
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(rotation, 0, 1, 0)
    
    # Truck body
    glColor3f(1.0, 0.0, 0.0)  # Red truck
    glPushMatrix()
    glScalef(2.0, 1.0, 1.0)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Truck cabin
    glColor3f(0.8, 0.8, 0.8)  # Light gray
    glPushMatrix()
    glTranslatef(-0.5, 0.75, 0)
    glScalef(1.0, 0.5, 0.9)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Water tank
    glColor3f(0.0, 0.0, 0.7)  # Dark blue
    glPushMatrix()
    glTranslatef(0.5, 0.5, 0)
    glScalef(1.0, 0.5, 0.8)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Wheels
    glColor3f(0.2, 0.2, 0.2)  # Dark gray
    
    # Front left wheel
    glPushMatrix()
    glTranslatef(-0.8, -0.3, 0.6)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.2, 0.3, 8, 8)
    glPopMatrix()
    
    # Front right wheel
    glPushMatrix()
    glTranslatef(-0.8, -0.3, -0.6)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.2, 0.3, 8, 8)
    glPopMatrix()
    
    # Back left wheel
    glPushMatrix()
    glTranslatef(0.8, -0.3, 0.6)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.2, 0.3, 8, 8)
    glPopMatrix()
    
    # Back right wheel
    glPushMatrix()
    glTranslatef(0.8, -0.3, -0.6)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(0.2, 0.3, 8, 8)
    glPopMatrix()
    
    # Water cannon
    glColor3f(0.5, 0.5, 0.5)  # Gray
    glPushMatrix()
    glTranslatef(0.5, 1.0, 0)
    glRotatef(-30, 0, 0, 1)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.15, 1.0, 10, 5)
    glPopMatrix()
    
    # If the truck is spraying water, draw water spray
    if fire_truck['spraying']:
        # Calculate water spray target (in front of the truck)
        angle_rad = math.radians(rotation)
        spray_start = [x + 0.5 * math.sin(angle_rad), 1.0, z + 0.5 * math.cos(angle_rad)]
        spray_target = [x + SPRAY_DISTANCE * math.sin(angle_rad), 
                       1.0, 
                       z + SPRAY_DISTANCE * math.cos(angle_rad)]
        
        draw_water_spray(spray_start, spray_target)
    
    glPopMatrix()

# Draw the ground
def draw_ground():
    glPushMatrix()
    
    # Draw a grid ground
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
    
    for i in range(-WORLD_SIZE, WORLD_SIZE + 1, 5):
        glVertex3f(i, 0.01, -WORLD_SIZE)
        glVertex3f(i, 0.01, WORLD_SIZE)
        
        glVertex3f(-WORLD_SIZE, 0.01, i)
        glVertex3f(WORLD_SIZE, 0.01, i)
    
    glEnd()
    
    glEnable(GL_LIGHTING)
    glPopMatrix()

# Draw game info (score, houses saved)
def draw_game_info():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Set up orthographic projection for 2D text
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 600)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw score and houses saved
    glColor3f(1.0, 1.0, 1.0)
    
    if game_over:
        draw_text(300, 300, f"GAME OVER!")
        draw_text(300, 270, f"Final Score: {score}")
        draw_text(300, 240, f"Houses Saved: {houses_saved}/{NUM_HOUSES}")
        draw_text(300, 210, f"Press 'R' to restart")
    else:
        if not game_started:
            draw_text(300, 300, f"Press SPACE to start the game")
            draw_text(300, 270, f"Arrow keys to move, SPACE to spray water")
        else:
            draw_text(10, 580, f"Score: {score}")
            draw_text(10, 560, f"Houses Saved: {houses_saved}/{NUM_HOUSES}")
            draw_text(10, 540, f"Time: {int(game_time)} seconds")
    
    # Restore projection
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

# Render text using GLUT bitmap font
def draw_text(x, y, text):
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

# Main display function
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Set up the camera
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 800/600, 0.1, 100.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Camera follows the fire truck from behind and above
    x, y, z = fire_truck['position']
    rotation = fire_truck['rotation']
    
    # Calculate camera position (behind and above the truck)
    angle_rad = math.radians(rotation)
    camera_x = x - 10 * math.sin(angle_rad)
    camera_z = z - 10 * math.cos(angle_rad)
    
    gluLookAt(camera_x, 8, camera_z,  # Camera position
              x, 0, z,                # Look at point
              0, 1, 0)                # Up vector
    
    # Draw the ground
    draw_ground()
    
    # Draw all houses
    for house in houses:
        if house['health'] > 0:  # Only draw houses that are still standing
            draw_house(house['position'], house['health'], house['on_fire'])
    
    # Draw the fire truck
    draw_fire_truck()
    
    # Draw game info
    draw_game_info()
    
    glutSwapBuffers()

# Update game state
def update(value):
    global game_over, score, last_time, game_time, houses_saved, game_started
    
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    if game_started and not game_over:
        game_time += delta_time
        
        # Update houses - start fires, update health
        houses_alive = 0
        houses_burning = 0
        
        for house in houses:
            if house['health'] <= 0:
                continue
                
            houses_alive += 1
                
            # Check if house is on fire
            if house['on_fire']:
                houses_burning += 1
                
                # Decrease health for burning houses
                house['health'] -= FIRE_DAMAGE * delta_time * 60
                
                # Check if house is destroyed
                if house['health'] <= 0:
                    house['health'] = 0
                    house['on_fire'] = False
                    
                # Check if the truck is close enough and spraying water
                if fire_truck['spraying']:
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
                        # Heal the house
                        house['health'] += WATER_HEAL * delta_time * 60
                        
                        # Cap health at max
                        if house['health'] > MAX_HEALTH:
                            house['health'] = MAX_HEALTH
                            
                            # If house is fully healed, mark as saved if it was on fire
                            if house['on_fire'] and not house['saved']:
                                house['saved'] = True
                                house['on_fire'] = False
                                houses_saved += 1
                                score += 100  # Score for saving a house
            else:
                # Randomly start fires in houses that aren't burning
                if random.random() < FIRE_PROBABILITY * delta_time * 60:
                    house['on_fire'] = True
                    house['fire_time'] = game_time
        
        # Game over if all houses are destroyed
        if houses_alive == 0:
            game_over = True
        
        # Add points for each second of play
        score += int(delta_time * 1)
        
        # Bonus score for saving houses
        score += houses_saved * 5 * delta_time
    
    glutPostRedisplay()
    glutTimerFunc(16, update, 0)  # ~60 FPS

# Handle keyboard input
def keyboard(key, x, y):
    global game_started, game_over, score, game_time, houses_saved
    
    if game_over:
        if key == b'r' or key == b'R':
            # Restart the game
            init_houses()
            fire_truck['position'] = [0, 0, 0]
            fire_truck['rotation'] = 0
            fire_truck['spraying'] = False
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
            else:
                fire_truck['spraying'] = not fire_truck['spraying']
        elif key == b'\x1b':  # ESC key
            sys.exit()

# Handle special keys (arrow keys)
def special_keys(key, x, y):
    if game_started and not game_over:
        if key == GLUT_KEY_UP:
            # Move forward
            angle_rad = math.radians(fire_truck['rotation'])
            fire_truck['position'][0] += TRUCK_SPEED * math.sin(angle_rad)
            fire_truck['position'][2] += TRUCK_SPEED * math.cos(angle_rad)
        elif key == GLUT_KEY_DOWN:
            # Move backward
            angle_rad = math.radians(fire_truck['rotation'])
            fire_truck['position'][0] -= TRUCK_SPEED * math.sin(angle_rad)
            fire_truck['position'][2] -= TRUCK_SPEED * math.cos(angle_rad)
        elif key == GLUT_KEY_LEFT:
            # Turn left
            fire_truck['rotation'] = (fire_truck['rotation'] - 2) % 360
        elif key == GLUT_KEY_RIGHT:
            # Turn right
            fire_truck['rotation'] = (fire_truck['rotation'] + 2) % 360
        
        # Keep the truck within the world boundaries
        fire_truck['position'][0] = max(min(fire_truck['position'][0], WORLD_SIZE - 2), -WORLD_SIZE + 2)
        fire_truck['position'][2] = max(min(fire_truck['position'][2], WORLD_SIZE - 2), -WORLD_SIZE + 2)

# Main function
def main():
    global last_time
    
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Fire Fighter 3D")
    
    init()
    
    glutDisplayFunc(display)
    glutTimerFunc(16, update, 0)  # ~60 FPS
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    
    last_time = time.time()
    
    glutMainLoop()

if __name__ == "__main__":
    main()