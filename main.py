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

SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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
        
        # Tạo hitbox nhỏ hơn - KHÔNG dùng inflate_ip
        self.hitbox = pygame.Rect(
            self.dino_rect.x + 20,
            self.dino_rect.y + 20,
            self.dino_rect.width - 40,
            self.dino_rect.height - 40
        )
        
        self.ammo = 0  # Số đạn hiện có
        self.last_shot_time = 0
        self.shoot_cooldown = 500
        self.bullet_list = []
        self.is_shooting = False

    def shoot(self):
        """Bắn một viên đạn nếu còn đạn"""
        try:
            if self.ammo > 0:
                bullet = Bullet(self.dino_rect.right, self.dino_rect.centery)
                self.bullet_list.append(bullet)
                self.ammo -= 1
                print(f"Shot fired! Ammo left: {self.ammo}")  # Debug
        except Exception as e:
            print(f"Error shooting: {e}")

    def add_ammo(self, amount=1):
        """Thêm đạn khi nhặt súng"""
        self.ammo += amount
    
    def has_ammo(self):
        """Kiểm tra còn đạn không"""
        return self.ammo > 0

    def update(self, userInput):
        if self.dino_duck:
            self.duck()
        if self.dino_run:
            self.run()
        if self.dino_jump:
            self.jump()

        if self.step_index >= 10:
            self.step_index = 0

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
            
        if self.using_item:
            if userInput[pygame.K_LEFT]:
                self.dino_rect.x -= self.MOVE_VEL  
            if userInput[pygame.K_RIGHT]:
                self.dino_rect.x += self.MOVE_VEL
                
            if self.dino_rect.x < 0:
                self.dino_rect.x = 0
            if self.dino_rect.x > SCREEN_WIDTH - self.dino_rect.width:
                self.dino_rect.x = SCREEN_WIDTH - self.dino_rect.width
        
        # Cập nhật hitbox theo vị trí dino
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
        # Debug: vẽ hitbox (có thể bỏ comment để test)
        # pygame.draw.rect(SCREEN, (255, 0, 0), self.hitbox, 2)


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
            # Nếu không load được hình, tạo bullet đơn giản
            self.image = pygame.Surface((10, 5))
            self.image.fill((255, 255, 0))
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.active = True  # Đánh dấu đạn còn hoạt động

    def update(self):
        if self.active:
            self.rect.x += 20

    def draw(self, screen):
        if self.active:
            screen.blit(self.image, self.rect)


# Import Item và Gun
try:
    from item import Item, Gun
