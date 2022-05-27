import pygame, math, random, pickle

MUSHROOM_WIDTH = 20
MUSHROOM_HEIGHT = 20
MUSHROOM_COLOR = (0,255,0)

PLAYER_SMALL_HEIGHT = 25
PLAYER_BIG_HEIGHT = 40
PLAYER_WIDTH = 20

class Game:
    def __init__(self):
        self.width = 700 # screen 
        self.height = 495
        self.screen = pygame.display.set_mode([self.width, self.height])
        pygame.display.set_caption("SquareJumper")
        self.clock = pygame.time.Clock()
        self.framerate = 60
        self.frame_time = 0 # time for last frame to take place

        self.level = 0

        self.edit_action_font = pygame.font.Font(None, 25)
        self.hud_font = pygame.font.Font(None, 20)
        self.player = Player()
        self.objects = {"collision_rects":[],"climbing_rects":[],"enemies":[],"mushrooms":[],"animations":[],"particles":[],
                        "camera_lines":[],"pipes":[],"coins":[],"flags":[],"clouds":[]}
        self.object_mappings = {CollisionRect:"collision_rects",MovingCollisionRect:"collision_rects",ItemizedCollisionRect:"collision_rects",
                                ClimbingRect:"climbing_rects",Pipe:"pipes",
                                WalkEnemy:"enemies",JumpEnemy:"enemies",JumpThrowEnemy:"enemies",Axe:"enemies",FlyingEnemy:"enemies",
                                Mushroom:"mushrooms",
                                AnimationMushroom:"animations",AnimationPlayerInPipe:"animations",
                                Particle:"particles",
                                CameraLine:"camera_lines",
                                Coin:"coins",
                                RespawnFlag:"flags", WinFlag:"flags",
                                Cloud:"clouds"}
        self.load_saved_object_state()
        self.game_stopping_animation = None

        self.camera = Camera(self)
        self.hud = Hud()

        self.play_mode = True # if false: edit mode

        self.mouse_clicked_this_frame = [False, False, False] # left, middle, right
        self.space_pressed_this_frame = False
        self.up_pressed_this_frame = False
        self.down_pressed_this_frame = False

        self.start_game()

    def load_saved_object_state(self):
        self.game_stopping_animation = None
        self.player.visible = True

        with open("level"+str(self.level)+".pickle", "rb") as f:
            try:
                self.objects = pickle.load(f)
            except:
                print("empty level")

        self.logic_order = ["collision_rects","player","enemies","mushrooms","animations","particles","flags","clouds"] # note the omitted
        self.draw_order = ["animations","pipes","coins","collision_rects","flags","enemies","particles","mushrooms","player","climbing_rects","clouds"]
        self.collision_rects = self.objects["collision_rects"]
        self.climbing_rects = self.objects["climbing_rects"]
        self.enemies = self.objects["enemies"]
        self.mushrooms = self.objects["mushrooms"]
        self.animations = self.objects["animations"]
        self.particles = self.objects["particles"]
        self.camera_lines = self.objects["camera_lines"]
        self.pipes = self.objects["pipes"]
        self.coins = self.objects["coins"]
        self.flags = self.objects["flags"]
        if "clouds" in self.objects:
            self.clouds = self.objects["clouds"]
        else:
            self.objects["clouds"] = []

        self.objects_to_add = []
        self.objects_to_remove = []

    def save_object_state(self):
        with open("level"+str(self.level)+".pickle", "wb") as f:
            pickle.dump(self.objects, f)

    def load_new_level(self, way=1):
        self.level += way
        self.player.set_position_to(0,0)
        self.player.respawn_point = (0,0)
        self.camera.teleport_to((-self.width/2, -self.height/2))
        self.load_saved_object_state()

    def start_game(self):
        running = True
        while running:
            self.mouse_clicked_this_frame = [False, False, False]
            self.space_pressed_this_frame = False
            self.up_pressed_this_frame = False
            self.down_pressed_this_frame = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_k: 
                        if self.play_mode: # into edit mode
                            self.load_saved_object_state()
                            
                        else: # move player to camera
                            self.save_object_state()
                            self.player.set_position_to(self.camera.x+self.width/2-self.player.width/2,self.camera.y+self.height/2-self.player.height/2)
                        
                        self.play_mode = not self.play_mode

                    if event.key == pygame.K_SPACE:
                        self.space_pressed_this_frame = True
                    if event.key == pygame.K_o:
                        self.camera.change_edit_action(-1)
                    if event.key == pygame.K_p:
                        self.camera.change_edit_action(1)
                    if event.key == pygame.K_u:
                        self.camera.change_edit_y_place(-1)
                    if event.key == pygame.K_j:
                        self.camera.change_edit_y_place(1)
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        self.up_pressed_this_frame = True
                    if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        self.down_pressed_this_frame = True
                    #if event.key == pygame.K_h:
                        

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 1 <= event.button <= 3:
                        self.mouse_clicked_this_frame[event.button - 1] = True

            self.do_game_logic()

            self.do_game_drawing()

            self.frame_time = self.clock.tick(self.framerate)
    def do_game_logic(self):

        if self.play_mode:
            self.do_game_play_logic()
        else:
            self.do_game_edit_logic()

        # add and remove necessary objects
        for obj in self.objects_to_remove:
            self.objects[self.object_mappings[type(obj)]].remove(obj)
        for obj in self.objects_to_add:
            self.objects[self.object_mappings[type(obj)]].append(obj)
        self.objects_to_add = []
        self.objects_to_remove = []

    def do_game_play_logic(self):
        if self.game_stopping_animation == None:
            for category in self.logic_order: # logic for all objects
                if category == "player":
                    self.player.logic(self)
                else:
                    for obj in self.objects[category]:
                        obj.logic(self)

            self.camera.play_logic(self)
            
        else: # game stopping animation
            self.game_stopping_animation.logic(self)

    def do_game_edit_logic(self):
        self.camera.edit_logic(self)

    def do_game_drawing(self):
        # Fill the background with white
        self.screen.fill((255, 255, 255))

        for category in self.draw_order:
            if category == "player":
                self.player.draw(self)
            else:
                for obj in self.objects[category]:
                    obj.draw(self)

        if self.play_mode:
            self.hud.draw(self)
        else:
            self.camera.draw_edit_things(self)

        # Flip the display
        pygame.display.flip()

