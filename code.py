# title:   LP_Trabalho1
# author:  Alexandre, Jean, Joao Vitor, Julia
# desc:    trabalho de LP
# site:    website link
# license: MIT License (change this to your license of choice)
# version: 0.1
# script:  python

#TODO: refactor player sprite for 16x16 pixels
#TODO: implement different sprite states (idle, moving, jumping, droping, attacking)
#TODO: fix player teleporting up in walls
#TODO: refactor camera placement for hide rooms
#TODO: implement player physical attack and projectile upgrade
#TODO: implement 2 enemies structure type and 1 boss

class Player:
 def __init__(self, x, y, sprite_base):
  #location
  self.x = x
  self.y = y
  self.vx=0
  self.friction = 0.1
  self.max_vx=3
  self.gspeed = 0.5
  self.aspeed = 0.5
  self.dir = 0 #0 right 1 left
  
  #physic
  self.vy=0
  self.gravity = 0.4
  self.jump_force = -4
  self.jump_boost = -0.4
  self.max_jump_time = 12
  self.jump_timer = 0
  self.on_ground = False
  
  #anim
  self.sprite_base = sprite_base
  self.w = 8   # sprite width
  self.h = 8   # sprite height
  self.frame = 0 
  self.frame_max = 4 #n of sprites
  self.anim_speed = 8 #sprite change speed
  self.t = 0 #time counter
  self.flipper = 0
  self.flipper_speed = 4
  self.flipper_t = 0
  
 def move_horizontal(self):
  """w,a,s,d (23,1,19,4)"""
  #self.dir = 0 if self.vx>=0 else 1
  old_x = self.x
  self.x += self.vx
  if self.vx>self.max_vx:
   self.vx=self.max_vx
  elif self.vx<-self.max_vx:
   self.vx=-self.max_vx
  moving = False
  speed = self.gspeed if self.on_ground else self.aspeed
  if btn(2) or key(1):
   self.vx -= speed
   self.dir = 1
   moving = True
  elif btn(3) or key(4):
   self.vx += speed
   self.dir = 0
   moving = True
  else:
   if abs(self.vx)>self.friction:
    self.vx = 0
   if self.vx>0:
    self.vx -=self.friction
   elif self.vx<0:
    self.vx +=self.friction
  
  #horizontal colision
  left = self.x
  right = self.x + self.w - 1
  top = self.y
  bottom = self.y + self.h - 1
  
  if self.vx < 0:  # movendo para esquerda
   if solid_tile_at(left, top) or solid_tile_at(left, bottom):
    self.x = old_x
    self.vx = 0

  if self.vx > 0:  # movendo para direita
   if solid_tile_at(right, top) or solid_tile_at(right, bottom):
    self.x = old_x
    self.vx = 0
  
  #horizontal move
  if moving:
   self.t +=1
   if self.t % self.anim_speed == 0:
    self.frame = (self.frame+1)%self.frame_max
  else:
   self.frame = 0

 def apply_gravity(self):
  old_y = self.y

  # aplica gravidade
  self.vy += self.gravity
  if self.vy > 3:
   self.vy = 3

  self.y += self.vy

  # --- COLISÃO VERTICAL ---
  left = self.x
  right = self.x + self.w - 1
  top = self.y
  bottom = self.y + self.h - 1

  # caindo
  if self.vy > 0:
   if solid_tile_at(left, bottom) or solid_tile_at(right, bottom):
    self.y = (int(bottom) // 8) * 8 - self.h
    self.vy = 0
    self.on_ground = True
   else:
    self.on_ground = False

  # subindo
  elif self.vy < 0:
   if solid_tile_at(left, top) or solid_tile_at(right, top):
    self.y = (int(top) // 8 + 1) * 8
    self.vy = 0

 def jump(self):
  jump_pressed = btn(4) or key(23) or key(48)
  jump_just_pressed = btnp(4) or key(23) or key(48)
  
  if jump_just_pressed and self.on_ground:
   self.vy = self.jump_force
   self.on_ground = False
   self.jump_timer = 0
  if jump_pressed and not self.on_ground and self.vy<0:
   if self.jump_timer<self.max_jump_time:
    self.vy += self.jump_boost
    self.jump_timer += 1

 def move(self):
  self.move_horizontal()
  self.apply_gravity()
  self.jump()

 def draw(self, cam_x, cam_y):
  sprite_id = self.sprite_base+self.frame

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

def solid_tile_at(px, py):
 px=int(px)
 py=int(py)
 tile_x = px // 8
 tile_y = py // 8
 tile_id = mget(tile_x, tile_y)
 return tile_id < 64
 
def get_camera(player):
 cam_x = int(player.x - 240//2)
 cam_y = int(player.y - 136//2)

 # limitacoes da camera
 cam_x = max(0, min(cam_x, MAP_W - 240))
 cam_y = max(0, min(cam_y, MAP_H - 136))

 return cam_x, cam_y

player = Player(100,60,256)

#tamanho do mundo em tiles
TILE_SIZE = 8
MAP_W_TILES = 120
MAP_H_TILES = 30
MAP_W = MAP_W_TILES * TILE_SIZE
MAP_H = MAP_H_TILES * TILE_SIZE

def TIC():
 global player
 
 cls()
 
 cam_x, cam_y = get_camera(player)
 
 map(
  cam_x//TILE_SIZE,
  cam_y//TILE_SIZE,
  30,
  20,
  -(cam_x % TILE_SIZE),
  -(cam_y % TILE_SIZE)
 )
 player.update(cam_x,cam_y)