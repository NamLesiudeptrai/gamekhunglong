import pygame
import os
import random
import asyncio
import sys

# Kiểm tra nếu đang chạy trên WASM
WASM_MODE = sys.platform == "emscripten"

pygame.init()

# Khởi tạo mixer cẩn thận hơn
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    print("Audio mixer initialized successfully")
except Exception as e:
    print(f"Warning: Audio mixer not available: {e}")

# Kích thước màn hình mặc định (portrait)
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100

# Kiểm tra orientation
def get_screen_orientation():
    """Phát hiện orientation dựa trên kích thước màn hình"""
    info = pygame.display.Info()
    if info.current_w > info.current_h:
        return "landscape"
    return "portrait"

# Khởi tạo màn hình với RESIZABLE flag
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Khủng long vượt ngàn chông gai")

RUNNING = [pygame.image.load(os.path.join("Assets/Dino", "run1.png")),
           pygame.image.load(os.path.join("Assets/Dino", "run2.png"))]
JUMPING = pygame.image.load(os.path.join("Assets/Dino", "jump.png"))
DUCKING = [pygame.image.load(os.path.join("Assets/Dino", "duck.png")),
           pygame.image.load(os.path.join("Assets/Dino", "duck2.png"))]

SMALL_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png"))]
LARGE_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png"))]

ROCK = [pygame.image.load(os.path.join("Assets/Rock", "Rock1.png")),
         pygame.image.load(os.path.join("Assets/Rock", "Rock2.png")),
         pygame.image.load(os.path.join("Assets/Rock", "Rock3.png"))]

BIRD = [pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
        pygame.image.load(os.path.join("Assets/Bird", "Bird2.png"))]

CLOUD = pygame.image.load(os.path.join("Assets/Other", "Cloud.png"))

BG = pygame.image.load(os.path.join("Assets/Other", "Track.png"))

# Load sounds với error handling
def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except:
        print(f"Warning: Could not load sound {path}")
        return None

JUMP_SOUND = load_sound(os.path.join("Assets/Sounds", "jump.mp3"))
DIE_SOUND = load_sound(os.path.join("Assets/Sounds", "die.mp3"))
CHECKPOINT_SOUND = load_sound(os.path.join("Assets/Sounds", "point.mp3"))
ITEM_COLLECT_SOUND = load_sound(os.path.join("Assets/Sounds", "item_collect.mp3"))
BOOM_SOUND = load_sound(os.path.join("Assets/Sounds", "ex.mp3"))

SPIKES = [pygame.image.load(os.path.join("Assets/Spikes", "spikes1.png")),
          pygame.image.load(os.path.join("Assets/Spikes", "spikes2.png")),
          pygame.image.load(os.path.join("Assets/Spikes", "spikes3.png"))]


def play_sound(sound):
    """Helper function để play sound an toàn"""
    if sound:
        try:
            sound.play()
        except:
            pass


def is_mobile():
    """Kiểm tra có phải đang chạy trên mobile không"""
    if WASM_MODE:
        # Kiểm tra user agent thông qua JavaScript (nếu có thể)
        # Hoặc dựa vào kích thước màn hình và orientation
        info = pygame.display.Info()
        
        # Kiểm tra xem có phải màn hình cảm ứng không
        # Trong Pygbag, mobile thường có màn hình portrait hoặc nhỏ hơn
        is_small_screen = info.current_w < 1024 and info.current_h < 1024
        is_portrait = info.current_h > info.current_w
        is_touch_size = info.current_w < 768
        
        return is_touch_size or (is_small_screen and is_portrait)
    
    return False