class General: # rects are objects with x,y,width,height
    @staticmethod
    def rects_collide_tuples(f, s): # first and second object
        return f[0]+f[2] > s[0] and f[0] < s[0]+s[2] and f[1]+f[3] > s[1] and f[1] < s[1]+s[3]
    @staticmethod
    def rects_collide(f, s): # first and second object. Both require x,y,width,height variables
        return General.rects_collide_tuples((f.x,f.y,f.width,f.height),(s.x,s.y,s.width,s.height))
    @staticmethod
    def point_in_rect(p, r): # point and rect. Both require x,y,width,height variables
        return General.rects_collide_tuples((p[0],p[1],0,0),(r.x,r.y,r.width,r.height))
    @staticmethod
    def line_in_rect (x1, y1, x2, y2, minX, minY, maxX, maxY):
        # Completely outside.
        if (x1 <= minX and x2 <= minX) or (y1 <= minY and y2 <= minY) or (x1 >= maxX and x2 >= maxX) or (y1 >= maxY and y2 >= maxY):
            return False
        if x2 - x1 == 0:
            m = 0
        else:
            m = (y2 - y1) / (x2 - x1)
        y = m * (minX - x1) + y1
        if y > minY and y < maxY: return True
        y = m * (maxX - x1) + y1
        if y > minY and y < maxY: return True
        if m == 0:
            x = x1
        else:
            x = (minY - y1) / m + x1
        if x > minX and x < maxX: return True
        if m == 0:
            x = x1
        else:
            x = (maxY - y1) / m + x1
        if x > minX and x < maxX: return True
        return False
    @staticmethod
    def line_in_tuple_rect(start_pos, end_pos, r): # pos is for line
        # check start and end position
        if General.rects_collide_tuples(start_pos+(0,0),r) or General.rects_collide_tuples(end_pos+(0,0),r):
            return True
        if General.line_in_rect(start_pos[0],start_pos[1],end_pos[0],end_pos[1],r[0],r[1],r[0]+r[2],r[1]+r[3]):
            return True
        return False
    @staticmethod
    def get_rect_of_two_points(p1, p2, grid_size):
        x1, x2 = (p1[0], p2[0]) if p2[0] >= p1[0] else (p2[0], p1[0])
        y1, y2 = (p1[1], p2[1]) if p2[1] >= p1[1] else (p2[1], p1[1])
        w, h = (x2 - x1 + grid_size, y2 - y1 + grid_size)
        return (x1, y1, w, h)
    @staticmethod
    def circle_in_rect(circle_pos, circle_radius, rect):
        dx = abs(circle_pos[0] - (rect.x+rect.width/2))
        dy = abs(circle_pos[1] - (rect.y+rect.height/2))
        if dx + dy <= circle_radius*1.5:
            return True
        return False

class Hud:
    def draw(self, g):
        text = "Coins:"+str(g.player.coins) + " FPS:" + str(int(g.clock.get_fps()))
        text_surface = g.hud_font.render(text, True, (0,0,0))
        g.screen.blit(text_surface, (0,0))

EDIT_ACTIONS = 7 # how many different objects there are to place
EDIT_COL_RECT, EDIT_MOVING_COL_RECT, EDIT_ENEMY, EDIT_CAM_LINE, EDIT_PIPE, EDIT_COIN, EDIT_FLAG = range(EDIT_ACTIONS)

EDIT_OPTIONS = [2, 1, 8, 0, 1, 0, 1]
EDIT_TEXTS = [["Collision Rect","Has item?","Climbing?"],["Moving Collsion Rect, first width, then start+end pos","Speed?"],
              ["Enemy","Turns at edges?","Jumps?","Jump: walks on ground?", "Jump: walks in air?", "Throws?","Flying?",
               "Flying Speed", "Flying Range"],["Camera Line"],["Pipe","Color?"],["Coin"],["Flag","Respawn/Win?"]]
EDIT_COL_RECT_ITEM, EDIT_COL_RECT_CLIMBING = range(2)
EDIT_MOVING_COL_RECT_SPEED = 0
EDIT_ENEMY_EDGES,EDIT_ENEMY_JUMPS,EDIT_ENEMY_JUMP_WALKS_GROUND,EDIT_ENEMY_JUMP_WALKS_AIR,EDIT_ENEMY_THROW, \
    EDIT_ENEMY_FLYING, EDIT_ENEMY_FLYING_SPEED, EDIT_ENEMY_FLYING_RANGE = range(8)
