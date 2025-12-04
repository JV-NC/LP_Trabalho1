# title:   LP_Trabalho1
# author:  Alexandre, Jean, Joao Vitor, Julia
# desc:    trabalho de LP
# license: MIT License
# version: 0.1
# script:  python

#TODO: implement attacking sprites states
#TODO: implement player physical attack and projectile upgrade
#TODO: implement 2 enemies structure type and 1 boss
#TODO: draw better menu and gameover screen
#TODO: refactor patrol enemy for patrol coordinates
#TODO: fix interactables for working as chest and doors with keys
#TODO: implement drop and collect keys

class Player:
    def __init__(self, x, y):
        # location
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        
        self.friction = 0.1
        self.max_vx = 3
        self.gspeed = 0.5
        self.aspeed = 0.5
        self.dir = 0   # 0 right / 1 left

        # physics
        self.gravity = 0.4
        self.jump_force = -4
        self.jump_boost = -0.4
        self.max_jump_time = 12
        self.jump_timer = 0
        self.on_ground = False

        # animation
        self.w = 16
        self.h = 16
        self.animations = {
            'idle': {'start': 256, 'frames': 2, 'speed': 30},
            'run':  {'start': 260, 'frames': 2, 'speed': 12},
            'jump': {'start': 264, 'frames': 1, 'speed': 1},
            'fall': {'start': 266, 'frames': 1, 'speed': 1},
            'sleep': {'start': 288, 'frames': 2, 'speed': 30},
            'interact': {'start': 268, 'frames': 1, 'speed': 1},
            'attack': {'start': 270, 'frames': 1, 'speed': 1}
        }
        self.state = 'idle'
        self.frame = 0
        self.t = 0
        self.flipper = 0
        self.flipper_speed = 4
        self.flipper_t = 0
        self.sleep_timer = 0
        self.sleep_time = 180

        #interact
        self.interact_timer = 0
        self.interact_duration = 10
        self.can_move = True

    # HORIZONTAL MOVEMENT AND SIDE COLLISION
    def move_horizontal(self):
        old_x = self.x
        self.x += self.vx

        # clamp speed
        if self.vx > self.max_vx: self.vx = self.max_vx
        if self.vx < -self.max_vx: self.vx = -self.max_vx

        # input
        speed = self.gspeed if self.on_ground else self.aspeed
        if btn(2) or key(1):   # left
            self.vx -= speed
            self.dir = 1
        elif btn(3) or key(4): # right
            self.vx += speed
            self.dir = 0
        else:
            if abs(self.vx) < self.friction:
                self.vx = 0
            elif self.vx > 0:
                self.vx -= self.friction
            elif self.vx < 0:
                self.vx += self.friction

        # side collision
        left = int(self.x)
        right = int(self.x + self.w -1)
        top = int(self.y)
        bottom = int(self.y + self.h -1)

        if self.vx < 0:  # left
            if solid_tile_at(left, top) or solid_tile_at(left, bottom):
                self.x = old_x
                self.vx = 0

        if self.vx > 0:  # right
            if solid_tile_at(right, top) or solid_tile_at(right, bottom):
                self.x = old_x
                self.vx = 0

    # GRAVITY AND VERTICAL COLLISION
    def apply_gravity(self):
        self.vy += self.gravity
        if self.vy > 3:
            self.vy = 3

        self.y += self.vy

        ix = int(self.x)
        iy = int(self.y)

        HIT_L = 3
        HIT_R = 3
        HIT_T = 2
        HIT_B = 2

        left = ix + HIT_L
        right = ix + self.w - HIT_R
        top = iy + HIT_T
        bottom = iy + self.h - HIT_B

        # FLOOR COLLISION
        if self.vy >= 0:
            foot_y = iy + self.h
            foot_tile_y = foot_y // 8

            left_tile_x = (ix + 2) // 8
            right_tile_x = (ix + self.w - 3) // 8

            on_floor = (solid_tile_at(left_tile_x * 8, foot_tile_y * 8) or solid_tile_at(right_tile_x * 8, foot_tile_y * 8))

            if on_floor:
                tile_top = foot_tile_y * 8
                self.y = tile_top - self.h
                self.vy = 0
                self.on_ground = True
            else:
                self.on_ground = False

        # CEILING COLLISION
        if self.vy < 0:
            hit_ceiling = (solid_tile_at(left, top) or solid_tile_at(right, top))

            if hit_ceiling:
                tile_bottom = ((top // 8) + 1) * 8
                self.y = tile_bottom
                self.vy = 0

    # JUMP SYSTEM
    def jump(self):
        jump_pressed = btn(4) or key(23) or key(48)
        jump_just_pressed = btnp(4) or key(23) or key(48)

        if jump_just_pressed and self.on_ground:
            self.vy = self.jump_force
            self.on_ground = False
            self.jump_timer = 0

        if jump_pressed and not self.on_ground and self.vy < 0:
            if self.jump_timer < self.max_jump_time:
                self.vy += self.jump_boost
                self.jump_timer += 1

    # MOVE
    def move(self):
        if self.interact_timer>0:
            self.interact_timer-=1
            if self.interact_timer ==0:
                self.can_move = True
            return
        
        if not self.can_move:
            return
        
        self.move_horizontal()
        self.apply_gravity()
        self.jump()

    # INTERACT
    def try_interact(self,interactibles):
        if self.interact_timer>0 or not self.on_ground:
            return

        if not (btnp(7) or key(5)): #'E' or button 'Y'
            return
        
        self.interact_timer = self.interact_duration
        self.can_move = False
        self.state = 'interact'
        self.frame = 0
        self.t = 0

        # procurar interagível em colisão
        for obj in interactibles:
            if obj.check_collision(self):
                # checa requisito (se tiver)
                if obj.req is None or obj.req(self):
                    obj.trigger(self)
                return

    # STATE MACHINE
    def set_state(self):
        old = self.state

        if self.interact_timer>0:
            self.state = 'interact'
            return

        if not self.on_ground:
            if self.vy < 0:
                self.state = 'jump'
            elif self.vy > 0.1:
                self.state = 'fall'
        else:
            if abs(self.vx) > 1.0:
                self.state = 'run'
            else:
                if self.sleep_timer>=self.sleep_time:
                    self.state = 'sleep'
                else:
                    self.state = 'idle'
                    self.sleep_timer+=1
                
        if self.state not in ('idle','sleep'):
            self.sleep_timer=0

        if old != self.state:
            self.frame = 0
            self.t = 0

    # ANIMATION CONTROL
    def animate(self):
        anim = self.animations[self.state]

        if anim['frames'] <= 1:
            self.frame = 0
            self.t = 0
            return

        self.t += 1
        speed = max(1, anim['speed'])
        #trace(f'Timer: {self.t}; Frame: {self.frame}; State: {self.state}')
        if self.t >= speed:
            self.frame = (self.frame + 1) % anim['frames']
            self.t = 0

    # DRAW PLAYER
    def draw(self, cam_x, cam_y):
        anim = self.animations[self.state]
        sprite_id = anim['start'] + self.frame * 2
        if not self.on_ground:
          self.flipper_t += 1
          if self.flipper_t >= self.flipper_speed:
            self.flipper = (self.flipper + 1) % 4
            self.flipper_t = 0
        else:
          self.flipper = 0
          self.flipper_t = 0
        spr(
            sprite_id,
            int(self.x - cam_x),
            int(self.y - cam_y),
            colorkey=0,
            scale=1,
            flip=self.dir,
            rotate=0,
            w=2,
            h=2
        )

    # Gather all update methods
    def update(self, cam_x, cam_y):
        self.move()
        self.set_state()
        self.animate()
        self.draw(cam_x, cam_y)

# INTERACTABLE
class Interactable:
    def __init__(self, x, y, w, h, trigger, req=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.trigger = trigger   # função a ser chamada
        self.req = req           # requisito opcional (ex: chave)
    
    def check_collision(self, player):
        return (self.x < player.x + player.w and self.x + self.w > player.x and self.y < player.y + player.h and self.y + self.h > player.y)

# ---------- INIMIGOS ----------

class Patrulha:
    def __init__(self, x, y, sprite_base):
        self.x = x
        self.y = y
        self.vx = 1
        self.w = 8
        self.h = 8
        self.sprite_base = sprite_base
        self.frame = 0
        self.frame_max = 2
        self.anim_speed = 15
        self.t = 0

        # física vertical
        self.vy = 0
        self.gravity = 0.4
        self.on_ground = False

        # patrulha limitada
        self.patrol_range = 105  # distância máxima do player
        self.direction = 1      # direção inicial

    def move(self, player):
        old_x = self.x

        # calcula distância pro player
        distance_to_player = player.x - self.x

        # inverte direção se estiver longe do player
        if abs(distance_to_player) > self.patrol_range:
            self.direction *= -1

        self.vx = self.direction

        # checa se tem chão à frente
        front_x = self.x + (self.vx > 0) * self.w
        front_y = self.y + self.h
        if not solid_tile_at(front_x, front_y + 1):
            self.vx *= -1
            self.direction *= -1

        self.x += self.vx

        # colisão horizontal com paredes
        left = int(self.x)
        right = int(self.x + self.w - 1)
        top = int(self.y)
        bottom = int(self.y + self.h - 1)

        if self.vx > 0:
            if solid_tile_at(right, top) or solid_tile_at(right, bottom):
                self.x = old_x
                self.vx *= -1
                self.direction *= -1
        elif self.vx < 0:
            if solid_tile_at(left, top) or solid_tile_at(left, bottom):
                self.x = old_x
                self.vx *= -1
                self.direction *= -1

        # animação
        self.t += 1
        if self.t % self.anim_speed == 0:
            self.frame = (self.frame + 1) % self.frame_max

    def apply_gravity(self):
        self.vy += self.gravity
        if self.vy > 3:
            self.vy = 3

        self.y += self.vy

        left = int(self.x)
        right = int(self.x + self.w - 1)
        top = int(self.y)
        bottom = int(self.y + self.h - 1)

        # caindo
        if self.vy > 0:
            if solid_tile_at(left, bottom) or solid_tile_at(right, bottom):
                tile_y = bottom // 8
                self.y = tile_y * 8 - self.h
                self.vy = 0
                self.on_ground = True
            else:
                self.on_ground = False
        # subindo
        elif self.vy < 0:
            if solid_tile_at(left, top) or solid_tile_at(right, top):
                tile_y = top // 8 + 1
                self.y = tile_y * 8
                self.vy = 0

    def draw(self, cam_x, cam_y):
        spr(
            self.sprite_base + self.frame,
            int(self.x - cam_x),
            int(self.y - cam_y),
            colorkey=0,
            scale=1
        )

    def update(self, cam_x, cam_y, player):
        self.move(player)       # movimento horizontal limitado perto do player
        self.apply_gravity()    # física vertical
        self.draw(cam_x, cam_y)

    def check_collision_player(self, player):
        if self.x < player.x + player.w and self.x + self.w > player.x and self.y < player.y + player.h and self.y + self.h > player.y:
            return True
        return False

# ---------- MAPA ----------

# TILE SOLID CHECK
def solid_tile_at(px, py):
    tile_x = int(px) // 8
    tile_y = int(py) // 8
    tile_id = mget(tile_x, tile_y)
    return tile_id < 64

# CAMERA
def get_camera(player):
    CAMERA_Y_OFFSET = -36
    cam_x = round(player.x - 240//2)
    cam_y = round(player.y - 136//2 + CAMERA_Y_OFFSET)

    cam_x = max(0, min(cam_x, MAP_W - 240))
    cam_y = max(0, min(cam_y, MAP_H - 136))

    return int(cam_x), int(cam_y)

#Globals
player = Player(100, 60)

enemies = [
     Patrulha(200, 100, 348),
     Patrulha(300, 100, 348),
]

def porta_trigger(player):
    trace("Porta abriu!")

interactables = [
    Interactable(150, 80, 16, 16, porta_trigger),
]

GAME_STATE = "menu"
death_timer = 0

music_started = False

# ---------- GAME SCREENS ----------

def draw_menu():
    cls()
    title = "TIC GAME"
    start = "PRESSIONE 'PULO' PARA JOGAR"

    # centraliza automaticamente
    print(title, 240//2 - (len(title)*4)//2, 40, 15, False, 2)
    print(start, 240//2 - (len(start)*4)//2, 80, 12, False, 1)

def draw_game_over():
    cls()
    msg = "VOCE MORREU!"
    retry = "PRESSIONE 'E' PARA RECOMEÇAR"

    print(msg, 240//2 - (len(msg)*4)//2, 40, 14, False, 2)
    print(retry, 240//2 - (len(retry)*4)//2, 80, 12, False, 1)

TILE_SIZE = 8
MAP_W_TILES = 120
MAP_H_TILES = 120
MAP_W = MAP_W_TILES * TILE_SIZE
MAP_H = MAP_H_TILES * TILE_SIZE
W = 240
H = 136
T = 8

def TIC():
    global player, GAME_STATE, death_timer, music_started, interactables

    #music
    if not music_started:
        music(0, loop=True)
        music_started = True

    if GAME_STATE == "menu":
        draw_menu()
        # SPACE = começar jogo
        if btn(4) or key(48):  # botão 'A' do TIC-80
            player = Player(100, 60)
            GAME_STATE = "game"
        return

    if GAME_STATE == "game":
        cls()

        cam_x, cam_y = get_camera(player)

        map(
            cam_x // T,
            cam_y // T,
            (W // T) + 1,
            (H // T) + 1,
            -(cam_x % T),
            -(cam_y % T)
        )
        #update player
        player.update(cam_x, cam_y)
        player.try_interact(interactables)

        #update enemy
        for enemy in enemies:
            enemy.update(cam_x, cam_y, player)
            if enemy.check_collision_player(player):
                GAME_STATE = "dead"
                death_timer = 20

        #fall from map
        if player.y > MAP_H:
            GAME_STATE = "dead"
            death_timer = 20

        return
    
    if GAME_STATE == "dead":
        draw_game_over()

        if death_timer > 0:
            death_timer -= 1
            return

        # E = volta ao menu
        if btnp(7) or key(5):
            GAME_STATE = "menu"
        return