except ImportError:
    print("Error: Cannot import Item and Gun classes")
    # Tạo dummy classes nếu không import được
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
    global game_speed, x_pos_bg, y_pos_bg, points, obstacles, item_visible
    run = True
    clock = pygame.time.Clock()
    player = Dinosaur()
    clouds = [Cloud() for _ in range(8)]
    game_speed = 20
    x_pos_bg = 0
    y_pos_bg = 370
    points = 0
    # Dùng font hệ thống thay vì load file
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
    gun_spawned = False
    gun_reset_time = 0
    gun_spawn_counter = 0  # Bộ đếm để spawn súng thường xuyên hơn
    
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
        textRect.center = (1000, 40)
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
        
        if paused:
            pause_text = font.render("Tạm dừng - Nhấn P để tiếp tục", True, (255, 0, 0))
            pause_text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            SCREEN.blit(pause_text, pause_text_rect)
            pygame.display.update()
            clock.tick(5)
            await asyncio.sleep(0)
            continue
        
        userInput = pygame.key.get_pressed()
        
        # Xử lý bắn đạn với cooldown - SỬA LẠI
        current_time = pygame.time.get_ticks()
        try:
            if userInput[pygame.K_SPACE]:
                if player.has_ammo() and (current_time - player.last_shot_time > player.shoot_cooldown):
                    player.shoot()
                    player.last_shot_time = current_time
                elif not player.has_ammo():
                    # Thông báo hết đạn (optional)
                    pass
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

        # Logic spawn súng mới - xuất hiện thường xuyên hơn
        gun_spawn_counter += 1
        
        # Mỗi 150-300 frames (khoảng 5-10 giây) kiểm tra spawn súng
        if gun_spawn_counter >= random.randint(150, 300) and not gun_visible:
            if random.randint(0, 99) < 60:  # 60% cơ hội xuất hiện
                gun.reset()
                gun_visible = True
                gun_spawn_counter = 0  # Reset counter
        
        # Reset counter nếu quá lớn
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
                player.add_ammo(1)  # Thêm 1 viên đạn
                gun_visible = False
                gun_reset_time = pygame.time.get_ticks()

        # Vẽ thông tin về đạn
        if player.ammo > 0:
            ammo_text = font.render(f"🔫 Đạn: {player.ammo}", True, (255, 165, 0))
            SCREEN.blit(ammo_text, (10, 40))
        
        # Hiển thị số đạn đang bay
        if len(player.bullet_list) > 0:
            bullet_text = font.render(f"Đang bay: {len(player.bullet_list)}", True, (255, 255, 0))
            SCREEN.blit(bullet_text, (10, 70))

        # Xử lý đạn và va chạm - SỬA LẠI LOGIC AN TOÀN
        try:
            # Cập nhật tất cả đạn trước
            for bullet in player.bullet_list:
                if bullet.active:
                    bullet.update()
            
            # Vẽ đạn
            for bullet in player.bullet_list:
                if bullet.active:
                    bullet.draw(SCREEN)
            
            # Kiểm tra va chạm và đánh dấu để xóa
            bullets_to_remove = []
            obstacles_to_remove = []
            
            for bullet in player.bullet_list:
                if not bullet.active:
                    continue
                    
                # Kiểm tra ra khỏi màn hình
                if bullet.rect.x > SCREEN_WIDTH:
                    bullet.active = False
                    bullets_to_remove.append(bullet)
                    continue
                
                # Kiểm tra va chạm với obstacles
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
            
            # Xóa đạn đã đánh dấu
            for bullet in bullets_to_remove:
                if bullet in player.bullet_list:
                    player.bullet_list.remove(bullet)
            
            # Xóa obstacles đã đánh dấu
            for obstacle in obstacles_to_remove:
                if obstacle in obstacles:
                    obstacles.remove(obstacle)
                    
        except Exception as e:
            print(f"Error in bullet logic: {e}")
            # Nếu có lỗi, clear tất cả đạn để tránh crash
            player.bullet_list.clear()

        player.draw(SCREEN)
        player.update(userInput)

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

        clock.tick(30)
        pygame.display.update()
        await asyncio.sleep(0)


async def menu(death_count):
    global points
    run = True
    button_start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
    button_exit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 120, 200, 50)
    audio_enabled = False  # Flag để track audio đã enable chưa

    while run:
        SCREEN.fill((255, 255, 255))
        # Dùng font hệ thống
        font = pygame.font.SysFont('arial', 30)

        if death_count == 0:
            text = font.render("Thánh Long K'uhul Ajaw Toàn Năng!", True, (0, 0, 0))
            # Thêm hướng dẫn về audio
            small_font = pygame.font.SysFont('arial', 16)
            audio_hint = small_font.render("(Click để kích hoạt âm thanh)", True, (128, 128, 128))
            audio_hint_rect = audio_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            SCREEN.blit(audio_hint, audio_hint_rect)
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Kích hoạt audio khi user click
                if not audio_enabled:
                    try:
                        pygame.mixer.unpause()
                        audio_enabled = True
                        print("Audio enabled!")
                    except:
                        pass
                
                if button_start_rect.collidepoint(event.pos):
                    await main()
                    return
                elif button_exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    return
        
        await asyncio.sleep(0)


# Entry point
asyncio.run(menu(death_count=0))