EDIT_PIPE_COLOR = 0
EDIT_FLAG_RESPAWN_WIN = 0
class Camera:
    def __init__(self, g):
        self.x = -g.width/2
        self.y = -g.height/2
        self.grid_size = 30
        self.x_offset = 0
        self.x_offset_max = g.width*0.1
        """self.x_vel = 0
        self.y_vel = 0"""
        self.cloud_timer = 0
        
        self.edit_action = EDIT_COL_RECT # what object to place
        self.edit_y_place = 0 # 0 is the category, others are options
        self.options = []
        for i in range(EDIT_ACTIONS):
            self.options.append([])
            for _ in range(EDIT_OPTIONS[i]):
                self.options[i].append(0)

        print(self.options)

        self.edit_points_clicked = []

    def bad_play_logic(self, g):
        dif = 0.5

        x_endpoint = g.player.x + g.player.width/2 - g.width/2
        x_increase = ((x_endpoint - self.x)/300) * g.frame_time
        if abs(self.x_vel - x_increase) > dif:
            self.x_vel += dif if x_increase > self.x_vel else -dif
        screen_rect = (self.x + self.x_vel, self.y, g.width, g.height)
        
        for cl in g.camera_lines:
            if General.line_in_tuple_rect(cl.start_pos,cl.end_pos, screen_rect):
                self.x_vel = 0
                break
        else:
            self.x += self.x_vel
        
        y_endpoint = (g.player.y+g.player.height/2) - g.height/2
        y_increase = ((y_endpoint - self.y)/150) * g.frame_time
        if abs(self.y_vel - y_increase) > dif:
            self.y_vel += dif if y_increase > self.y_vel else -dif
        screen_rect = (self.x, self.y + self.y_vel, g.width, g.height)

        for cl in g.camera_lines:
            if General.line_in_tuple_rect(cl.start_pos,cl.end_pos, screen_rect):
                self.y_vel = 0
                break
        else:
            self.y += self.y_vel
    def play_logic(self, g):

        x_endpoint = g.player.x + g.player.width/2 + self.x_offset - g.width/2
        x_increase = ((x_endpoint - self.x)/300) * g.frame_time
        
        self.x_offset += x_increase/3
        self.x_offset = max(-self.x_offset_max, min(self.x_offset_max, self.x_offset))

        screen_rect = (self.x + x_increase, self.y, g.width, g.height)
        
        for cl in g.camera_lines:
            if General.line_in_tuple_rect(cl.start_pos,cl.end_pos, screen_rect):
                break
        else:
            self.x += x_increase
        
        y_endpoint = (g.player.y+g.player.height/2) - g.height/2
        y_increase = ((y_endpoint - self.y)/150) * g.frame_time
        screen_rect = (self.x, self.y + y_increase, g.width, g.height)

        for cl in g.camera_lines:
            if General.line_in_tuple_rect(cl.start_pos,cl.end_pos, screen_rect):
                break
        else:
            self.y += y_increase

        # handle clouds
        self.cloud_timer += g.frame_time
        if self.cloud_timer > 2000:
            g.objects_to_add.append(Cloud(g))
            self.cloud_timer = 0

    def edit_logic(self, g):
        pressed_keys = pygame.key.get_pressed() # move
        vel = 0.3*g.frame_time
        if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
            self.x += vel
        if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
            self.x -= vel
        if pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w]:
            self.y -= vel
        if pressed_keys[pygame.K_DOWN] or pressed_keys[pygame.K_s]:
            self.y += vel

        
        # place objects
        m_pos = pygame.mouse.get_pos()
        exact_x = m_pos[0]+self.x
        exact_y = m_pos[1]+self.y
        x = exact_x - (exact_x % self.grid_size) # moved to grind lines
        y = exact_y - (exact_y % self.grid_size)
        if g.mouse_clicked_this_frame[0]: # left mouse button = create object in game
            if self.edit_action == EDIT_COL_RECT:
                if len(self.edit_points_clicked) == 0:
                    self.edit_points_clicked.append((x, y))
                else:
                    x_, y_, w, h = General.get_rect_of_two_points((x,y), self.edit_points_clicked[0], self.grid_size)

                    if bool(self.options[EDIT_COL_RECT][EDIT_COL_RECT_CLIMBING]):
                        g.objects_to_add.append(ClimbingRect(x_,y_,w,h))
                    elif self.options[EDIT_COL_RECT][EDIT_COL_RECT_ITEM] == 0:
                        g.objects_to_add.append(CollisionRect(x_, y_, w, h))
                    elif self.options[EDIT_COL_RECT][EDIT_COL_RECT_ITEM] == 1:
                        g.objects_to_add.append(ItemizedCollisionRect(x_, y_, w, h))
                    self.edit_points_clicked = []

            elif self.edit_action == EDIT_MOVING_COL_RECT:
                if len(self.edit_points_clicked) < 3:
                    self.edit_points_clicked.append((x, y))
                else:
                    x1, y1 = self.edit_points_clicked[0]
                    x2, y2 = self.edit_points_clicked[1]
                    if x2 >= x1 and y2 >= y1: # legal
                        w, h = (x2 - x1 + self.grid_size, y2 - y1 + self.grid_size)
                        start_pos = self.edit_points_clicked[2]
                        end_pos = (x, y)
                        speed = 0.02 + self.options[EDIT_MOVING_COL_RECT][EDIT_MOVING_COL_RECT_SPEED] * 0.02
                        g.objects_to_add.append(MovingCollisionRect(start_pos, end_pos, w, h, speed))
                    self.edit_points_clicked = []

            elif self.edit_action == EDIT_ENEMY:
                turns = bool(self.options[EDIT_ENEMY][EDIT_ENEMY_EDGES])
                throws = bool(self.options[EDIT_ENEMY][EDIT_ENEMY_THROW])
                if self.options[EDIT_ENEMY][EDIT_ENEMY_FLYING]:
                    speed = self.options[EDIT_ENEMY][EDIT_ENEMY_FLYING_SPEED]
                    f_range = self.options[EDIT_ENEMY][EDIT_ENEMY_FLYING_RANGE]
                    g.objects_to_add.append(FlyingEnemy(x, y, speed, f_range, throws))

                elif self.options[EDIT_ENEMY][EDIT_ENEMY_JUMPS]:
                    if throws:
                        g.objects_to_add.append(JumpThrowEnemy(x, y))
                    else:
                        walks_on_ground = bool(self.options[EDIT_ENEMY][EDIT_ENEMY_JUMP_WALKS_GROUND])
                        walks_in_air = bool(self.options[EDIT_ENEMY][EDIT_ENEMY_JUMP_WALKS_AIR])
                        g.objects_to_add.append(JumpEnemy(x, y, walks_on_ground, walks_in_air))
                else:
                    g.objects_to_add.append(WalkEnemy(x, y, turns))

            elif self.edit_action == EDIT_CAM_LINE:
                if len(self.edit_points_clicked) == 0:
                    self.edit_points_clicked.append((x, y))
                else:
                    g.objects_to_add.append(CameraLine(self.edit_points_clicked[0], (x,y)))
                    self.edit_points_clicked = []
            
            elif self.edit_action == EDIT_PIPE:
                if len(self.edit_points_clicked) < 3:
                    self.edit_points_clicked.append((x, y))
                else:
                    x1, y1, w1, h1 = General.get_rect_of_two_points(self.edit_points_clicked[0], self.edit_points_clicked[1], self.grid_size)
                    x2, y2, w2, h2 = General.get_rect_of_two_points(self.edit_points_clicked[2], (x, y), self.grid_size)
                    color_value = self.options[EDIT_PIPE][EDIT_PIPE_COLOR]
                    g.objects_to_add.append(Pipe(x1, y1, w1, h1, color_value,(x2+w2/2,y2)))
                    g.objects_to_add.append(Pipe(x2, y2, w2, h2, color_value, (x1+w1/2,y1)))
                    self.edit_points_clicked = []

            elif self.edit_action == EDIT_COIN:
                g.objects_to_add.append(Coin(g,x,y))

            elif self.edit_action == EDIT_FLAG:
                if self.options[EDIT_FLAG][EDIT_FLAG_RESPAWN_WIN] == 0:
                    g.objects_to_add.append(RespawnFlag(g, x, y))
                else:
                    g.objects_to_add.append(WinFlag(g, x, y))
                
        elif g.mouse_clicked_this_frame[2]: # right = remove object in game
            for r in g.collision_rects + g.climbing_rects + g.pipes + g.enemies:
                if General.point_in_rect((exact_x, exact_y), r):
                    g.objects_to_remove.append(r)
                    break # only remove one per frame, (nicer)
            else:
                for cl in g.camera_lines: # camera line
                    if cl.start_pos[0] == x and cl.start_pos[1] == y:
                        g.objects_to_remove.append(cl)
                        break
                else:
                    for f in g.flags: # respawn flag
                        if General.rects_collide_tuples((f.x,f.y,self.grid_size,self.grid_size),(x,y+self.grid_size,10,10)):
                            g.objects_to_remove.append(f)
                            break
                    else:
                        for coin in g.coins:
                            if General.rects_collide_tuples((coin.x,coin.y,0,0),(x,y,self.grid_size,self.grid_size)):
                                g.objects_to_remove.append(coin)
                                break

    def translate_position(self, x, y): # translates real position to position in relation to the camera
        return x - self.x, y - self.y

    def draw_edit_things(self, g):
        self.draw_grid(g)
        self.draw_edit_action(g)
        self.draw_camera_lines(g)

    def draw_camera_lines(self, g):
        for cl in g.camera_lines:
            cl.draw(g)

    def draw_grid(self, g):
        x = - self.x % self.grid_size
        while x < g.width:
            pygame.draw.line(g.screen, (0,0,0), (int(x),0),(int(x),g.height))
            x += self.grid_size
        y = - self.y % self.grid_size
        while y < g.height:
            pygame.draw.line(g.screen, (0,0,0), (0,int(y)),(g.width,int(y)))
            y += self.grid_size

    def draw_edit_action(self, g):
        for i in range(EDIT_OPTIONS[self.edit_action] + 1):
            if i == 0:
                text = EDIT_TEXTS[self.edit_action][0]
            else:
                text = EDIT_TEXTS[self.edit_action][i] + ": " + str(self.options[self.edit_action][i-1])
            color = (0,255,0) if self.edit_y_place == i else (0,0,0)
            text_surface = g.edit_action_font.render(text, True, color)
            pos = (0,i*15)
            g.screen.blit(text_surface, pos)

    def change_edit_action(self, way):
        if self.edit_y_place == 0:
            self.edit_action += way
            if self.edit_action < 0: self.edit_action = EDIT_ACTIONS - 1
            elif self.edit_action >= EDIT_ACTIONS: self.edit_action = 0
        else:
            self.options[self.edit_action][self.edit_y_place-1] += way

    def change_edit_y_place(self, way):
        self.edit_y_place += way
        if self.edit_y_place < 0: self.edit_y_place = EDIT_OPTIONS[self.edit_action]
        elif self.edit_y_place > EDIT_OPTIONS[self.edit_action]: self.edit_y_place = 0

    def teleport_to(self, pos):
        self.x = pos[0]
        self.y = pos[1]

