# title:   LP_Trabalho1
# author:  Alexandre, Jean, Joao Vitor, Julia
# desc:    trabalho de LP
# site:    website link
# license: MIT License (change this to your license of choice)
# version: 0.1
# script:  python


SFX_JUMP = 4
SFX_JUMP_BOOST = 1
SFX_LAND = 5

music_started = False

GAME_STATE = "menu"
death_timer = 0



class Player:
    def __init__(self, x, y, sprite_base):

        # --- Jump helpers ---
        self.coyote_time = 6
        self.coyote_counter = 0

        self.jump_buffer = 6
        self.jump_buffer_counter = 0

        # location
        self.x = x
        self.y = y
        self.vx = 0
        self.friction = 0.1
        self.max_vx = 3
        self.gspeed = 0.1
        self.aspeed = 0.1
        self.dir = 0

        # physics
        self.vy = 0
        self.gravity = 0.4
        self.jump_force = -4
        self.jump_boost = -0.4
        self.max_jump_time = 12
        self.jump_timer = 0
        self.on_ground = False

        # animation
        self.sprite_base = sprite_base
        self.w = 8
        self.h = 8
        self.frame = 0
        self.frame_max = 4
        self.anim_speed = 8
        self.t = 0
        self.flipper = 0
        self.flipper_speed = 4
        self.flipper_t = 0

    def move_horizontal(self):

        old_x = self.x
        self.x += self.vx

        # clamp velocidade
        if self.vx > self.max_vx:
            self.vx = self.max_vx
        elif self.vx < -self.max_vx:
            self.vx = -self.max_vx

        moving = False
        speed = self.gspeed if self.on_ground else self.aspeed

        # esquerda
        if btn(2) or key(1):
            self.vx -= speed
            self.dir = 1
            moving = True

        # direita
        elif btn(3) or key(4):
            self.vx += speed
            self.dir = 0
            moving = True

        # desaceleração
        else:
            if abs(self.vx) > self.friction:
                self.vx = 0
            if self.vx > 0:
                self.vx -= self.friction
            elif self.vx < 0:
                self.vx += self.friction

        # colisão horizontal
        left = self.x
        right = self.x + self.w - 1
        top = self.y
        bottom = self.y + self.h - 1

        if self.vx < 0:
            if solid_tile_at(left, top) or solid_tile_at(left, bottom):
                self.x = old_x
                self.vx = 0

        if self.vx > 0:
            if solid_tile_at(right, top) or solid_tile_at(right, bottom):
                self.x = old_x
                self.vx = 0

        # animação
        if moving:
            self.t += 1
            if self.t % self.anim_speed == 0:
                self.frame = (self.frame + 1) % self.frame_max
        else:
            self.frame = 0

    def apply_gravity(self):

        self.vy += self.gravity
        if self.vy > 3:
            self.vy = 3

        self.y += self.vy

        left = int(self.x)
        right = int(self.x + self.w - 1)
        top = int(self.y)
        bottom = int(self.y + self.h - 1)

        was_on_ground = self.on_ground  # <-- importante

        # --- caindo ---
        if self.vy > 0:
            if solid_tile_at(left, bottom) or solid_tile_at(right, bottom):

               # if not was_on_ground:
                #    sfx(SFX_LAND)

                tile_y = bottom // 8
                self.y = tile_y * 8 - self.h
                
                self.vy = 0
                self.on_ground = True

            else:
                self.on_ground = False

        # --- subindo ---
        elif self.vy < 0:
            if solid_tile_at(left, top) or solid_tile_at(right, top):
                tile_y = top // 8 + 1
                self.y = tile_y * 8
                self.vy = 0

    def jump(self):

        jump_pressed = btn(4) or key(23) or key(48)
        jump_just_pressed = btnp(4) or keyp(23) or keyp(48)

        # --- jump buffer ---
        if jump_just_pressed:
            self.jump_buffer_counter = self.jump_buffer
        else:
            if self.jump_buffer_counter > 0:
                self.jump_buffer_counter -= 1

        # --- coyote time ---
        if self.on_ground:
            self.coyote_counter = self.coyote_time
        else:
            if self.coyote_counter > 0:
                self.coyote_counter -= 1

        can_jump = (self.coyote_counter > 0)
        buffered = (self.jump_buffer_counter > 0)

        # --- pulo normal ---
        if buffered and can_jump:
            self.vy = self.jump_force
            self.on_ground = False
            self.jump_timer = 0
            self.jump_buffer_counter = 0
            sfx(SFX_JUMP)

        # --- pulo prolongado (segurar pra subir mais) ---
        if jump_pressed and not self.on_ground and self.vy < 0:
            if self.jump_timer < self.max_jump_time:
                self.vy += self.jump_boost
                self.jump_timer += 1

    def move(self):
        self.move_horizontal()
        self.apply_gravity()
        self.jump()

    def draw(self, cam_x, cam_y):

        sprite_id = self.sprite_base + self.frame

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
            rotate=self.flipper
        )

    def update(self, cam_x, cam_y):
        self.move()
        self.draw(cam_x, cam_y)


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

