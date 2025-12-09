# title:   LP_Trabalho1
# author:  Alexandre, Jean, Joao Vitor, Julia
# desc:    trabalho de LP
# license: MIT License
# version: 0.1
# script:  python

#TODO: implement Ghost Stalker
#TODO: implement 2 enemies structure type and 1 boss
#TODO: draw better menu and gameover screen
#TODO: fix interactables collision for enemies
#TODO: implement drop and collect keys
#TODO: test and try different attributes for player and enemies for better game pacing
#TODO: fix double jump attack rotation
#TODO: fix (or ignore) enemy flicking on_ground because of bad apply_gravity
#TODO: fix Patrol Enemy for 'real' patrol_range funcionality, if have time
#TODO: put doors and spawners
#TODO: create boss as shooter
#TODO: fix menu and gameover screen


import random
#RECOIL
def recoil(target, causer_x, causer_y, side_force=2,up_force=-2):
    tx = target.x + (getattr(target, "w") / 2)
    dx = tx - causer_x
    #if 0, push to right
    if dx == 0:
        dir_sign = 1 if getattr(target, "vx") >= 0 else -1
    else:
        dir_sign = 1 if dx > 0 else -1

    # Apply horizontal push
    target.vx += side_force * dir_sign

    # Aply vertical push upwards
    target.vy = up_force

#verify overlap
def aabb(a,b):
    return (a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y)

def collide_interactables(entity, interactables):
    for obj in interactables:
        if obj.solid:
            if (entity.x < obj.x + obj.w and entity.x + entity.w > obj.x and entity.y < obj.y + obj.h and entity.y + entity.h > obj.y):
                return True
    return False