class CameraLine:
    def __init__(self, start_pos, end_pos): # cl_type = camera line type
        self.start_pos = start_pos
        self.end_pos = end_pos
    def draw(self, g):
        x1, y1 = g.camera.translate_position(self.start_pos[0], self.start_pos[1])
        x2, y2 = g.camera.translate_position(self.end_pos[0], self.end_pos[1])
        pygame.draw.line(g.screen, (255,0,0), (int(x1),int(y1)), (int(x2),int(y2)), 3)

class InteractiveObject:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.y_vel = 0
        self.x_vel = 0
        self.stood_on_ground_previous_frame = False
    def closest_side_of_rect(self, r): # requires x,y,width,height
        left_x_dif = abs((self.x)-(r.x-self.width))
        right_x_dif = abs((self.x)-(r.x+r.width))
        up_y_dif = abs((self.y)-(r.y-self.height))
        down_y_dif = abs((self.y)-(r.y+r.height))

        if up_y_dif < down_y_dif: # closest to up
            if right_x_dif < left_x_dif:
                if up_y_dif < right_x_dif:
                    return "up"
                else:
                    return "right"
            else:
                if up_y_dif < left_x_dif:
                    return "up"
                else:
                    return "left"
        else: 
            if right_x_dif < left_x_dif: # closest to down
                if down_y_dif < right_x_dif:
                    return "down"
                else:
                    return "right"
            else:
                if down_y_dif < left_x_dif:
                    return "down"
                else:
                    return "left"
    def handle_moving_like_physical_object(self, r, collide_part):
        if collide_part == "up":
            self.y = r.y - self.height
            self.y_vel = min(0, self.y_vel)
            self.stood_on_ground_previous_frame = True
            if type(r) == MovingCollisionRect:
                self.x_vel += r.x_vel
                self.y_vel += max(0, r.y_vel)
        elif collide_part == "down":
            self.y = r.y + r.height
            self.y_vel = max(0, self.y_vel)   
        elif collide_part == "right":
            self.x = r.x + r.width
            self.x_vel = max(0, self.x_vel)
        elif collide_part == "left":
            self.x = r.x - self.width
            self.x_vel = min(0, self.x_vel)
    def interact_with_collision_rects(self, g):
        self.stood_on_ground_previous_frame = False

        # VERB: correct placement, if it's illegal
        for r in g.collision_rects + g.pipes: # rect = r
            if General.rects_collide(self,r):
                collide_part = self.closest_side_of_rect(r)
                self.collide_rect_handle_before(r, collide_part, g)
                self.handle_moving_like_physical_object(r, collide_part)
                
    def collide_rect_handle_before(self, r, collide_part, g):
        pass
    def got_jumped_on(self, g):
        for _ in range(random.randint(10,30)):
            g.objects_to_add.append(Particle(self.x,self.y,self.width,self.height, self.color))
        g.objects_to_remove.append(self)