def solid_tile_at(px, py):
    tile_x = int(px) // 8
    tile_y = int(py) // 8
    tile_id = mget(tile_x, tile_y)
    return tile_id < 64

def get_camera(player):
    cam_x = int(player.x - 240 // 2)
    cam_y = int(player.y - 136 // 2)

    cam_x = max(0, min(cam_x, MAP_W - 240))
    cam_y = max(0, min(cam_y, MAP_H - 136))
    return cam_x, cam_y


player = Player(100, 60, 256)

enemies = [
     Patrulha(200, 100, 272),
     Patrulha(300, 100, 272),
]

TILE_SIZE = 8
MAP_W_TILES = 120
MAP_H_TILES = 30
MAP_W = MAP_W_TILES * TILE_SIZE
MAP_H = MAP_H_TILES * TILE_SIZE

def draw_menu():
    cls()
    title = "TIC GAME"
    start = "PRESSIONE D PARA JOGAR"

    # centraliza automaticamente
    print(title, 240//2 - (len(title)*4)//2, 40, 15, False, 2)
    print(start, 240//2 - (len(start)*4)//2, 80, 12, False, 1)

def draw_game_over():
    cls()
    msg = "VOCE MORREU!"
    retry = "PRESSIONE X PARA RECOMEÇAR"

    print(msg, 240//2 - (len(msg)*4)//2, 40, 14, False, 2)
    print(retry, 240//2 - (len(retry)*4)//2, 80, 12, False, 1)


def TIC():
    global player, music_started, GAME_STATE, death_timer

    # --- música ---
    if not music_started:
        music(0, loop=True)
        music_started = True

    # -------------------------
    # ESTADO: MENU
    # -------------------------
    if GAME_STATE == "menu":
        draw_menu()
        # D = começar jogo
        if btn(3) or key(4):  # botão X do TIC-80
            player = Player(100, 60, 256)
            GAME_STATE = "game"
        return

    # -------------------------
    # ESTADO: GAMEPLAY
    # -------------------------
    if GAME_STATE == "game":
        cls()

        # câmera
        cam_x, cam_y = get_camera(player)

        # desenhar mapa
        map(
            cam_x // TILE_SIZE,
            cam_y // TILE_SIZE,
            30,
            20,
            -(cam_x % TILE_SIZE),
            -(cam_y % TILE_SIZE)
        )

        # atualizar jogador
        player.update(cam_x, cam_y)

        # atualizar inimigos
        for enemy in enemies:
            enemy.update(cam_x, cam_y, player)
            if enemy.check_collision_player(player):
                GAME_STATE = "dead"
                death_timer = 20

        # morte: cair fora do mapa
        if player.y > MAP_H:
            GAME_STATE = "dead"
            death_timer = 20

        return

    # -------------------------
    # ESTADO: GAME OVER
    # -------------------------
    if GAME_STATE == "dead":
        draw_game_over()

        if death_timer > 0:
            death_timer -= 1
            return

        # X = volta ao menu
        if btnp(4):
            GAME_STATE = "menu"
        return


