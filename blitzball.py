import pygame, sys, random, sqlite3

pygame.init() # Initiate pygame

# Width and height of display window
width = 1200
height = 800
screen = pygame.display.set_mode((width, height)) # Create display surface
clock = pygame.time.Clock() # Create game clock
pygame.display.set_caption("Blitzball") # Caption of window

# Connect to database of usernames, scores, etc
conn = sqlite3.connect('blitz_scores.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS highscores (
    username TEXT,
    hrs INTEGER,
    max_distance INTEGER )''')
conn.commit()

# Background soundtrack -- Made by me!
pygame.mixer.music.load("Blitzball Theme RE.aif")
pygame.mixer.music.set_volume(0.4)
pygame.mixer.music.play(loops=-1)

# Sound effects
crack = pygame.mixer.Sound("Bat Crack.mp3")
pitch_sound = pygame.mixer.Sound("Pitch Sound.mp3")
charge = pygame.mixer.Sound("Blitzball Charge Sound 2.mp3")

# Colors, etc
RED = (255, 0, 0)
LRED = (255, 69, 61)
DRED = (194, 59, 34)
WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
LGREEN = (144, 238, 144)
LBLUE = (144, 144, 238)
YELLOW = (255, 255, 40)

# Parameters representing the strike zone
swidth = 150
sheight = 200
midtopx = width / 2
midtopy = int(height * 3 / 7)
slinewidth = 3
strike_zone_color = WHITE

# Create strike zone rectangle object, set position
strike_zone = pygame.Rect((0, 0, swidth, sheight))
strike_zone.midtop = (midtopx, midtopy)

# Bat and contact coefficients
ideal_contact_point = 0.9
contact_radius = 0.2
bat_width = 150
bat_height = 20

# Parameters dealing with the colors of different elements of the game
BACKGROUND = LGREEN
TARG = LRED #LGREEN
ALT_BACKGROUND = TARG
TEXT_COLOR = WHITE
LEAD_COLOR = LBLUE #LRED
LOAD_COLOR = WHITE
LEAD_HIGHLIGHT_TEXT = YELLOW

# Ball color and size
ball_color = BLACK
ball_size = 12

# Parameters dealing with the color fade animation when a ball is hit well
anim_interval = 10 # Looks good with 5 or with 200
num_intervals = 80 # 2 # number of maximum color shifts possible

r_step = (TARG[0] - BACKGROUND[0]) / num_intervals
g_step = (TARG[1] - BACKGROUND[1]) / num_intervals
b_step = (TARG[2] - BACKGROUND[2]) / num_intervals

# Parameters defining duration, distance of a hit
base = 100
modifier = 1000
pow = 1 / 2

def hit_dur(dist): # Duration of hit as a function of dist to barrel
    return base + modifier * (1 - power(dist)) ** (pow)

# Score function for a given hit
max_dist = ((bat_width / 2) ** 2 + (bat_height / 2) ** 2) ** (1/2)

def power(dist):
    # Gives number from 0 to 1, where 0 is low power, 1 is higher power
    return (max_dist - dist) / max_dist

# Functions to help generate parameters for a random pitch
wbuffer = 50 # Buffer for the width of the game
hbuffer = 50 # Buffer for the height of the game

def rand_node():
    # return width // 2, height // 2 # BP mode
    return random.randint(wbuffer, width - wbuffer), random.randint(hbuffer, height - hbuffer)

def rand_strike():
    # return width // 2, height // 2 + 50 # BP mode
    return random.randint(midtopx - swidth / 2, midtopx + swidth / 2), random.randint(midtopy, midtopy + sheight)

# Ms between test pitches (determines speed), buffer
duration = 1000
buffer = 1000

# Import pitcher sprites
pitcher1 = pygame.image.load("Pitcher 2.png")
pitcher1 = pygame.transform.scale(pitcher1, (150, 150))
pitcher2 = pygame.image.load("Pitcher.png")
pitcher2 = pygame.transform.scale(pitcher2, (150, 150))
pitcher1_rect = pitcher1.get_rect(center = (width // 2, height // 4))
pitcher2_rect = pitcher2.get_rect(center = (width // 2, height // 4))

# Import batter sprite
bat = pygame.image.load("Bat.png")
bat = pygame.transform.scale(bat, (bat_width + 4 + 10, bat_height * 8 + 10))

# Position that the ball is thrown from
pitcher_x = width / 2 - 45
pitcher_y = 175

# Initialize control points - not strictly necessary but helps for clarity
control_points = [(pitcher_x, pitcher_y), rand_node(), rand_strike()]

# Function to get current ball position given curve parameters; here 0 < t < 1
def ball_pos(t, control_points = control_points):
    # First, we find the points that are t of the way between each ctrl point
    a = [x * (1-t) + y * t for x, y in zip(control_points[0], control_points[1])]
    b = [x * (1-t) + y * t for x, y in zip(control_points[1], control_points[2])]

    # Then, we find the point t of the way between them - this is a Bezier curve
    ball = [x * (1-t) + y * t for x, y in zip(a, b)]
    return ball

# Function to adjust the speeding up/slowing down of pitched by adjusting t
# Here, -1 < j < 1, and this determines if the pitch speeds up or slows down (j = 1 - slows most)
def tweak(t, j):
    k = j / 2
    return (t - k * t ** 2) / (1 - k)

# Functions computing distance and type of a given hit - power is between 0 and 1
def hit_distance(power):
    pow = power ** 3 # Adjusted coefficient between 0 and 1
    return int(600 * pow)

def hit_type(hit_distance):
    luck = random.uniform(0,1)
    offset = random.randint(-25, 25)
    if hit_distance + offset < 100:
        if luck < 0.5:
            return "INFIELD FLY"
        return "GROUNDOUT"
    if hit_distance + offset < 200:
        if luck < 0.75:
            return "POPOUT"
        return "BASE HIT"
    if hit_distance + offset < 325:
        if luck < 0.5:
            return "FLYOUT"
        if luck < 0.75:
            return "BASE HIT"
        return "DOUBLE"
    if hit_distance + offset < 350:
        if luck < 0.5:
            return "DEEP FLYOUT"
        if luck < 0.75:
            return "TRIPLE"
        return "HOME RUN"
    if hit_distance + offset < 450:
        return "HOME RUN"
    return "GONE"

# Function computing speed of pitch in terms of iters - pitches should vary more overtime, approaching min duration to max window
max_duration = 1200
min_duration = 700
step = 50
strikes = 0

def rand_duration(iters):
    duration_floor = max(min_duration, max_duration - iters * step) 
    return random.randint(duration_floor, max_duration)

# Set up font for printing things on screen
font_file = "joystix monospace.otf"
font = pygame.font.Font(font_file, 40)
font2 = pygame.font.Font(font_file, 20)
fontb = pygame.font.Font(font_file, 80)

# Score is number of HR, farthest_hit is farthest hit
num_outs = 1 #3 # Number of outs before game ends

# Text handling
username = ""
cursor_visible = True
cursor_timer = 0
CURSOR_BLINK_TIME = 500  # milliseconds
username_stage = True

# Initialize j = 0 - constant speed, and click to false
j = 0
click = False
ball_hit = False
score = 0
strikes = 0
outs = 0
iters = 0
duration = 1200
farthest_hit = 0
running = False
transition = False
leader_stage = False

# Game loop
while True:
    for event in pygame.event.get(): # Monitor user input
        if event.type == pygame.QUIT: # Close game
            conn.close()
            pygame.mixer.music.stop()
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN: # See if trackpad clicked
            # Get the touch position
            touch_x, touch_y = pygame.mouse.get_pos()
            click = True
        elif event.type == pygame.KEYDOWN and username_stage == True: # See if key entered
            if event.key == pygame.K_RETURN and len(username) > 0:
                username_stage = False
                print("Username:", username)
            elif event.key == pygame.K_BACKSPACE:
                username = username[:-1]
            elif event.key != pygame.K_RETURN and (event.key != pygame.K_SPACE or len(username) > 0) and len(username) < 16:
                username += event.unicode.upper()
    
    if username_stage: # This is true if we are in the game phase when the useer enters a username
        # Clear the screen
        screen.fill(LOAD_COLOR)
        
        # Render the text
        rendered_text = font.render("USERNAME: " + username, True, LRED)
        text_rect = rendered_text.get_rect(center=(width // 2, height // 2))
        screen.blit(rendered_text, text_rect)

        # Handle cursor blinking
        if pygame.time.get_ticks() - cursor_timer > CURSOR_BLINK_TIME:
            cursor_visible = not cursor_visible
            cursor_timer = pygame.time.get_ticks()

        # Draw cursor if visible
        if cursor_visible:
            cursor_surface = font.render("|", True, LRED)
            cursor_rect = cursor_surface.get_rect()
            cursor_rect.left = text_rect.right + 5
            cursor_rect.centery = text_rect.centery
            screen.blit(cursor_surface, cursor_rect)

        # Update the display
        pygame.display.flip()
        click = False # prevent game from starting immediately

    elif leader_stage: # This is true if we are in the game phase where the leaderboard is shown
        # Looking at the leaderboard after a game
        # Get the leaderboard data from the database
        cursor.execute("SELECT username, hrs, max_distance FROM highscores ORDER BY hrs DESC, max_distance DESC LIMIT 10")
        leaderboard = cursor.fetchall()

        # Fill screen with leaderboard background color
        screen.fill(LEAD_COLOR)
        y = 180
        spacer_y = 50
        xcenter = width // 2
        xleft = (xcenter + wbuffer) // 2
        xright = (xcenter + width - wbuffer) // 2

        # Write headings for the leaderboard columns
        text1 = fontb.render("LEADERBOARD", True, LEAD_HIGHLIGHT_TEXT)
        text1_rect = text1.get_rect(center=(xcenter, y // 2 - 10))
        screen.blit(text1, text1_rect)

        text1 = font2.render("PLAYER", True, TEXT_COLOR)
        text1_rect = text1.get_rect(center=(xleft, y))
        screen.blit(text1, text1_rect)

        text1 = font2.render("SCORE", True, TEXT_COLOR)
        text1_rect = text1.get_rect(center=(xcenter, y))
        screen.blit(text1, text1_rect)

        text1 = font2.render("FARTHEST HIT", True, TEXT_COLOR)
        text1_rect = text1.get_rect(center=(xright, y))
        screen.blit(text1, text1_rect)

        y += spacer_y

        # Display 10 names and scores on screen
        for i in range(len(leaderboard)):
            if leaderboard[i][0] == username:
                COL = LEAD_HIGHLIGHT_TEXT
            else:
                COL = TEXT_COLOR

            # Name and number column
            text1 = font2.render(str(i + 1) + ". " + str(leaderboard[i][0]), True, COL)
            text1_rect = text1.get_rect(center=(xleft, y))
            screen.blit(text1, text1_rect)

            # Score column
            text1 = font2.render(str(leaderboard[i][1]), True, COL)
            text1_rect = text1.get_rect(center=(xcenter, y))
            screen.blit(text1, text1_rect)

            # Score column
            text1 = font2.render(str(leaderboard[i][2]), True, COL)
            text1_rect = text1.get_rect(center=(xright, y))
            screen.blit(text1, text1_rect)

            y += spacer_y

        pygame.display.update()

        if click: # If we have clicked, then we exit from the leaderboard stage and go to the home screen
            leader_stage = False
            click = False


    elif transition: # This occurs after we have been on the home screen and clicked to start the game
        # Play a nice color fading animation
        curr_color = [TARG[0], TARG[1], TARG[2]]

        for i in range(num_intervals):
            # Change the background to be closer to target color
            curr_color[0] -= r_step
            curr_color[1] -= g_step
            curr_color[2] -= b_step
            screen.fill(curr_color)
            pygame.display.update() # Render frame
            pygame.time.delay(anim_interval)

        # Initialize time, first nodes
        start_time = pygame.time.get_ticks()
        control_points = [(pitcher_x, pitcher_y), rand_node(), rand_strike()]

        transition = False
        running = True

    if running: # This is the main gameplay loop for the game
        # If the ball has not been hit, throw a pitch, wait the buffer
        if ball_hit == False:
            # Get current time
            current_time = pygame.time.get_ticks()
            
            # If more than duration has elapsed, pick new points, reset start time, ball size, etc
            if current_time - start_time > duration:
                screen.fill(BACKGROUND) # Set background color

                # Display score and farthest hit
                score_text = font2.render("SCORE: " + str(score), True, TEXT_COLOR)
                far_text = font2.render("FARTHEST HIT: " + str(farthest_hit), True, TEXT_COLOR)
                score_text_rect = score_text.get_rect(topright=(width - wbuffer, hbuffer))
                far_text_rect = far_text.get_rect(topright=(width - wbuffer, hbuffer + 25))
                screen.blit(score_text, score_text_rect)
                screen.blit(far_text, far_text_rect)

                # Display the strike zone
                pygame.draw.rect(screen, strike_zone_color, strike_zone, width = slinewidth)

                strikes += 1
                if strikes >= 3:
                    strikes = 0
                    outs += 1
                    # Display outs on the screen
                    text1 = font.render("OUT " + str(outs), True, TEXT_COLOR)
                    text1_rect = text1.get_rect(center=(width // 2, height // 4))

                else:
                    # Display strike on the screen
                    text1 = font.render("STRIKE " + str(strikes), True, TEXT_COLOR)
                    text1_rect = text1.get_rect(center=(width // 2, height // 4))

                if outs >= num_outs: # Outs is greater than number of outs - game is over

                        running = False
                        # Add username and score to table if best so far - RETURN
                        cursor.execute("SELECT * FROM highscores WHERE username = ?", (username, ))
                        conn.commit()
                        existing_user = cursor.fetchone()
                        if existing_user is None: # New username, never before seen
                            print("Inserting new user into table")
                            cursor.execute("INSERT INTO highscores (username, hrs, max_distance) VALUES (?, ?, ?)", (username, score, farthest_hit))
                            conn.commit()
                        else:
                            print(existing_user)
                            new_score = max(existing_user[1], score)
                            new_dist = max(existing_user[2], farthest_hit)
                            # print(new_score, new_dist)
                            # Delete old entry, insert new entry with maxima
                            print("Replacing existing in table")
                            cursor.execute("DELETE FROM highscores WHERE username = ?", (username, ))
                            conn.commit()
                            cursor.execute("INSERT INTO highscores (username, hrs, max_distance) VALUES (?, ?, ?)", (username, new_score, new_dist))
                            conn.commit()

                        # Here, we want to have a screen where we display the nearest 10 entries on the leaderboard
                        # For a few seconds before returning to the home screen
                        leader_stage = True 

                else: # Game is not over, so update screen

                    # Display text
                    screen.blit(text1, text1_rect)
                    pygame.display.update() # Render frame

                    # Wait the buffer amount of time
                    pygame.time.delay(buffer)
                    iters += 1

                    # Before the next pitch is thrown, we draw the pitcher waiting to pitch
                    screen.fill(BACKGROUND) # Set background color

                    # Display score and farthest hit
                    score_text = font2.render("SCORE: " + str(score), True, TEXT_COLOR)
                    far_text = font2.render("FARTHEST HIT: " + str(farthest_hit), True, TEXT_COLOR)
                    score_text_rect = score_text.get_rect(topright=(width - wbuffer, hbuffer))
                    far_text_rect = far_text.get_rect(topright=(width - wbuffer, hbuffer + 25))
                    screen.blit(score_text, score_text_rect)
                    screen.blit(far_text, far_text_rect)

                    # Display the strike zone
                    pygame.draw.rect(screen, strike_zone_color, strike_zone, width = slinewidth)

                    # Draw the pitcher pre pitch
                    screen.blit(pitcher1, pitcher1_rect)

                    pygame.display.update() # Render frame

                    pygame.time.delay(buffer // 6)

                    # Play pitch swoosh sound
                    pitch_sound.play()

                    # Wait some more
                    pygame.time.delay(buffer // 6)

                    # Choose all new parameters and reset start_time
                    duration = rand_duration(iters)
                    control_points = [(pitcher_x, pitcher_y), rand_node(), rand_strike()]
                    start_time = pygame.time.get_ticks()
                    j = random.uniform(-1, 1)
                    ball_radius = ball_size / 2

            else: # Pitch still being thrown
                screen.fill(BACKGROUND) # Set background color

                # Display score and farthest hit
                score_text = font2.render("SCORE: " + str(score), True, TEXT_COLOR)
                far_text = font2.render("FARTHEST HIT: " + str(farthest_hit), True, TEXT_COLOR)
                score_text_rect = score_text.get_rect(topright=(width - wbuffer, hbuffer))
                far_text_rect = far_text.get_rect(topright=(width - wbuffer, hbuffer + 25))
                screen.blit(score_text, score_text_rect)
                screen.blit(far_text, far_text_rect)

                # Draw the pitcher post pitch
                screen.blit(pitcher2, pitcher2_rect)

                # Display the strike zone
                pygame.draw.rect(screen, strike_zone_color, strike_zone, width = slinewidth)

                # --- Pitch throwing mechanics ---
                # Parameter for Bezier curve
                t = (current_time - start_time) / duration

                # Set size of ball based on distance from batter - starts at half, goes to full
                ball_radius = ball_size * (1 + tweak(t, j)) / 2

                # Draw ball
                pygame.draw.circle(screen, ball_color, ball_pos(tweak(t, j), control_points), ball_radius)

                # Draw bat at mouse position
                mouse_pos = pygame.mouse.get_pos()
                bat_rect = bat.get_rect(center = (mouse_pos[0] - 10, mouse_pos[1]))
                screen.blit(bat, bat_rect)

                # Check if ball has been hit by click
                if click:
                    # First, see if swing is early or late
                    if ideal_contact_point - tweak(t, j) > contact_radius:
                        pass
                        # print("Too early")
                    elif ideal_contact_point - tweak(t, j) < -contact_radius:
                        pass
                        # print("Too late")
                    else:
                        # Define hitbox of bat - rectangle cenetered at click
                        bat_hitbox = pygame.Rect(touch_x - bat_width / 2, touch_y -  bat_height / 2, bat_width, bat_height)

                        # Define bat rectangle's sprite
                        bat_rect = bat.get_rect(center = (touch_x - 10, touch_y))

                        # Define hitbox of ball - rectangle containing ball
                        ball_x, ball_y = ball_pos(tweak(t, j), control_points)
                        ball_hitbox = pygame.Rect(ball_x - ball_size, ball_y -  ball_size, 2 * ball_size, 2 * ball_size)
                        
                        # Check if ball has been hit
                        if bat_hitbox.colliderect(ball_hitbox):
                            
                            ball_hit = True

                            # Compute power, duration, distance of hit
                            dist = ((touch_x - ball_x) ** 2 + (touch_y - ball_y) ** 2) ** (1/2)
                            hit_duration = hit_dur(dist)
                            distance = hit_distance(power(dist))
                            type = hit_type(distance)
                            # hit_index = int(10 * power(dist) ** 3)
                            hit_index = int(num_intervals * power(dist) ** 3)

                            # Play a cool little animation based on power - Green towards red based on power, then slow fade back
                            charge_sound = charge.play()

                            # Parameters for background color effects
                            curr_color = [BACKGROUND[0], BACKGROUND[1], BACKGROUND[2]]
                            fade_color = curr_color

                            # Play color fading, show bat if ball is hit well enough
                            if hit_index > num_intervals / 2:
                                for i in range(hit_index):
                                    # Change the background to be closer to target color
                                    curr_color[0] += r_step
                                    curr_color[1] += g_step
                                    curr_color[2] += b_step
                                    screen.fill(curr_color)

                                    # Display score and farthest hit
                                    score_text = font2.render("SCORE: " + str(score), True, TEXT_COLOR)
                                    far_text = font2.render("FARTHEST HIT: " + str(farthest_hit), True, TEXT_COLOR)
                                    score_text_rect = score_text.get_rect(topright=(width - wbuffer, hbuffer))
                                    far_text_rect = far_text.get_rect(topright=(width - wbuffer, hbuffer + 25))
                                    screen.blit(score_text, score_text_rect)
                                    screen.blit(far_text, far_text_rect)
                    
                                    pygame.draw.rect(screen, strike_zone_color, strike_zone, width = slinewidth) # Strike zone
                                    pygame.draw.circle(screen, ball_color, ball_pos(tweak(t, j), control_points), ball_radius) # Ball
                                    # pygame.draw.rect(screen, RED, bat_hitbox) # Bat hitbox
                                    screen.blit(bat, bat_rect) # Bat sprite
                                    pygame.display.update() # Render frame
                                    pygame.time.delay(anim_interval)

                            # Bat crack sound, stop charge sound
                            charge_sound.stop()
                            crack.play()
                                
                            # Reset start time because new ball trajectory begins
                            start_time = pygame.time.get_ticks()

                            # Update farthest hit, score
                            if distance > farthest_hit:
                                farthest_hit = distance
                            if type == "HOME RUN" or type == "GONE":
                                score += 1

                            # If ball is pulled, it ends up on left side
                            if touch_x - ball_x > - bat_width / 6:
                                end_x = random.randint(width // 2 - 2 * height // 3, width // 2)
                            else:
                                end_x = random.randint(width // 2, width // 2 + 2 * height // 3)
                            
                            end_y = random.randint(-500, -100)

                            # Choose random midpoints for Bezier curve
                            mid_x = random.randint(int(min(ball_x, end_x)), int(max(ball_x, end_x)))
                            mid_y = random.randint(int(min(ball_y, end_y)), int(max(ball_y, end_y)))

                            # Compute the ball's trajectory
                            control_points = [(ball_x, ball_y), 
                                            (mid_x, mid_y),
                                            (end_x, end_y)]

                # Draw curve skeleton - for testing
                pygame.draw.circle(screen, 'BLACK', control_points[0], 5)
                pygame.draw.circle(screen, 'BLACK', control_points[1], 5)
                pygame.draw.circle(screen, 'BLACK', control_points[2], 5)
                pygame.draw.aalines(screen, 'RED', False, control_points, 2)
            
        # If the ball has been hit:
        if ball_hit:
            # We want to show the ball flying away, then set reset ball_hit
            # Get current time
            current_time = pygame.time.get_ticks()

            # If all time has elapsed, reset all parameters
            if current_time - start_time > hit_duration:
                pygame.time.delay(buffer)

                # Before the next pitch is thrown, we draw the pitcher waiting to pitch
                screen.fill(BACKGROUND) # Set background color

                # Display score and farthest hit
                score_text = font2.render("SCORE: " + str(score), True, TEXT_COLOR)
                far_text = font2.render("FARTHEST HIT: " + str(farthest_hit), True, TEXT_COLOR)
                score_text_rect = score_text.get_rect(topright=(width - wbuffer, hbuffer))
                far_text_rect = far_text.get_rect(topright=(width - wbuffer, hbuffer + 25))
                screen.blit(score_text, score_text_rect)
                screen.blit(far_text, far_text_rect)

                # Display the strike zone
                pygame.draw.rect(screen, strike_zone_color, strike_zone, width = slinewidth)

                # Draw the pitcher pre pitch
                screen.blit(pitcher1, pitcher1_rect)

                pygame.display.update() # Render frame

                pygame.time.delay(buffer // 6)

                # Play pitch swoosh sound
                pitch_sound.play()

                # Wait some more
                pygame.time.delay(buffer // 6)
               
                iters += 1

                # Choose all new parameters and reset start_time
                duration = rand_duration(iters)
                ball_hit = False
                control_points = [(pitcher_x, pitcher_y), rand_node(), rand_strike()]
                start_time = pygame.time.get_ticks()
                j = random.uniform(-1, 1)
                ball_radius = ball_size / 2

            else:
                # Parameter for Bezier curve
                t = (current_time - start_time) / hit_duration

                # Update background to be correct fade color
                if ball_hit:
                    for i in range(3):
                        fade_color[i] = int(curr_color[i] * (1 - t) + BACKGROUND[i] * t)

                screen.fill(fade_color) # Set background color

                # Display score and farthest hit
                score_text = font2.render("SCORE: " + str(score), True, TEXT_COLOR)
                far_text = font2.render("FARTHEST HIT: " + str(farthest_hit), True, TEXT_COLOR)
                score_text_rect = score_text.get_rect(topright=(width - wbuffer, hbuffer))
                far_text_rect = far_text.get_rect(topright=(width - wbuffer, hbuffer + 25))
                screen.blit(score_text, score_text_rect)
                screen.blit(far_text, far_text_rect)

                # Display the strike zone
                pygame.draw.rect(screen, strike_zone_color, strike_zone, width = slinewidth)

                # Set size of ball based on distance from batter - starts at 10, goes to 5
                ball_radius = ball_size * (2 - tweak(t, j)) / 2

                # Text showing distance, kind of hit above the bat
                text1 = font.render(str(distance), True, TEXT_COLOR)
                text2 = font.render(type, True, TEXT_COLOR)
                text1_rect = text1.get_rect(center=(width // 2, height // 4))
                text2_rect = text2.get_rect(center=(width // 2, height // 4 + 50))
                screen.blit(text1, text1_rect)
                screen.blit(text2, text2_rect)

                # Draw ball
                pygame.draw.circle(screen, ball_color, ball_pos(tweak(t, j), control_points), ball_radius)

        pygame.display.update() # Render frame
        click = False # Reset click
        clock.tick(120) # Limit to 120 fps

    elif username_stage == False and leader_stage == False:
        # Home screen
        screen.fill(ALT_BACKGROUND)

        # Display score, farthest hit, etc -- home screen
        text1 = fontb.render("BLITZBALL", True, YELLOW)
        text2 = font.render("YOUR SCORE: " + str(score), True, TEXT_COLOR)
        text3 = font.render("FARTHEST HIT: " + str(farthest_hit), True, TEXT_COLOR)
        text4 = font.render("CLICK TO START", True, TEXT_COLOR)
        text1_rect = text1.get_rect(center=(width // 2, height // 2 - 75))
        text2_rect = text2.get_rect(center=(width // 2, height // 2 + 25))
        text3_rect = text3.get_rect(center=(width // 2, height // 2 + 75))
        text4_rect = text4.get_rect(center=(width // 2, height // 2 + 125))
        screen.blit(text1, text1_rect)
        screen.blit(text2, text2_rect)
        screen.blit(text3, text3_rect)

        # Flicker PRESS ENTER
        now = pygame.time.get_ticks()
        if now % 1000 < 500:
            screen.blit(text4, text4_rect)

        if click:
            # Reset all and restart if click
            j = 0
            click = False
            ball_hit = False
            score = 0
            strikes = 0
            outs = 0
            iters = 0
            duration = 1200
            farthest_hit = 0
            transition = True

        pygame.display.update() # Render frame
        clock.tick(120) # Limit to 120 fps