class Player(InteractiveObject):
    def __init__(self):
        super().__init__(0, 0, PLAYER_WIDTH, PLAYER_SMALL_HEIGHT)

        self.jump_mode = False
        self.jump_time = 1000
        self.jump_timer = self.jump_time

        self.climb_mode = False

        self.big = False # you get big when you eat a mushroom

        self.invincibility_timer = 0
        self.invincibility_time = 1500

        self.respawn_point = (0,0)

        self.pipe_player_is_on = None

        self.color = (255,255,255)
        self.visible = True

        self.coins = 0

    def set_position_to(self, x, y):
        self.x = x
        self.y = y
        self.x_vel = 0
        self.y_vel = 0
        self.jump_mode = False

    def logic(self, g):
        # move according to player input and physics

        pressed_keys = pygame.key.get_pressed()
        # interact with climbable rects
        if self.climb_mode:
            if self.allowed_to_climb(g):
                # climb
                speed = 0.1
                self.y_vel = 0
                if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
                    self.x_vel = speed
                if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
                    self.x_vel = -speed
                if pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w]:
                    self.y_vel = -speed
                if pressed_keys[pygame.K_DOWN] or pressed_keys[pygame.K_s]:
                    self.y_vel = speed
            else:
                self.climb_mode = False
        else:
            speed = 0.2 # move regularly
        
            if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
                self.x_vel += speed
            if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
                self.x_vel -= speed

            # possibly climb
            if g.up_pressed_this_frame and self.allowed_to_climb(g):
                self.climb_mode = True
                self.jump_mode = False

        # jump stuff
        if self.jump_mode:
            self.jump_timer += g.frame_time
            if self.jump_timer >= self.jump_time or not pressed_keys[pygame.K_SPACE]:
                self.jump_mode = False
                self.jump_timer = self.jump_time
        if (True if self.climb_mode else self.stood_on_ground_previous_frame) and g.space_pressed_this_frame:
            self.y_vel = -0.175
            self.jump_mode = True
            self.jump_timer = 0
            self.climb_mode = False

        if not self.climb_mode:
            gravity = 0.0175
            if self.jump_mode:
                self.y_vel += pow(self.jump_timer/self.jump_time,1)*gravity
            else:
                self.y_vel += gravity

        self.x += self.x_vel * g.frame_time
        self.x_vel = 0
        self.y += self.y_vel * g.frame_time
        
        self.interact_with_collision_rects(g)

        # die from being bad stuff
        if self.y_vel > 2:
            self.die(g)

        # invincibility stuff
        if self.invincibility_timer > 0:
            self.invincibility_timer -= g.frame_time
            self.invincibility_timer = max(0, self.invincibility_timer)

        # interact with enemies
        for e in g.enemies:
            if General.rects_collide(self, e):
                if e.can_be_jumped_on:
                    # check who attacks who
                    if General.rects_collide_tuples((self.x,self.y,self.width,self.height),(e.x,e.y+e.height/2,e.width,e.height/2)):
                        # player touched bottom half => player dies
                        self.get_hit(g)
                    else:
                        # player is on top => enemy dies
                        self.y_vel = -0.3
                        self.jump_mode = True
                        self.jump_timer = 0.2*self.jump_time
                        self.climb_mode = False
                        e.got_jumped_on(g) # removes enemy from array
                else:
                    self.get_hit(g) # without recourse
                break
        # interact with mushrooms
        for m in g.mushrooms:
            if General.rects_collide(self, m):
                self.eat_mushroom(g, m)

        # interact with pipes
        if g.down_pressed_this_frame:
            if self.pipe_player_is_on != None:
                g.game_stopping_animation = GameStoppingAnimationPlayerInPipe(g, self.pipe_player_is_on.teleport_pos)
        self.pipe_player_is_on = None # reset

        # interact with coins
        for coin in g.coins:
            if General.circle_in_rect((coin.x,coin.y),coin.radius, self):
                # collect coin
                coin.got_picked_up(g) # increases coins and kills coin
        
        # interact with flags
        for flag in g.flags:
            if General.rects_collide_tuples((self.x,self.y,self.width,self.height),(flag.x,flag.y-flag.length,0,flag.length)):
                flag.get_raised(g)
                if type(flag) == RespawnFlag:
                    self.respawn_point = (flag.x - 0.01,flag.y-self.height)
                if type(flag) == WinFlag:
                    pass

    def allowed_to_climb(self, g):
        for r in g.climbing_rects:
            if General.rects_collide(self,r):
                return True
        return False

    def collide_rect_handle_before(self, r, collide_part, g):
        if collide_part == "down":
            if self.y_vel < 0: # It only gets hit when jumped at from below, not above
                r.got_hit(g)
            self.jump_mode = False
        if collide_part == "up":
            if type(r) == Pipe and self.x > r.x and self.x+self.width < r.x+r.width:
                self.pipe_player_is_on = r

    def get_hit(self, g):
        if self.invincibility_timer == 0:
            if self.big:
                self.big = False
                self.invincibility_timer = self.invincibility_time
                g.game_stopping_animation = GameStoppingAnimation(GS_ANIMATION_PLAYER_GET_SMALLER)
            else:
                # die
                self.die(g)

    def die(self, g):
        print("die")
        g.game_stopping_animation = GameStoppingAnimation(GS_ANIMATION_PLAYER_DIES)

    def respawn(self, g):
        self.coins = 0
        g.load_saved_object_state()
        self.set_position_to(self.respawn_point[0], self.respawn_point[1])

    def eat_mushroom(self, g, m): # m = mushroom
        if not self.big:
            self.big = True
            g.game_stopping_animation = GameStoppingAnimation(GS_ANIMATION_PLAYER_GET_BIGGER)
        g.objects_to_remove.append(m)

    def draw(self, g):
        if self.visible:
            x, y = g.camera.translate_position(self.x, self.y)
            if self.invincibility_timer == 0 or self.invincibility_timer % 2 == 0:
                pygame.draw.rect(g.screen, (0,0,0), (int(x),int(y),int(self.width),int(self.height)), 1)