# Class cho Virtual Buttons
class VirtualButton:
    def __init__(self, x, y, width, height, text, color=(100, 100, 255), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.is_pressed = False
        self.alpha = 150  # Độ trong suốt
        
    def draw(self, screen):
        # Tạo surface trong suốt
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        if self.is_pressed:
            color = tuple(max(0, c - 50) for c in self.color) + (200,)
        else:
            color = self.color + (self.alpha,)
            
        pygame.draw.rect(s, color, s.get_rect(), border_radius=10)
        pygame.draw.rect(s, (255, 255, 255, 180), s.get_rect(), 3, border_radius=10)
        
        screen.blit(s, self.rect)
        
        # Vẽ text
        font = pygame.font.SysFont('arial', 20, bold=True)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def check_press(self, pos):
        return self.rect.collidepoint(pos)


class VirtualControls:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.buttons = {}
        self.setup_buttons()
        
    def setup_buttons(self):
        """Tạo các nút ảo"""
        button_size = 50
        gap = 8  # Khoảng cách đồng đều cho cả ngang và dọc
        padding = 30
        bottom_offset = self.screen_height - (button_size * 3 + gap * 2) - padding
        
        # Tính toán vị trí trung tâm để tạo hình chữ thập hoàn hảo
        center_x = padding + button_size + gap
        center_y = bottom_offset + button_size + gap
        
        # Hình chữ thập chuẩn
        self.buttons['up'] = VirtualButton(
            center_x, bottom_offset, button_size, button_size, "", (0, 0, 255)
        )
        
        self.buttons['left'] = VirtualButton(
            padding, center_y, button_size, button_size, "", (0, 255, 0)
        )
        
        self.buttons['right'] = VirtualButton(
            padding + (button_size + gap) * 2, center_y, button_size, button_size, "", (0, 255, 0)
        )
        
        self.buttons['down'] = VirtualButton(
            center_x, bottom_offset + (button_size + gap) * 2, button_size, button_size, "", (0, 0, 255)
        )
        
        # Nút bắn bên phải - đối xứng
        shoot_center_y = center_y
        shoot_center_x = self.screen_width - padding - button_size - (button_size + gap)
        self.buttons['shoot'] = VirtualButton(
            shoot_center_x, shoot_center_y, 
            button_size, button_size, "", (255, 0, 0)
        )
    
    def resize(self, screen_width, screen_height):
        """Cập nhật vị trí nút khi resize màn hình"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.setup_buttons()
    
    def draw(self, screen):
        """Vẽ tất cả nút"""
        for button in self.buttons.values():
            button.draw(screen)
    
    def handle_touch(self, pos, is_down=True):
        """Xử lý touch events và trả về action"""
        actions = {}
        for key, button in self.buttons.items():
            if button.check_press(pos):
                button.is_pressed = is_down
                actions[key] = is_down
            elif not is_down:
                button.is_pressed = False
        return actions
    
    def reset(self):
        """Reset tất cả nút"""
        for button in self.buttons.values():
            button.is_pressed = False


class Dinosaur:
    X_POS = 80
    Y_POS = 305
    Y_POS_DUCK = 330
    JUMP_VEL = 8.5
    MOVE_VEL = 25

    def __init__(self):
        self.duck_img = DUCKING
        self.run_img = RUNNING
        self.jump_img = JUMPING

        self.dino_duck = False
        self.dino_run = True
        self.dino_jump = False
        self.using_item = False

        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = self.run_img[0]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        
        self.hitbox = pygame.Rect(
            self.dino_rect.x + 20,
            self.dino_rect.y + 20,
            self.dino_rect.width - 40,
            self.dino_rect.height - 40
        )
        
        self.ammo = 0
        self.last_shot_time = 0
        self.shoot_cooldown = 500
        self.bullet_list = []

    def shoot(self):
        try:
            if self.ammo > 0:
                bullet = Bullet(self.dino_rect.right, self.dino_rect.centery)
                self.bullet_list.append(bullet)
                self.ammo -= 1
        except Exception as e:
            print(f"Error shooting: {e}")

    def add_ammo(self, amount=1):
        self.ammo += amount
    
    def has_ammo(self):
        return self.ammo > 0

    def update(self, userInput, virtual_input=None):
        if self.dino_duck:
            self.duck()
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()

        if self.step_index >= 10:
            self.step_index = 0

        # Xử lý keyboard input
        if userInput[pygame.K_UP] and not self.dino_jump:
            self.dino_duck = False
            self.dino_run = False
            self.dino_jump = True
        elif userInput[pygame.K_DOWN] and not self.dino_jump:
            self.dino_duck = True
            self.dino_run = False
            self.dino_jump = False
        elif not (self.dino_jump or userInput[pygame.K_DOWN]):
            self.dino_duck = False
            self.dino_run = True
            self.dino_jump = False
        
        # Xử lý virtual button input
        if virtual_input:
            if virtual_input.get('up') and not self.dino_jump:
                self.dino_duck = False
                self.dino_run = False
                self.dino_jump = True
            elif virtual_input.get('down') and not self.dino_jump:
                self.dino_duck = True
                self.dino_run = False
                self.dino_jump = False
            elif not (self.dino_jump or virtual_input.get('down')):
                if not virtual_input.get('up'):
                    self.dino_duck = False
                    self.dino_run = True
                    self.dino_jump = False
            
        if self.using_item:
            # Di chuyển bằng phím
            if userInput[pygame.K_LEFT]:
                self.dino_rect.x -= self.MOVE_VEL  
            if userInput[pygame.K_RIGHT]:
                self.dino_rect.x += self.MOVE_VEL
            
            # Di chuyển bằng virtual buttons
            if virtual_input:
                if virtual_input.get('left'):
                    self.dino_rect.x -= self.MOVE_VEL
                if virtual_input.get('right'):
                    self.dino_rect.x += self.MOVE_VEL
                
            if self.dino_rect.x < 0:
                self.dino_rect.x = 0
            if self.dino_rect.x > SCREEN_WIDTH - self.dino_rect.width:
                self.dino_rect.x = SCREEN_WIDTH - self.dino_rect.width
        
        self.hitbox.x = self.dino_rect.x + 20
        self.hitbox.y = self.dino_rect.y + 20

    def activate_item(self):
        self.using_item = True

    def deactivate_item(self):
        self.using_item = False

    def duck(self):
        self.image = self.duck_img[self.step_index // 5]
        self.dino_rect.y = self.Y_POS_DUCK 
        self.step_index += 1

    def run(self):
        self.image = self.run_img[self.step_index // 5]
        self.dino_rect.y = self.Y_POS  
        self.step_index += 1

    def jump(self):
        self.image = self.jump_img
        if self.dino_jump:
            if self.dino_rect.y == self.Y_POS:
                play_sound(JUMP_SOUND)
            self.dino_rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8
        if self.jump_vel < -self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))


class Cloud:
    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(800, 1000)
        self.y = random.randint(50, 100)
        self.image = CLOUD
        self.width = self.image.get_width()

    def update(self):
        self.x -= game_speed
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(2500, 3000)
            self.y = random.randint(50, 100)

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.x, self.y))


class Obstacle:
    def __init__(self, image, type):
        self.image = image
        self.type = type
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.pop()

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)


class SmallCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 325


class LargeCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 300


class Rock(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)      
        super().__init__(image, self.type)      
        self.rect.y = 395 - self.rect.height


class Spikes(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 315


class Bird(Obstacle):
    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = 250
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index//5], self.rect)
        self.index += 1


class Bullet:
    def __init__(self, x, y):
        try:
            self.image = pygame.image.load(os.path.join("Assets", "Other", "Bullet.png"))
            new_width = int(self.image.get_width() * 0.05)
            new_height = int(self.image.get_height() * 0.05)
            self.image = pygame.transform.scale(self.image, (new_width, new_height))
        except:
            self.image = pygame.Surface((10, 5))
            self.image.fill((255, 255, 0))
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.active = True

    def update(self):
        if self.active:
            self.rect.x += 20

    def draw(self, screen):
        if self.active:
            screen.blit(self.image, self.rect)


try:
    from item import Item, Gun
except ImportError:
    print("Error: Cannot import Item and Gun classes")
    class Item:
        def __init__(self):
            self.rect = pygame.Rect(0, 0, 1, 1)
        def reset(self): pass
        def update(self): pass
        def draw(self, screen): pass
        def collect(self): pass
    
    class Gun:
        def __init__(self):
            self.rect = pygame.Rect(0, 0, 1, 1)
        def reset(self): pass
        def update(self): pass
        def draw(self, screen): pass
        def collect(self): pass


async def main():
    global game_speed, x_pos_bg, y_pos_bg, points, obstacles, item_visible, SCREEN, SCREEN_WIDTH, SCREEN_HEIGHT
    run = True
    clock = pygame.time.Clock()
    player = Dinosaur()
    
    # Kiểm tra mobile - bắt đầu với giá trị mặc định
    mobile_mode = is_mobile()
    touch_detected = False  # Flag để phát hiện touch thực tế
    virtual_controls = None
    
    virtual_input = {}
    
    clouds = [Cloud() for _ in range(8)]
    game_speed = 20
    x_pos_bg = 0
    y_pos_bg = 370
    points = 0
    font = pygame.font.SysFont('arial', 20)
    obstacles = []
    death_count = 0
    
    day_night_cycle = 0
    current_brightness = 255
    transition_speed = 3
    
    item = Item()
    item_active = False
    item_start_time = 0
    item_visible = False  
    
    gun = Gun()
    gun_visible = False
    gun_reset_time = 0
    gun_spawn_counter = 0
    
    paused = False
    
    def score():
        global points, game_speed, item_visible
        points += 1
        if points % 100 == 0:
            game_speed += 1
            
        if points % 1000 == 0:
            play_sound(CHECKPOINT_SOUND)
            
        if points % 200 == 0 and not item_visible:
            item_visible = True
            item.reset()  

        text = font.render("Điểm: " + str(points), True, (0, 255, 0))
        textRect = text.get_rect()
        textRect.center = (SCREEN_WIDTH - 100, 40)
        SCREEN.blit(text, textRect)

    def background():
        global x_pos_bg, y_pos_bg
        image_width = BG.get_width()
        SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        if x_pos_bg <= -image_width:
            x_pos_bg = 0
        x_pos_bg -= game_speed

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                return
            
            # Xử lý resize màn hình
            if event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                if virtual_controls:
                    virtual_controls.resize(SCREEN_WIDTH, SCREEN_HEIGHT)
                print(f"Screen resized to: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
            
            # Xử lý virtual buttons
            if event.type == pygame.FINGERDOWN:
                # Phát hiện touch thực tế - bật mobile mode
                if not touch_detected:
                    touch_detected = True
                    mobile_mode = True
                    if not virtual_controls:
                        virtual_controls = VirtualControls(SCREEN_WIDTH, SCREEN_HEIGHT)
                        print("Touch detected! Enabling virtual controls")
            
            if mobile_mode or touch_detected:
                if not virtual_controls:
                    virtual_controls = VirtualControls(SCREEN_WIDTH, SCREEN_HEIGHT)
                    
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                    if event.type == pygame.FINGERDOWN:
                        pos = (int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT))
                    else:
                        pos = event.pos
                    actions = virtual_controls.handle_touch(pos, is_down=True)
                    virtual_input.update(actions)
                    
                    # Xử lý bắn
                    if actions.get('shoot'):
                        current_time = pygame.time.get_ticks()
                        if player.has_ammo() and (current_time - player.last_shot_time > player.shoot_cooldown):
                            player.shoot()
                            player.last_shot_time = current_time
                
                if event.type == pygame.MOUSEBUTTONUP or event.type == pygame.FINGERUP:
                    if event.type == pygame.FINGERUP:
                        pos = (int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT))
                    else:
                        pos = event.pos
                    actions = virtual_controls.handle_touch(pos, is_down=False)
                    for key in actions:
                        if key in virtual_input:
                            virtual_input[key] = False
        
        if paused:
            pause_text = font.render("Tạm dừng - Nhấn P để tiếp tục", True, (255, 0, 0))
            pause_text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            SCREEN.blit(pause_text, pause_text_rect)
            pygame.display.update()
            clock.tick(5)
            await asyncio.sleep(0)
            continue
        
        userInput = pygame.key.get_pressed()
        
        # Xử lý bắn đạn với keyboard
        current_time = pygame.time.get_ticks()
        try:
            if userInput[pygame.K_SPACE]:
                if player.has_ammo() and (current_time - player.last_shot_time > player.shoot_cooldown):
                    player.shoot()
                    player.last_shot_time = current_time
        except Exception as e:
            print(f"Error in shooting: {e}")

        if day_night_cycle % 2 == 0:
            if current_brightness < 255:
                current_brightness += transition_speed
        else:
            if current_brightness > 0:
                current_brightness -= transition_speed

        SCREEN.fill((current_brightness, current_brightness, current_brightness))

        if points >= 500:
            day_night_cycle = (points // 500) % 2

        gun_spawn_counter += 1
        
        if gun_spawn_counter >= random.randint(150, 300) and not gun_visible:
            if random.randint(0, 99) < 60:
                gun.reset()
                gun_visible = True
                gun_spawn_counter = 0
        
        if gun_spawn_counter > 500:
            gun_spawn_counter = 0

        if item_visible:
            item.update()
            item.draw(SCREEN)

            if player.hitbox.colliderect(item.rect):
                play_sound(ITEM_COLLECT_SOUND)
                item.collect()
                item_active = True
                item_start_time = pygame.time.get_ticks()
                player.activate_item()
                item_visible = False 

        if item_active:
            elapsed_time = pygame.time.get_ticks() - item_start_time
            remaining_time = max(0, 4000 - elapsed_time) // 1000

            time_text = font.render(f"Item Time: {remaining_time}s", True, (255, 0, 0))
            SCREEN.blit(time_text, (10, 10))

            if elapsed_time >= 4000:
                item_active = False
                player.deactivate_item()

        if gun_visible:
            gun.update()
            gun.draw(SCREEN)

            if player.hitbox.colliderect(gun.rect):
                play_sound(ITEM_COLLECT_SOUND)
                gun.collect()
                player.add_ammo(1)
                gun_visible = False
                gun_reset_time = pygame.time.get_ticks()

        if player.ammo > 0:
            ammo_text = font.render(f"🔫 Đạn: {player.ammo}", True, (255, 165, 0))
            SCREEN.blit(ammo_text, (10, 40))

        try:
            for bullet in player.bullet_list:
                if bullet.active:
                    bullet.update()
            
            for bullet in player.bullet_list:
                if bullet.active:
                    bullet.draw(SCREEN)
            
            bullets_to_remove = []
            obstacles_to_remove = []
            
            for bullet in player.bullet_list:
                if not bullet.active:
                    continue
                    
                if bullet.rect.x > SCREEN_WIDTH:
                    bullet.active = False
                    bullets_to_remove.append(bullet)
                    continue
                
                hit_obstacle = False
                for obstacle in obstacles:
                    if bullet.rect.colliderect(obstacle.rect):
                        play_sound(BOOM_SOUND)
                        bullet.active = False
                        bullets_to_remove.append(bullet)
                        obstacles_to_remove.append(obstacle)
                        hit_obstacle = True
                        break
                
                if hit_obstacle:
                    break
            
            for bullet in bullets_to_remove:
                if bullet in player.bullet_list:
                    player.bullet_list.remove(bullet)
            
            for obstacle in obstacles_to_remove:
                if obstacle in obstacles:
                    obstacles.remove(obstacle)
                    
        except Exception as e:
            print(f"Error in bullet logic: {e}")
            player.bullet_list.clear()

        player.draw(SCREEN)
        player.update(userInput, virtual_input if mobile_mode else None)

        if len(obstacles) == 0:
            rand_num = random.randint(0, 4)
            if rand_num == 0:
                obstacles.append(SmallCactus(SMALL_CACTUS))
            elif rand_num == 1:
                obstacles.append(LargeCactus(LARGE_CACTUS))
            elif rand_num == 2:
                obstacles.append(Bird(BIRD))
            elif rand_num == 3:
                obstacles.append(Spikes(SPIKES))
            elif rand_num == 4:
                obstacles.append(Rock(ROCK))

        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()
            if player.hitbox.colliderect(obstacle.rect):
                play_sound(DIE_SOUND)
                await asyncio.sleep(2)
                death_count += 1
                await menu(death_count)
                return

        background()

        for cloud in clouds:
            cloud.draw(SCREEN)
            cloud.update()

        score()
        
        # Vẽ virtual controls chỉ khi đã phát hiện touch hoặc mobile mode
        if (mobile_mode or touch_detected) and virtual_controls:
            virtual_controls.draw(SCREEN)

        clock.tick(30)
        pygame.display.update()
        await asyncio.sleep(0)


async def menu(death_count):
    global points, SCREEN, SCREEN_WIDTH, SCREEN_HEIGHT
    run = True
    button_start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
    button_exit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 120, 200, 50)
    audio_enabled = False

    while run:
        SCREEN.fill((255, 255, 255))
        font = pygame.font.SysFont('arial', 30)

        if death_count == 0:
            text = font.render("Thánh Long K'uhul Ajaw Toàn Năng!", True, (0, 0, 0))
            small_font = pygame.font.SysFont('arial', 16)
            audio_hint = small_font.render("(Click để kích hoạt âm thanh)", True, (128, 128, 128))
            audio_hint_rect = audio_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            SCREEN.blit(audio_hint, audio_hint_rect)
            
            # Hiển thị hướng dẫn controls
            if is_mobile():
                control_hint = small_font.render("Sử dụng nút ảo trên màn hình để điều khiển", True, (100, 100, 100))
                control_hint_rect = control_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200))
                SCREEN.blit(control_hint, control_hint_rect)
        elif death_count > 0:
            text = font.render("Nhấn nút bên dưới để chơi lại", True, (0, 0, 0))
            score = font.render("Điểm của bạn: " + str(points), True, (0, 0, 0))
            scoreRect = score.get_rect()
            scoreRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
            SCREEN.blit(score, scoreRect)

        textRect = text.get_rect()
        textRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        SCREEN.blit(text, textRect)

        pygame.draw.rect(SCREEN, (0, 150, 0), button_start_rect)
        button_start_text = font.render("Bắt đầu", True, (255, 255, 255))
        button_start_text_rect = button_start_text.get_rect(center=button_start_rect.center)
        SCREEN.blit(button_start_text, button_start_text_rect)

        pygame.draw.rect(SCREEN, (150, 0, 0), button_exit_rect)
        button_exit_text = font.render("Thoát", True, (255, 255, 255))
        button_exit_text_rect = button_exit_text.get_rect(center=button_exit_rect.center)
        SCREEN.blit(button_exit_text, button_exit_text_rect)

        SCREEN.blit(RUNNING[0], (SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 - 140))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            # Xử lý resize
            if event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                button_start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
                button_exit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 120, 200, 50)
                print(f"Menu resized to: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
            
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                if not audio_enabled:
                    try:
                        pygame.mixer.unpause()
                        audio_enabled = True
                        print("Audio enabled!")
                    except:
                        pass
                
                if event.type == pygame.FINGERDOWN:
                    pos = (int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT))
                else:
                    pos = event.pos
                    
                if button_start_rect.collidepoint(pos):
                    await main()
                    return
                elif button_exit_rect.collidepoint(pos):
                    pygame.quit()
                    return
        
        await asyncio.sleep(0)


# Entry point
asyncio.run(menu(death_count=0))