class Player:
    def __init__(self, x, y):
        #location
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        
        self.friction = 0.1
        self.max_vx = 3
        self.gspeed = 0.5
        self.aspeed = 0.5
        self.dir = 0   # 0 right / 1 left

        #physics
        self.gravity = 0.4
        self.max_gravity = 3
        self.jump_force = -4
        self.jump_boost = -0.4
        self.max_jump_time = 12
        self.jump_timer = 0
        self.on_ground = False

        #double jump
        self.double_jump_unlocked = True
        self.djump_force = -3
        self.djump_boost = -0.4
        self.max_djump_time = 12
        self.djump_timer = 0
        self.djump_used = False
        self.jump_released = True
        self.max_vertical_speed_djump = 2.0

        #take damage
        self.max_hp = 3
        self.hp = self.max_hp
        self.invincible_timer = 0
        self.invincible_duration = 30

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
        self.interact_duration = 12
        self.can_move = True
        self.door_keys = 1
        self.chest_keys = 1

        #attack
        self.attack_timer = 0
        self.attack_duration = 12
        self.attack_sprite = 298
        self.attack_w = 16
        self.attack_h = 16
        self.attacking_in_air = False
        self.attacking_on_ground = False
        self.attack_cooldown = 0
        self.attack_cooldown_max = self.attack_duration + 20
        self.attack_dir = 'side'

        #projectile
        self.shoot_unlocked = True
        self.shoot_timer = 0
        self.shoot_duration = 12
        self.shoot_sprite = 302
        self.shoot_w = 8
        self.shoot_h = 8
        self.shoot_cooldown = 0
        self.shoot_cooldown_max = self.attack_duration + 40
        self.shoot_speed = 4
        self.shoot_distance = 80
        self.rotation_time=0
        self.projectile_damage = 2

    def collide_interactables_horizontal(self, interactables):
        for obj in interactables:
            if not obj.solid:
                continue
            if not aabb(self, obj):
                continue

            # Ignorar colisão horizontal se o player está em cima do objeto
            player_bottom = self.y + self.h
            obj_top = obj.y
            if abs(player_bottom - obj_top) <= 1:
                continue  # player está apoiado no topo, não empurra lateralmente

            # Colisão horizontal normal
            if self.vx > 0:  # moveu para a direita
                self.x = obj.x - self.w
                self.vx = 0
            elif self.vx < 0:  # moveu para a esquerda
                self.x = obj.x + obj.w
                self.vx = 0

    def collide_interactables_vertical(self, interactables):
        for obj in interactables:
            if not obj.solid:
                continue
            if not aabb(self, obj):
                continue

            # Apenas colisão ao cair sobre o objeto
            if self.vy > 0:
                self.y = obj.y - self.h
                self.vy = 0
                self.on_ground = True
                self.jump_timer = 0
                self.djump_timer = 0
                self.djump_used = False

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
        if self.vy > self.max_gravity:
            self.vy = self.max_gravity

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
                #landed resets jump states
                self.on_ground = True
                self.jump_timer = 0
                self.djump_timer = 0
                self.djump_used = False
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
        jump_pressed = btn(4) or key(48)
        jump_just_pressed = (jump_pressed and self.jump_released)

        #update button state
        if not jump_pressed:
            self.jump_released = True

        if jump_just_pressed:
            self.jump_released = False
            if self.on_ground:
                #normal jump from ground
                self.vy = self.jump_force
                self.on_ground = False
                self.jump_timer = 0
            else: #double jump
                if (self.double_jump_unlocked and not self.djump_used and abs(self.vy)<self.max_vertical_speed_djump):
                    self.vy = self.djump_force
                    self.djump_used = True
                    self.djump_timer = 0

        if jump_pressed and not self.on_ground and self.vy < 0:
            #jump from ground jump boost if not double jumped
            if self.jump_timer < self.max_jump_time and not self.djump_used:
                self.vy += self.jump_boost
                self.jump_timer += 1
            elif self.djump_used and self.djump_timer<self.max_djump_time:
                self.vy += self.djump_boost
                self.djump_timer +=1

    # MOVE
    def move(self):
        if self.attack_cooldown>0:
            self.attack_cooldown-=1

        if self.invincible_timer >0:
            self.invincible_timer-=1
        
        if self.interact_timer>0 and self.attack_timer==0:
            self.interact_timer-=1
            if self.interact_timer ==0:
                self.can_move = True
            return
        
        if self.attack_timer>0:
            self.attack_timer-=1
            if self.attacking_in_air:
                """if want lock on air
                self.vx = 0
                self.vy = 0
                if want pogo"""
                self.apply_gravity()
                self.move_horizontal()
                return
            
            if self.attacking_on_ground:
                self.vx = 0
                self.apply_gravity()
                return
        else:
            self.attacking_in_air = False
            self.attacking_on_ground = False
        
        if not self.can_move:
            return
        
        self.move_horizontal()
        self.apply_gravity()
        self.jump()

    def cheat_full_health(self):
        if key(8):
            self.hp = self.max_hp

    def cheat_more_health(self):
        if key(10):
            self.max_hp = 10
            self.hp = self.max_hp
    # TAKE DAMAGE
    def take_damage(self,amount,causer_x,causer_y,knockback=3, i_frames=None):
        if self.invincible_timer>0:
            return False
        
        #apply damage
        self.hp -= amount
        self.invincible_timer = self.invincible_duration if i_frames is None else i_frames

        recoil(self, causer_x, causer_y, side_force=knockback,up_force=-4)

        if self.hp<=0:
            global GAME_STATE,death_timer
            GAME_STATE = 'dead'
            death_timer = 20
        return True
        
    #CHECK ENEMIES PROJECTILES
    def check_player_projectile(self, player: Player, projectiles: list[Projectile]):
        for proj in list(projectiles):

            # ============================
            # 1) PROJÉTIL DO PLAYER → acerta INIMIGO
            # ============================
            if proj.owner == "player":
                if (
                    self.x < proj.x + proj.w and self.x + self.w > proj.x and self.y < proj.y + proj.h and self.y + self.h > proj.y
                ):
                    if self.invincible_timer > 0:
                        continue

                    # dano no inimigo
                    self.take_damage(proj.damage, source=player)

                    # stun + invencibilidade
                    self.stun_timer = self.stun_duration
                    self.invincible_timer = self.invincible_duration

                    # RECOIL correto
                    recoil(
                        self, proj.x, proj.y, side_force=self.side_force, up_force=-3
                    )

                    if proj in projectiles:
                        projectiles.remove(proj)
                    continue

            # ============================
            # 2) PROJÉTIL DO BOSS → acerta PLAYER
            # ============================
            if proj.owner == "boss":
                if (
                    player.x < proj.x + proj.w and player.x + player.w > proj.x and player.y < proj.y + proj.h and player.y + player.h > proj.y
                ):

                    if proj in projectiles:
                        projectiles.remove(proj)

                    player.take_damage(
                        proj.damage,
                        self.x,
                        self.y,
                        self.knockback
                    )
                    continue


    def check_hit_by_projectiles(self, projectiles):
        for proj in list(projectiles):

            # só projétil do boss bate no player
            if proj.owner != "boss":
                continue

            # colisão AABB
            if (
                self.x < proj.x + proj.w and self.x + self.w > proj.x and self.y < proj.y + proj.h and self.y + self.h > proj.y
            ):
                # remove o projétil
                if proj in projectiles:
                    projectiles.remove(proj)

                # aplica dano no player
                self.take_damage(
                    proj.damage,
                    proj.x,
                    proj.y,
                    knockback=6  # ou o valor que usa no seu jogo
                )
                return   # só 1 hit por frame para evitar bug


    # INTERACT
    def try_interact(self,interactibles):
        if self.interact_timer>0 or not self.on_ground:
            return

        if not key(5): #'E' or button 'Y'
            return
        
        self.interact_timer = self.interact_duration
        self.can_move = False
        self.state = 'interact'
        self.frame = 0
        self.t = 0

        # search for nearest interactable on players direction
        for obj in interactibles:
            if obj.check_interact_area(self):
                if obj.req is None or obj.req(self):
                    obj.trigger(self,obj)
                return

    def try_attack(self):
        if self.attack_timer>0 or self.attack_cooldown>0:
            return
        
        if not key(6): #'F' attacks
            return
        
        if btn(0) or key(23):
            self.attack_dir = 'up'
        elif (btn(1) or key(19)) and not self.on_ground:
            self.attack_dir = 'down'
        else:
            self.attack_dir = 'side'
        
        self.attack_timer = self.attack_duration
        self.state = 'attack'
        self.frame = 0
        self.t = 0
        self.attack_cooldown = self.attack_cooldown_max

        if not self.on_ground:
            self.attacking_in_air = True
            self.attacking_on_ground = False
        else:
            self.attacking_in_air = False
            self.attacking_on_ground = True

    def attack_hitbox(self):
        # Define hitbox depending of direction
        if self.attack_dir == 'up':
            atk_x = self.x + (self.w // 2 - self.attack_w // 2)
            atk_y = self.y - self.attack_h
            atk_w = self.attack_w
            atk_h = self.attack_h
        elif self.attack_dir == 'down':
            atk_x = self.x + (self.w // 2 - self.attack_w // 2)
            atk_y = self.y + self.h
            atk_w = self.attack_w
            atk_h = self.attack_h
        else:  # side attack
            if self.dir == 0:  # right
                atk_x = self.x + self.w
            else:  # left
                atk_x = self.x - self.attack_w
            atk_y = self.y + 2
            atk_w = self.attack_w
            atk_h = self.attack_h

        return atk_x, atk_y, atk_w, atk_h


    def try_shoot(self, projectiles:list):
        if not self.shoot_unlocked:
            return
        
        if self.shoot_timer>0:
            self.shoot_timer-=1

        if self.shoot_cooldown>0:
            self.shoot_cooldown-=1
            return
        
        if not key(17):
            return
        
        self.shoot_timer = self.shoot_duration
        self.shoot_cooldown = self.attack_cooldown_max

        #shoot starting point
        if self.dir==0:
            px = self.x+self.w
        else:
            px = self.x - self.shoot_w

        py = self.y+self.h//2 - self.shoot_h//2

        projectile = Projectile(px,py,self.dir,self.shoot_sprite,speed=self.shoot_speed,max_dist=self.shoot_distance,w=self.shoot_w,h=self.shoot_h,rotation_time=self.rotation_time,owner='player',damage=self.projectile_damage)

        projectiles.append(projectile)

    # STATE MACHINE
    def set_state(self):
        old = self.state

        if self.interact_timer>0:
            self.state = 'interact'
            self.sleep_timer=0
            return
        
        if self.attack_timer>0:
            self.state = 'attack'
            self.sleep_timer=0
            return
        
        if self.shoot_timer>0: #state = shooting same sprite as interact for now
            self.state = 'interact'
            self.sleep_timer=0
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

        #if invincible, sprite flicker
        show_sprite = True
        if self.invincible_timer>0:
            show_sprite = (self.invincible_timer%4)<2
        
        if show_sprite:
            if self.djump_used: #rotate jump sprite if is a double jump
                spr(sprite_id,int(self.x - cam_x),int(self.y - cam_y),colorkey=0,scale=1,flip=self.dir,rotate=self.flipper,w=2,h=2)
            else:
                spr(sprite_id,int(self.x - cam_x),int(self.y - cam_y),colorkey=0,scale=1,flip=self.dir,rotate=0,w=2,h=2)

        #draw attack
        if self.attack_timer>0:
            if self.attack_dir == 'up':
                atk_x = self.x + (self.w//2 - self.attack_w//2)
                atk_y = self.y - self.attack_h

                spr(self.attack_sprite,int(atk_x - cam_x),int(atk_y - cam_y),colorkey=0,scale=1,flip=self.dir,rotate=3,w=2,h=2)
            elif self.attack_dir == 'down':
                atk_x = self.x + (self.w//2 - self.attack_w//2)
                atk_y = self.y + self.h

                spr(self.attack_sprite,int(atk_x - cam_x),int(atk_y - cam_y),colorkey=0,scale=1,flip=self.dir,rotate=1,w=2,h=2)
            else:
                if self.dir==0:
                    atk_x = self.x+self.w
                else:
                    atk_x = self.x-self.attack_w

                atk_y = self.y+2

                spr(self.attack_sprite,int(atk_x - cam_x),int(atk_y - cam_y),colorkey=0,scale=1,flip=self.dir,rotate=0,w=2,h=2)

    # Gather all update methods
    def update(self, cam_x, cam_y, interactables, projectiles):
        self.move()
        self.collide_interactables_horizontal(interactables)
        self.collide_interactables_vertical(interactables)
        self.check_hit_by_projectiles(projectiles)
        player.try_interact(interactables)
        player.try_shoot(projectiles)
        self.cheat_full_health()
        self.cheat_more_health()
        self.try_attack()
        self.set_state()
        self.animate()
        self.draw(cam_x, cam_y)

# PROJECTILE
class Projectile:
    def __init__(self, x, y, dir, sprite, speed=3, max_dist=120, w=8, h=8, rotation_time=0, owner='player', damage=1, vx=None, vy=None):
        # DEBUG TEMP (remova depois se quiser)
        # print("Projectile init (v2)", x, y, dir, sprite, "vx", vx, "vy", vy)

        self.x = x
        self.y = y
        self.dir = dir
        self.sprite = sprite
        self.speed = speed
        self.max_dist = max_dist
        self.start_x = x
        self.start_y = y
        self.w = w
        self.h = h

        # movimento custom
        self.vx = vx
        self.vy = vy

        # rotação
        self.rotation_time = rotation_time
        self.rotation_timer = 0
        self.rotation_frame = 0

        self.damage = damage
        self.owner = owner

    def move(self):
        # movimento padrão (horizontal)
        if self.vx is None:
            if self.dir == 0:
                self.x += self.speed
            else:
                self.x -= self.speed
        else:
            # movimento direcional real (teleguiado)
            self.x += self.vx
            self.y += self.vy

        # rotação
        if self.rotation_time > 0:
            self.rotation_timer += 1
            if self.rotation_timer >= self.rotation_time:
                self.rotation_frame = (self.rotation_frame + 1) % 4
                self.rotation_timer = 0

    def hit_solid(self):
        return (
            solid_tile_at(self.x, self.y) or solid_tile_at(self.x + self.w - 1, self.y + self.h - 1)
        )

    def draw(self, cam_x, cam_y):
        spr(
            self.sprite,
            int(self.x - cam_x),
            int(self.y - cam_y),
            colorkey=0,
            scale=1,
            flip=self.dir,
            rotate=self.rotation_frame if self.rotation_time > 0 else 0,
            w=1,
            h=1
        )

    def dead(self):
        dist = abs(self.x - self.start_x)
        return dist > self.max_dist


# INTERACTABLE
class Interactable:
    def __init__(self, x, y, w, h, sprite, trigger, req=None, solid=True):
            self.x = x
            self.y = y
            self.w = w
            self.h = h
            self.sprite = sprite     # base sprite
            self.trigger = trigger   # trigger function on interaction
            self.req = req           # optional requirement (ex: key)
            self.solid = solid

    def check_interact_area(self, player):
        RANGE = 10  # max distance for interaction

        if player.dir == 0:  # looking right
            ix = player.x + player.w
            iy1 = player.y
            iy2 = player.y + player.h
            return (ix + RANGE > self.x and ix < self.x + self.w and iy2 > self.y and iy1 < self.y + self.h)

        else:  # looking left
            ix = player.x
            iy1 = player.y
            iy2 = player.y + player.h
            return (ix - RANGE < self.x + self.w and ix > self.x and iy2 > self.y and iy1 < self.y + self.h)
        
    def draw(self, cam_x, cam_y):
        spr(self.sprite, int(self.x - cam_x), int(self.y - cam_y), 
            colorkey=0, scale=1, rotate=0, w=self.w//8, h=self.h//8)

def door_trigger(player, interactable):
    player.door_keys+=1
    door_opened_sprite = 192
    interactable.solid = False
    interactable.sprite = door_opened_sprite

def door_req(num):
    return lambda player: getattr(player, 'door_keys')>=num

def chest_trigger(player,interactable):
    chest_opened_sprite = 236
    interactable.solid = False
    interactable.sprite = chest_opened_sprite

def chest_req(num):
    return lambda player: getattr(player,'chest_keys')>=num

#SPAWNER
class Spawner:
    def __init__(self, x, y, enemy_type, interval=120, limit=None, req=None, offset_x=0, offset_y=0):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type     # classe do inimigo Ex: Patrol
        self.interval = interval         # frames entre spawns
        self.limit = limit               # maximo de inimigos vivos (None = infinito)
        self.req = req                   # função requisito: req(player) → bool
        self.timer = 0
        self.spawned = []                # lista de inimigos criados
        self.offset_x = offset_x         # ajuste fino para spawn
        self.offset_y = offset_y

    def update(self, player, enemies):
        # requisito falhou? não pode spawnar ainda
        if self.req and not self.req(player):
            return
        
        # controla tempo
        self.timer += 1
        if self.timer < self.interval:
            return
        
        self.timer = 0  # reset do timer

        # limite atingido?
        if self.limit is not None:
            # limpa os mortos antes
            self.spawned = [e for e in self.spawned if not e.is_dead()]
            if len(self.spawned) >= self.limit:
                return
        
        # cria inimigo
        enemy = self.enemy_type(
            self.x + self.offset_x,
            self.y + self.offset_y
        )

        enemies.append(enemy)
        self.spawned.append(enemy)

# ---------- ENEMIES ----------
class Enemy:
    def __init__(self, x, y, w, h, sprite_base, frame_max=2, anim_speed=15, max_hp=3,damage=1,speed=1,knockback=4):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        #standard attributes
        self.max_hp = max_hp
        self.hp = max_hp
        self.damage = damage
        self.knockback = knockback
        self.speed = speed

        #animation
        self.sprite_base = sprite_base
        self.frame = 0
        self.frame_max = frame_max
        self.anim_speed = anim_speed
        self.t = 0
        self.facing = 0 # 0 right / 1 left
        self.anim_timer = 0

        #physics
        self.vx = 0
        self.vy = 0
        self.gravity = 0.4
        self.max_fall = 3
        self.on_ground = False

        #invencibility
        self.invincible_timer = 0
        self.invincible_duration = 20  # frames de invencibilidade
        self.flasher = 0
        self.flipper = 0
        self.flipper_speed = 4
        self.flipper_t = 0
        self.stun_timer = 0
        self.stun_duration = 5
        self.side_force = 3
    
    # abstract methods
    def move_behavior(self,player: Player):
        pass

    def on_player_collision(self,player: Player):
        pass

    def check_player_attack(self, player: Player):
        #just verify if player attacks
        if player.attack_timer <= 0:
            return
        
        if self.invincible_timer > 0:
            return
        
        atk_x, atk_y, atk_w, atk_h = player.attack_hitbox()

        #check hitbox on enemy
        if self.x < atk_x + atk_w and self.x + self.w > atk_x and self.y < atk_y + atk_h and self.y + self.h > atk_y:
            # apply damage
            self.take_damage(1, source=player)
            # apply recoil on enemy
            recoil(self, player.x + player.w / 2, player.y + player.h / 2, side_force=self.side_force, up_force=-3)
            self.invincible_timer = self.invincible_duration
            self.stun_timer = self.stun_duration

            #pogo on player
            if player.attack_dir=='up':
                recoil(player,self.x,self.y,side_force=0,up_force=4)
            elif player.attack_dir=='down':
                recoil(player,self.x,self.y,side_force=0,up_force=-6)

    def check_player_projectile(self, player: Player, projectiles: list[Projectile]):
        for proj in list(projectiles):

            # ============================
            # 1) PROJÉTIL DO PLAYER → acerta INIMIGO
            # ============================
            if proj.owner == "player":
                if ( self.x < proj.x + proj.w and self.x + self.w > proj.x and self.y < proj.y + proj.h and self.y + self.h > proj.y):
                    if self.invincible_timer > 0:
                        continue

                    # dano no inimigo
                    self.take_damage(proj.damage, source=player)

                    # stun + invencibilidade
                    self.stun_timer = self.stun_duration
                    self.invincible_timer = self.invincible_duration

                    # RECOIL correto
                    recoil(
                        self,
                        proj.x,
                        proj.y,
                        side_force=self.side_force,
                        up_force=-3
                    )

                    if proj in projectiles:
                        projectiles.remove(proj)
                    continue

            # ============================
            # 2) PROJÉTIL DO BOSS → acerta PLAYER
            # ============================
            if proj.owner == "boss":
                if (player.x < proj.x + proj.w and player.x + player.w > proj.x and player.y < proj.y + proj.h and player.y + player.h > proj.y):

                    if proj in projectiles:
                        projectiles.remove(proj)

                    player.take_damage(
                        proj.damage,
                        self.x,
                        self.y,
                        self.knockback
                    )
                    continue



    def is_dead(self):
        return self.hp<=0
    
    def kill(self):
        self.hp = 0

    def take_damage(self, amount, source = None):
        self.hp -= amount

        if self.hp < 0:
            self.hp = 0

        #possible on_death actions

    def apply_gravity(self):
        self.vy += self.gravity
        if self.vy > self.max_fall:
            self.vy = self.max_fall
        
        self.y += self.vy
        
        ix = int(self.x)
        iy = int(self.y)

        left = ix
        right = ix + self.w - 1
        top = iy
        bottom = iy + self.h - 1

        #ground
        if self.vy >= 0:
            if solid_tile_at(left, bottom) or solid_tile_at(right, bottom):
                tile_y = (bottom // 8) * 8
                self.y = tile_y - self.h
                self.vy = 0
                self.on_ground = True
            else:
                self.on_ground = False
        #ceiling
        else:
            if solid_tile_at(left, top) or solid_tile_at(right, top):
                self.vy = 0
                self.y = ((top // 8) + 1) * 8
        
    def move_friction(self):
        old_x = self.x
        self.x += self.vx  # move pelo vx atual

        left = int(self.x)
        right = int(self.x + self.w - 1)
        top = int(self.y)
        bottom = int(self.y + self.h - 1)

        collided = False

        # colisões laterais
        if self.vx > 0 and (solid_tile_at(right, top) or solid_tile_at(right, bottom)):
            collided = True
        elif self.vx < 0 and (solid_tile_at(left, top) or solid_tile_at(left, bottom)):
            collided = True

        if collided:
            self.x = old_x
            self.vx = 0  # zera velocidade ao colidir

        # aplica atrito para ir desacelerando
        friction = 0.3  # ajuste conforme necessário
        if self.vx > 0:
            self.vx -= friction
            if self.vx < 0:
                self.vx = 0
        elif self.vx < 0:
            self.vx += friction
            if self.vx > 0:
                self.vx = 0

    def animate(self):
        self.t += 1
        if self.t % self.anim_speed == 0:
            self.frame = (self.frame + 1) % self.frame_max
    
    def draw(self, cam_x, cam_y):
        sx = self.w//8
        sy = self.h//8
        tiles_per_frame = sx

        show_sprite = True
        if self.invincible_timer > 0:
            show_sprite = (self.invincible_timer % 4) < 2  # flicking
        
        if show_sprite:
            spr(
                self.sprite_base + (self.frame*tiles_per_frame),
                int(self.x - cam_x),
                int(self.y - cam_y),
                colorkey=0,
                w=sx,
                h=sy,
                flip = self.facing
            )
    
    def check_collision_player(self, player):
        if self.x < player.x + player.w and self.x + self.w > player.x and self.y < player.y + player.h and self.y + self.h > player.y:
            return True
        return False
    
    def update(self, cam_x, cam_y, player):
        self.anim_timer += 1

        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            self.flipper_t += 1
            if self.flipper_t >= self.flipper_speed:
                self.flipper = (self.flipper + 1) % 2  # alterna entre 0 e 1
                self.flipper_t = 0

        if self.stun_timer>0:
            self.stun_timer-=1
            #don't make move behavior
            self.apply_gravity()  # ainda aplica gravidade
            self.move_friction()
            self.animate()
            self.draw(cam_x, cam_y)
            return

        self.apply_gravity()
        self.move_behavior(player)
        self.animate()
        self.draw(cam_x, cam_y)

        if self.check_collision_player(player):
            self.on_player_collision(player)
        
        self.check_player_attack(player)

class Patrol(Enemy):
    def __init__(self, x, y, w, h, sprite_base, frame_max=2, anim_speed=15, max_hp=3, damage=1, speed=1, knockback=4, patrol_range=80):
        super().__init__(x, y, w, h, sprite_base, frame_max, anim_speed, max_hp, damage, speed, knockback)
        self.dir = 1 if patrol_range>=0 else -1
        self.start_x = x
        self.patrol_range = abs(patrol_range)

    def move_behavior(self, player: Player):
        self.facing = 0 if self.dir > 0 else 1
        old_x = self.x

        # calculate distance from start
        dist_from_start = self.x - self.start_x

        # reverse if surpass patrol_range
        if dist_from_start >= self.patrol_range and self.dir > 0:
            self.dir = -1
        elif dist_from_start <= self.patrol_range * -1 and self.dir < 0:
            self.dir = 1

        # define velocity
        self.vx = self.dir * self.speed

        # verify floor ahead
        front_x = self.x + (self.dir > 0) * self.w
        front_y = self.y + self.h
        if not solid_tile_at(front_x, front_y + 1):
            self.dir *= -1
            self.vx = self.dir * self.speed

        # move enemy
        self.x += self.vx

        # side collisions
        left = int(self.x)
        right = int(self.x + self.w - 1)
        top = int(self.y)
        bottom = int(self.y + self.h - 1)

        if self.vx > 0 and (solid_tile_at(right, top) or solid_tile_at(right, bottom)):
            self.x = old_x
            self.dir = -1
        elif self.vx < 0 and (solid_tile_at(left, top) or solid_tile_at(left, bottom)):
            self.x = old_x
            self.dir = 1

    def on_player_collision(self, player):
        if player.invincible_timer==0:
            player.take_damage(self.damage,self.x,self.y,self.knockback)

class Patrol(Enemy):
    def __init__(self, x, y, w, h, sprite_base, frame_max=2, anim_speed=15, max_hp=3, damage=1, speed=1, knockback=4, patrol_range=80):
        super().__init__(x, y, w, h, sprite_base, frame_max, anim_speed, max_hp, damage, speed, knockback)
        self.dir = 1 if patrol_range>=0 else -1
        self.start_x = x
        self.patrol_range = abs(patrol_range)

    def move_behavior(self, player: Player):
        self.facing = 0 if self.dir > 0 else 1
        old_x = self.x

        # calculate distance from start
        dist_from_start = self.x - self.start_x

        # reverse if surpass patrol_range
        if dist_from_start >= self.patrol_range and self.dir > 0:
            self.dir = -1
        elif dist_from_start <= self.patrol_range * -1 and self.dir < 0:
            self.dir = 1

        # define velocity
        self.vx = self.dir * self.speed

        # verify floor ahead
        front_x = self.x + (self.dir > 0) * self.w
        front_y = self.y + self.h
        if not solid_tile_at(front_x, front_y + 1):
            self.dir *= -1
            self.vx = self.dir * self.speed

        # move enemy
        self.x += self.vx

        # side collisions
        left = int(self.x)
        right = int(self.x + self.w - 1)
        top = int(self.y)
        bottom = int(self.y + self.h - 1)

        if self.vx > 0 and (solid_tile_at(right, top) or solid_tile_at(right, bottom)):
            self.x = old_x
            self.dir = -1
        elif self.vx < 0 and (solid_tile_at(left, top) or solid_tile_at(left, bottom)):
            self.x = old_x
            self.dir = 1

    def on_player_collision(self, player):
        if player.invincible_timer==0:
            player.take_damage(self.damage,self.x,self.y,self.knockback)


class Stalker(Enemy):
    def __init__(self, x, y, w, h, sprite_base, frame_max=2, anim_speed=15, max_hp=3, damage=1, speed=1, knockback=4):
        super().__init__(x, y, w, h, sprite_base, frame_max, anim_speed, max_hp, damage, speed, knockback)

        self.start_x = x
        self.start_y = y
        self.jump_force = -4
        self.side_force = 5

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vx = 0
        self.vy = 0

    def move_behavior(self, player):
        self.facing = 0 if self.vx>=0 else 1
        #follows player
        if player.x>self.x:
            self.vx = self.speed
        elif player.x<self.x:
            self.vx = -self.speed
        else:
            self.vx = 0
        
        old_x = self.x
        self.x += self.vx

        #lateral collision
        left = int(self.x)
        right = int(self.x + self.w - 1)
        top = int(self.y)
        bottom = int(self.y + self.h - 1)

        collided = False
        wall = False

        #right collision
        if self.vx > 0 and (solid_tile_at(right, top) or solid_tile_at(right, bottom)):
            collided = True
        
        if self.vx < 0 and (solid_tile_at(left, top) or solid_tile_at(left, bottom)):
            collided = True
        
        if self.vx > 0 and solid_tile_at(right, bottom):
            wall = True
        elif self.vx < 0 and solid_tile_at(left, bottom):
            wall = True
        else:
            wall = False

        if collided:
            self.x = old_x
            self.vx = 0
        
        #jump
        if self.on_ground and wall:
            self.vy = self.jump_force
            self.on_ground = False

    def on_player_collision(self, player):
        if player.invincible_timer==0:
            player.take_damage(self.damage,self.x,self.y,self.knockback)



class FlyingStalker(Enemy):
    def __init__(self, x, y, w, h, sprite_base, frame_max=2, anim_speed=15,
                 max_hp=3, damage=1, speed=1, knockback=4):
        super().__init__(x, y, w, h, sprite_base, frame_max, anim_speed,
                         max_hp, damage, speed, knockback)

        # desliga física de solo
        self.gravity = 0
        self.max_fall = 0
        self.on_ground = False

    def apply_gravity(self):
        # NÃO FAZ NADA — voador não tem gravidade
        pass

    def move_friction(self):
        # NÃO FAZ NADA — voador não tem colisão nem atrito
        self.x += self.vx
        self.y += self.vy

    def move_behavior(self, player):
        # segue o player nos dois eixos
        dx = player.x - self.x
        dy = player.y - self.y

        # normaliza direção (pra não voar super rápido na diagonal)
        mag = (dx*dx + dy*dy)**0.5
        if mag != 0:
            dx /= mag
            dy /= mag

        # aplica velocidade
        self.vx = dx * self.speed
        self.vy = dy * self.speed

        # orientação horizontal (opcional)
        self.facing = 0 if self.vx >= 0 else 1

        # move sem colisões
        self.x += self.vx
        self.y += self.vy

    def on_player_collision(self, player):
        if player.invincible_timer == 0:
            player.take_damage(self.damage, self.x, self.y, self.knockback)

class BossFinal(Enemy):
    def __init__(self, x, y):
        super().__init__(
            x, y,
            32, 64,          # tamanho
            384,             # <-- sprite_base (coloque AQUI o primeiro sprite do boss)
            frame_max=2,     # AGORA TEM 4 FRAMES
            anim_speed=10,
            max_hp=40,
            damage=2,
            speed=0.3,
            knockback=6
            
        )
        
        self.spawn_timer = 0
        self.spawn_delay = 300   # frames (5s aprox)

        # tiro
        self.shoot_timer = 0
        self.shoot_delay = 90
        self.projectile_sprite = 303
        self.projectile_speed = 2
        self.projectile_damage = 1
        self.active = True

    def move_behavior(self, player: Player):
        if not self.active:
            self.vx = 0
            return

        # movimento horizontal simples
        if player.x > self.x:
            self.vx = self.speed
            self.facing = 0
        else:
            self.vx = -self.speed
            self.facing = 1

        # chama atrito/mov
        self.move_friction()

        # avanço da animação
        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame = (self.frame + 1) % self.frame_max

        # tiro
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            self.shoot(player)
            
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            self.spawn_minion()

    def shoot(self, player: Player):
        if not self.active:
            return

        spawn_x = int(self.x + (self.w // 2))
        spawn_y = int(self.y + (self.h // 2))

        dx = player.x - spawn_x
        dy = player.y - spawn_y
        dist = max(1, (dx*dx + dy*dy) ** 0.5)

        speed = self.projectile_speed
        vx = (dx / dist) * speed
        vy = (dy / dist) * speed

        projectiles.append(
            Projectile(
                spawn_x, spawn_y,
                0,
                self.projectile_sprite,
                speed=speed,
                max_dist=80,
                w=8, h=8,
                rotation_time=0,
                owner="boss",
                damage=self.projectile_damage,
                vx=vx,
                vy=vy
            )
        )
        
    def spawn_minion(self):
        enemies.append(
            FlyingStalker(
                self.x + self.w//2,   # nasce no meio do boss
                self.y,               # um pouco acima
                8, 8,
                380,                  # sprite do flying stalker
                speed=0.8,
                frame_max=2,
                anim_speed=12
            )
        )

    def on_player_collision(self, player: Player):
        if player.invincible_timer == 0:
            player.take_damage(self.damage, self.x, self.y, self.knockback)

    def reset(self):
        self.hp = self.max_hp
        self.vx = 0
        self.vy = 0
        self.shoot_timer = 0
        self.active = True

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

# ---------- GAME SCREENS ----------
def center_x(text, scale, screen_w=240):
    char_w = 5
    width = len(text) * char_w * scale
    return int(screen_w/2 - width/2)

menu_t = 0

def draw_menu(player):
    global menu_t
    menu_t+=1
    cls()

    bg_tile = 176
    tile_w = 1
    tile_h = 1
    WHITE = 12
    BLACK = 15

    #DRAW BG TILES
    for ty in range(0,136,tile_h):
        for tx in range(0,240,tile_w):
            spr(bg_tile,tx,ty,colorkey=0,w=tile_w,h=tile_h)

    #TITLE
    title = "COLISEU RUN"
    title_scale = 2
    title_x = center_x(title, title_scale)
    title_y = 20
    print(title, title_x, title_y, WHITE, False, title_scale)

    #PLAYER ANIMATION
    anim_state = player.animations['sleep']

    frame = (menu_t//anim_state['speed'])%anim_state['frames']
    sprite_id = anim_state['start'] + frame * 2

    #DRAW PLAYER WITH SCALE
    px = 240//2 - (16*3)//2
    py = 68
    spr(sprite_id, px, py, colorkey=0, scale=3, flip=0, w=2, h=2)

    #START MSG
    msg = "PRESS 'SPACE' TO PLAY"
    msg_scale = 1
    msg_x = center_x(msg, msg_scale)
    msg_y = py + 16*3 + 12

    # blink every 20 frames
    if (menu_t//20)%2==0:
        print(msg, msg_x, msg_y, WHITE, False, 1)

def draw_game_over():
    global menu_t
    menu_t += 1
    cls()

    bg_tile = 176
    tile_w = 1
    tile_h = 1
    WHITE = 12
    RED = 14

    #DRAW BG
    for ty in range(0, 136, tile_h):
        for tx in range(0, 240, tile_w):
            spr(bg_tile, tx, ty, colorkey=0, w=tile_w, h=tile_h)
    
    #TITLE
    title = "YOU DIED!"
    title_scale = 2
    title_x = center_x(title, title_scale)
    title_y = 20
    print(title, title_x, title_y, WHITE, False, title_scale)

    #DEAD SPRITE
    sprite_id = 308
    scale = 3
    w = 2 * 8 * scale   # largura real
    h = 1 * 8 * scale   # altura real

    px = int(240/2 - w/2)
    py = 60

    spr(sprite_id, px, py, colorkey=0, scale=scale, w=2, h=1)

    #RESTART MSG
    msg = "PRESS 'E' TO RESTART"
    msg_scale = 1
    msg_x = center_x(msg, msg_scale)
    msg_y = py + h + 16

    # blink every 20 frames
    if (menu_t // 20) % 2 == 0:
        print(msg, msg_x, msg_y, WHITE, False, msg_scale)

def draw_game_win():
    cls()

    bg_tile = 176
    tile_w = 1
    tile_h = 1

    WHITE = 12
    YELLOW = 5

    # fundo
    for ty in range(0, 136, tile_h):
        for tx in range(0, 240, tile_w):
            spr(bg_tile, tx, ty, colorkey=34, w=tile_w, h=tile_h)

    # TÍTULO EM AMARELO
    title = "VICTORY!"
    title_scale = 2
    title_x = center_x(title, title_scale)
    title_y = 20
    print(title, title_x, title_y, YELLOW, False, title_scale)   # <-- AQUI
    
    spr(396, 104, 52, colorkey=0, w=3, h=3)

    # texto inferior branco
    msg = "PRESS 'E' TO RETURN"
    msg_scale = 1
    msg_x = center_x(msg, msg_scale)
    msg_y = 90
    print(msg, msg_x, msg_y, WHITE, False, msg_scale)



#GLOBALS

TILE_SIZE = 8
MAP_W_TILES = 120
MAP_H_TILES = 120
MAP_W = MAP_W_TILES * TILE_SIZE
MAP_H = MAP_H_TILES * TILE_SIZE
W = 240
H = 136
T = 8


def rand(a, b):
    return random.randint(a, b) 

player = Player(0, 0)

enemies = []
spawners = []

projectiles = []

interactables = []

GAME_STATE = "menu"
death_timer = 0

music_started = False

def init_game():
    global player, enemies, projectiles, interactables, death_timer, music_started, spawners

    player = Player(0, 100)

    enemies = [
        # Patrol(200,100,16,32,320,speed=0.5),
        # Patrol(200,100,8,8,348,patrol_range=40),
        # Stalker(200,100,8,8,364,speed=0.6,knockback=7),

        # # FANTASMA VOADOR (FlyingStalker)
        # FlyingStalker(150, 50, 8, 8, 380, speed=0.8, frame_max=2, anim_speed=12),
        
        # BOSS FINAL (32x64)
        BossFinal(400, 50)

    ]

    spawners = [
        #Spawner(150,80,lambda x,y: Patrol(x,y,8,8,348,patrol_range=40),180,3,lambda p: p.door_keys == 1),
        Spawner(27*8,0,lambda x,y: Stalker(x,y,8,8,364,speed=0.4),180,3,lambda p: p.door_keys==1)
    ]

    projectiles = []

    chest_closed_sprite = 204
    door_closed_sprite = 206

    interactables = [
        Interactable(232, 88, 16, 32, door_closed_sprite, door_trigger, door_req(1)),
        Interactable(7*8, 13*8, 16, 16, chest_closed_sprite, chest_trigger, chest_req(1))
    ]

    death_timer = 0
    music_started = False

def draw_HUD(player):
    # hud position
    x = 2
    y = 2

    # cada coração vale 1 de vida
    max_hearts = player.max_hp
    hearts = player.hp

    for i in range(max_hearts):
        px = x + i * 10  # spacing

        if i < hearts:
            spr(292, px, y,colorkey=0)   # full heart
        else:
            spr(293, px, y,colorkey=0)   # empty heart

def TIC():
    global player, GAME_STATE, death_timer, music_started, interactables, projectiles

    #music
    if not music_started:
        music(0, loop=True)
        music_started = True

    if GAME_STATE == "menu":
        draw_menu(player)
        # SPACE = começar jogo
        if btn(4) or key(48):  # botão 'A' do TIC-80
            init_game()
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

        #draw interactables
        for inter in interactables:
            inter.draw(cam_x,cam_y)

        #update player
        player.update(cam_x, cam_y,interactables,projectiles)

        #update projectiles
        for proj in projectiles:
            proj.move()

            if proj.hit_solid() or collide_interactables(proj,interactables) or proj.dead():
                projectiles.remove(proj)
                continue
            proj.draw(cam_x, cam_y)

        for sp in spawners:
            sp.update(player, enemies)

        #update enemy
        for enemy in list(enemies):
            enemy.update(cam_x, cam_y, player)
            enemy.check_player_projectile(player, projectiles)

            if enemy.is_dead():
                # SE FOR O BOSS → VITÓRIA!
                if isinstance(enemy, BossFinal):
                    GAME_STATE = "win"
                    return

                enemies.remove(enemy)


        #draw hud must be the last draw function
        draw_HUD(player)

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
    
    if GAME_STATE == "win":
        draw_game_win()

        # Aperta E para voltar ao menu
        if btnp(7) or key(5):
            GAME_STATE = "menu"
        return