class SelfSovereignBeing(InteractiveObject): # moves around freely, turns at walls, possibly turns at edges
    def __init__(self, x, y, width, height, x_speed, y_speed, turns_around_at_edges=False, color=(50,50,255), can_be_jumped_on=False):
        super().__init__(x, y, width, height)

        self.x_speed = x_speed
        self.y_speed = y_speed
        self.color = color

        self.x_dir = -1
        self.turn_around_at_edges = turns_around_at_edges
        self.turn_around = False

        self.turned_on = False

        self.can_be_jumped_on = can_be_jumped_on

    def logic(self, g):
        if self.turned_on:
            self.logic_movement(g)
            self.logic_interacting(g)
        else:
            if General.rects_collide_tuples((g.camera.x,g.camera.y,g.width,g.height),(self.x,self.y,self.width,self.height)):
                self.turned_on = True
        
    def logic_movement(self, g):
        self.x_vel += self.x_dir * self.x_speed
        self.x += self.x_vel * g.frame_time
        self.x_vel = 0

        self.y_vel += self.y_speed
        self.y += self.y_vel * g.frame_time

    def logic_interacting(self, g):
        self.interact_with_collision_rects(g)
        if self.turn_around:
            self.x_dir *= -1
            self.turn_around = False

    def collide_rect_handle_before(self, r, collide_part, g):
        if collide_part == "up":
            # turn around at edges
            if self.turn_around_at_edges:
                if (self.x < r.x and self.x_dir < 0) or (self.x+self.width > r.x+r.width and self.x_dir > 0):
                    self.turn_around = True
        elif collide_part == "right":
            self.turn_around = True
        elif collide_part == "left":
            self.turn_around = True
    
    def remove_self_if_under_camera(self, g):
        x, y = g.camera.translate_position(self.x, self.y)
        if y > g.height: #or x > g.width or x < 0:
            # remove
            g.objects_to_remove.append(self)

    def draw(self, g):
        x, y = g.camera.translate_position(self.x, self.y)
        pygame.draw.rect(g.screen, self.color, (int(x),int(y),self.width,self.height))

class WalkEnemy(SelfSovereignBeing):
    def __init__(self, x, y, turns_around_at_edges=False):
        super().__init__(x, y, 25, 30, 0.1, 0.005, turns_around_at_edges, (50,50,255), True)

class JumpEnemy(SelfSovereignBeing):
    def __init__(self, x, y, walks_on_ground=True, walks_in_air=True):
        super().__init__(x, y, 25, 40, 0.1, 0.01, True, (50,100,255), True)

        self.wait_timer = 0
        self.wait_time = 750 # time to wait on ground til next jump
        self.walks_on_ground = walks_on_ground
        self.walks_in_air = walks_in_air

    def logic_movement(self, g):
        should_walk = False
        if self.stood_on_ground_previous_frame:
            if self.walks_on_ground:
                should_walk = True

            self.wait_timer += g.frame_time
            if self.wait_timer >= self.wait_time:
                # jump
                self.y_vel = -0.5
                self.wait_timer = 0
        elif self.walks_in_air:
            should_walk = True

        if should_walk:
            self.x_vel += self.x_dir * self.x_speed
            self.x += self.x_vel * g.frame_time
            self.x_vel = 0

        self.y_vel += self.y_speed
        self.y += self.y_vel * g.frame_time
class JumpThrowEnemy(SelfSovereignBeing): # Throws axes
    def __init__(self, x, y):
        super().__init__(x, y, 20, 30, 0.075, 0.01, True, (0,255,255), True)
        self.mode = 0
        self.timer = 0
        self.time = 1000
        self.has_thrown = False

    def logic_movement(self, g):
        self.timer += g.frame_time
        if self.mode == 0: # walk around

            if random.uniform(0,1) < 0.0005 * g.frame_time:
                self.x_dir *= -1
            
            if self.timer > self.time:
                self.mode = 1
                self.timer = 0
                self.y_vel -= 0.3
        elif self.mode == 1: # jump and throw
            if self.y_vel > 0 and not self.has_thrown:
                # throw
                g.objects_to_add.append(Axe(self.x+self.width/2,self.y, g.player.x-self.x))
                self.has_thrown = True
            if self.stood_on_ground_previous_frame:
                self.mode = 0
                self.timer = 0
                self.has_thrown = False
        self.x_vel += self.x_dir * self.x_speed * (0 if self.mode == 1 else 1)
        self.x += self.x_vel * g.frame_time
        self.x_vel = 0

        self.y_vel += self.y_speed
        self.y += self.y_vel * g.frame_time
class FlyingEnemy(SelfSovereignBeing):
    def __init__(self, x, y, speed, f_range, throws):
        super().__init__(x, y, 25,35, 0, 0, False, (100,0,200),True)
        self.timer = 0
        self.speed = (1 + speed)
        self.range = (1 + f_range)
        self.throws = throws
        if throws:
            self.throw_time = 2000
            self.throw_timer = 0

    def logic_movement(self, g): # flying logic
        self.timer += g.frame_time
        self.y_vel = math.cos((self.speed*self.timer)/1000) * self.range
        self.y += self.y_vel
        self.x += self.x_vel
        self.x_vel = 0

        if self.throws: # throw logic
            self.throw_timer += g.frame_time
            if self.throw_timer > self.throw_time:
                self.throw_timer = 0
                g.objects_to_add.append(Axe(self.x+self.width/2,self.y, g.player.x-self.x))

class Axe(SelfSovereignBeing):
    def __init__(self, x, y, x_distance_to_player):
        max_x_speed = 0.5
        x_speed = max(-max_x_speed, min(max_x_speed, -x_distance_to_player/700))
        super().__init__(x, y, 15, 15, x_speed, 0.01, False, (255,100,0), False)
        self.y_vel = -0.1

    def logic(self, g):
        self.logic_movement(g)
        self.remove_self_if_under_camera(g)

class Mushroom(SelfSovereignBeing):
    def __init__(self, x, y):
        super().__init__(x, y, MUSHROOM_WIDTH, MUSHROOM_HEIGHT, 0.11, 0.01, False, MUSHROOM_COLOR) # walks of edges
        self.x_dir = 1
    def logic(self, g):
        super().logic(g)
        self.remove_self_if_under_camera(g)

class CollisionRect:
    def __init__(self, x, y, width, height, color=(50,50,50)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
    def logic(self, g):
        pass
    def got_hit(self, g): # played jumped up into self
        print("bruh")
    def draw(self, g):
        x, y = g.camera.translate_position(self.x, self.y)
        pygame.draw.rect(g.screen, self.color, (int(x),int(y),int(self.width),int(self.height)))
        pygame.draw.rect(g.screen, (0,0,0), (int(x),int(y),int(self.width),int(self.height)),1)
class Cloud:
    def __init__(self, g):
        self.x = g.camera.x + g.width * random.uniform(1,1.25)
        self.y = g.camera.y + g.height * random.uniform(-0.25,1.25)
        self.width = g.width * random.uniform(0.2, 0.8)
        self.height = g.height * random.uniform(0.2, 0.5)
        self.x_vel = -random.uniform(0.1,0.2)
        self.y_vel = random.uniform(-0.01,0.01)
        self.color = (127,127,127)
    def logic(self, g):
        self.x += self.x_vel * g.frame_time
        self.y += self.y_vel * g.frame_time
        if self.x + g.width < g.camera.x:
            g.objects_to_remove.append(self)
    def draw(self, g):
        x, y = g.camera.translate_position(self.x, self.y)

        s = pygame.Surface((int(self.width),int(self.height)))
        s.set_alpha(50)
        s.fill(self.color)
        g.screen.blit(s, (int(x),int(y)))
class Pipe(CollisionRect):
    def __init__(self, x, y, width, height, color_value, teleport_pos):
        color = (0,0,0)
        if color_value == 0: color = (0,0,255)
        elif color_value == 1: color = (0,255,0)
        elif color_value == 2: color = (255,0,0)
        else: color == (255,255,0)
        super().__init__(x, y, width, height, color)

        self.teleport_pos = teleport_pos

    def draw(self, g):
        x, y = g.camera.translate_position(self.x, self.y)
        pygame.draw.rect(g.screen, self.color, (int(x),int(y),int(self.width),int(self.height)))
        pygame.draw.rect(g.screen, (0,0,0), (int(x),int(y),int(self.width),int(self.height)),1)

        y_ = int(y+g.camera.grid_size*0.75)
        pygame.draw.line(g.screen, (0,0,0), (int(x), y_),(int(x+self.width),y_), 2)

class ClimbingRect(CollisionRect):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, (20,150,20))

    def draw(self, g):
        x, y = g.camera.translate_position(self.x, self.y)

        s = pygame.Surface((int(self.width),int(self.height)))
        s.set_alpha(100)
        s.fill(self.color)
        g.screen.blit(s, (int(x),int(y)))    


class MovingCollisionRect(CollisionRect):
    def __init__(self, start_pos, end_pos, width, height, speed=0.1, color=(50,100,100)):
        super().__init__(start_pos[0],start_pos[1],width,height,color)
        self.start_pos = start_pos
        self.end_pos = end_pos

        self.x_distance = self.end_pos[0] - self.start_pos[0]
        self.y_distance = self.end_pos[1] - self.start_pos[1]
        self.distance = math.sqrt(self.x_distance*self.x_distance + self.y_distance*self.y_distance)
        self.x_normalized = self.x_distance/self.distance
        self.y_normalized = self.y_distance/self.distance

        self.speed = speed
        self.x_vel = 0
        self.y_vel = 0

        self.way = 1 # 1 == to end, -1 == to start

    def logic(self, g):
        self.x_vel = self.x_normalized * self.speed * self.way 
        self.y_vel = self.y_normalized * self.speed * self.way 
        self.x += self.x_vel * g.frame_time
        self.y += self.y_vel * g.frame_time

        # is x or y more than it should
        pos = self.end_pos if self.way == 1 else self.start_pos
        x_dif = pos[0] - self.x
        x_sign = 1 if self.x_distance > 0 else -1
        
        y_dif = pos[1] - self.y
        y_sign = 1 if self.y_distance > 0 else -1
        if x_dif * x_sign * self.way <= 0 and y_dif * y_sign * self.way <= 0:
            # over
            self.way *= -1
class ItemizedCollisionRect(CollisionRect):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, (255,255,0))
        self.items = 1
    def got_hit(self, g):
        if self.items > 0 :
            print("ITEM GOT")
            g.objects_to_add.append(AnimationMushroom((self.x+self.width/2-MUSHROOM_WIDTH/2,self.y),MUSHROOM_WIDTH, MUSHROOM_HEIGHT, MUSHROOM_COLOR))
            self.items -= 1
            if self.items == 0:
                self.color = (189, 113, 28)

class AnimationMushroom(MovingCollisionRect):
    def __init__(self, start_pos, width, height, color):
        end_pos = (start_pos[0], start_pos[1] - height)

        super().__init__(start_pos,end_pos,width,height,0.025,color)
    def logic(self, g):
        super().logic(g)
        if self.way == -1: # done
            g.objects_to_remove.append(self)
            g.objects_to_add.append(Mushroom(self.x,self.y))

ANIMATION_PLAYER_PIPE_IN, ANIMATION_PLAYER_PIPE_OUT = range(2)
class AnimationPlayerInPipe(MovingCollisionRect): # in game.objects.animations, also in GameStoppingAnimationPlayerInPipe.animation
    def __init__(self, start_pos, player, a_type): # a_type == animation_type
        end_pos = (start_pos[0], start_pos[1] + player.height)
        if a_type == ANIMATION_PLAYER_PIPE_OUT:
            start_pos, end_pos = end_pos, start_pos

        super().__init__(start_pos,end_pos,player.width,player.height,0.025,player.color)
        self.alive = True
    def logic(self, g):
        if self.alive:
            super().logic(g)
            if self.way == -1: # done
                g.objects_to_remove.append(self)
                self.alive = False

GS_ANIMATION_PLAYER_GET_SMALLER, GS_ANIMATION_PLAYER_GET_BIGGER, GS_ANIMATION_PLAYER_DIES = range(3)
class GameStoppingAnimation:
    def __init__(self, animation):
        self.animation = animation
        self.timer = 0
    def logic(self, g):
        
        if self.animation == GS_ANIMATION_PLAYER_GET_BIGGER:
            increase = 0.03 * g.frame_time
            g.player.height += increase
            g.player.y -= increase
            if g.player.height >= PLAYER_BIG_HEIGHT:
                g.player.height = PLAYER_BIG_HEIGHT
                g.game_stopping_animation = None

        elif self.animation == GS_ANIMATION_PLAYER_GET_SMALLER:
            decrease = 0.03 * g.frame_time
            g.player.height -= decrease
            g.player.y += decrease
            if g.player.height <= PLAYER_SMALL_HEIGHT:
                g.player.height = PLAYER_SMALL_HEIGHT
                g.game_stopping_animation = None

        elif self.animation == GS_ANIMATION_PLAYER_DIES:
            for obj in g.particles:
                obj.logic(g)
            if self.timer == 0: # create particles
                for _ in range(100):
                    g.objects_to_add.append(Particle(g.player.x,g.player.y,PLAYER_WIDTH,PLAYER_SMALL_HEIGHT,(0,0,0),1))
                g.player.visible = False
            if self.timer > 1000:
                g.player.set_position_to(g.player.respawn_point[0], g.player.respawn_point[1])
                g.camera.play_logic(g)
            if self.timer > 2000:
                g.player.visible = True
                g.player.respawn(g)
                g.game_stopping_animation = None
            
        else:
            print("ERROR, no such animation")

        self.timer += g.frame_time
class GameStoppingAnimationPlayerInPipe:
    def __init__(self, g, teleport_pos):
        self.timer = 0
        self.teleport_pos = teleport_pos
        self.mode = 0 # 0 == into pipe, 1 == out of pipe
        g.objects_to_add.append(AnimationPlayerInPipe((g.player.x,g.player.y),g.player, ANIMATION_PLAYER_PIPE_IN))
        self.animation = g.objects_to_add[-1]
        g.player.visible = False

    def logic(self, g):
        if self.mode == 0:
            self.animation.logic(g)

            if self.timer > 1000:
                self.mode = 1
                g.camera.teleport_to((self.teleport_pos[0]-g.width/2,self.teleport_pos[1]-g.height/2))
                g.objects_to_add.append(AnimationPlayerInPipe((self.teleport_pos[0]-g.player.width/2,self.teleport_pos[1]-g.player.height), g.player, ANIMATION_PLAYER_PIPE_OUT))
                self.animation = g.objects_to_add[-1]
                
                self.timer = 0

        elif self.mode == 1:
            self.animation.logic(g)
            if self.timer > 1000:
                g.player.x = self.animation.x
                g.player.y = self.animation.y
                g.player.visible = True
                g.game_stopping_animation = None

        self.timer += g.frame_time
class GameStoppingAnimationPlayerWinsLevel:
    def __init__(self, g):
        self.timer = 0
    def logic(self, g):

        for obj in g.flags + g.particles:
            obj.logic(g)
        g.player.logic(g)
        self.timer += g.frame_time
        if self.timer > 6000:
            # next level
            g.load_new_level(1)
            

class Particle(SelfSovereignBeing):
    def __init__(self, x, y, width, height, color=(0,0,0), thickness=1):
        
        width = random.randint(int(width*0.5), int(width*0.75))
        height = random.randint(int(height*0.5), int(height*0.75))

        speed = random.uniform(0.2,1)
        angle = random.uniform(0, 2*math.pi)
        x_speed = math.cos(angle) * speed
        
        super().__init__(x, y, width, height, x_speed, 0.01, False, color, False)

        self.y_vel = math.sin(angle) * speed
        self.thickness = thickness

    def logic(self, g):
        self.logic_movement(g)
        self.remove_self_if_under_camera(g)
        
    def draw(self, g):
        x, y = g.camera.translate_position(self.x, self.y)
        pygame.draw.rect(g.screen, self.color, (int(x),int(y),int(self.width),int(self.height)), self.thickness)
class Coin:
    def __init__(self, g, x, y):
        self.x = x + g.camera.grid_size/2
        self.y = y + g.camera.grid_size/2
        self.radius = int(g.camera.grid_size/2)
        self.color = (255,255,51)
    def draw(self, g):
        x, y = g.camera.translate_position(self.x, self.y)
        pygame.draw.circle(g.screen, self.color, (int(x),int(y)),self.radius)
        #pygame.draw.circle(g.screen, (200,200,200), (int(x),int(y)), self.radius,1)
    def got_picked_up(self, g):
        for _ in range(18):
            g.objects_to_add.append(Particle(self.x,self.y,self.radius,self.radius,self.color,3))
        g.objects_to_remove.append(self)
        g.player.coins += 1

class Flag:
    def __init__(self, g, x, y, length, flag_width, flag_height):
        self.x = x
        self.y = y
        self.length = length

        self.flag_width = flag_width
        self.flag_height = flag_height
        self.flag_raisedness = 0
        self.flag_raise_velocity = 1

        self.color = (42, 196, 76)
        
        self.mode = 0# 0 = not getting raised, 1 = getting raised, 2 = already raised
    def logic(self, g):
        if self.mode == 1:
            self.flag_raisedness += self.flag_raise_velocity*(math.sin(g.frame_time*0.05)+0.01)
            if self.flag_raisedness >= self.length - self.flag_height:
                self.mode = 2
                self.particle_effect(g)
    def get_raised(self, g):
        if self.mode == 0:
            self.mode = 1
    def particle_effect(self, g):
        for _ in range(100):
            g.objects_to_add.append(Particle(self.x,self.y-self.length,1,1,self.color,2))
    def draw(self, g):
        x, y  = g.camera.translate_position(self.x, self.y)

        # flag rect
        y_ = int(y-self.flag_height-self.flag_raisedness)
        pygame.draw.rect(g.screen, self.color, (int(x),y_,self.flag_width,self.flag_height))

        # flag pole
        pygame.draw.line(g.screen, (0,0,0), (int(x), int(y)), (int(x),int(y-self.length)), 2)
class RespawnFlag(Flag): # goes up from x,y to length
    def __init__(self, g, x, y):
        super().__init__(g, x, y + g.camera.grid_size, g.camera.grid_size * 2.5, 40, 28)
class WinFlag(Flag):
    def __init__(self, g, x, y):
        super().__init__(g, x, y + g.camera.grid_size, g.camera.grid_size * 7.5, 80, 57)
    def get_raised(self, g):
        if self.mode == 0:
            self.mode = 1
            g.game_stopping_animation = GameStoppingAnimationPlayerWinsLevel(g)
    def particle_effect(self, g):
        for _ in range(200):
            g.objects_to_add.append(Particle(self.x,self.y-self.length,10,10,self.color,5))
def main():
    pygame.init()
    Game()
    pygame.quit()

if __name__ == "__main__":
    main()