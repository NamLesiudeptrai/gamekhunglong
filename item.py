import pygame
import random
import os


class Item:
    def __init__(self):
        # Sử dụng os.path.join để đảm bảo đường dẫn đúng trên mọi platform
        self.image = pygame.image.load(os.path.join("Assets", "Other", "Chicken.png"))
        self.rect = self.image.get_rect()
        self.is_collected = False
        self.reset()

    def reset(self):
        """Đặt lại vị trí item"""
        self.rect.x = 1200
        self.rect.y = random.randint(50, 300)  # Tránh spawn quá thấp
        self.is_collected = False

    def update(self):
        """Cập nhật vị trí item"""
        if not self.is_collected:
            self.rect.x -= 20
            if self.rect.x < -self.rect.width:
                self.reset()

    def draw(self, screen):
        """Vẽ item lên màn hình"""
        if not self.is_collected:
            screen.blit(self.image, self.rect)

    def collect(self):
        """Đánh dấu item đã được thu thập"""
        self.is_collected = True


class Gun:
    def __init__(self):
        # Sử dụng os.path.join để đảm bảo đường dẫn đúng
        self.image = pygame.image.load(os.path.join("Assets", "Other", "gun.png"))
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.visible = False
        self.float_offset = 0  # Hiệu ứng nổi
        self.float_direction = 1
        self.reset()

    def reset(self):
        """Đặt lại vị trí gun khi xuất hiện"""
        self.rect.x = random.randint(800, 1000)
        self.rect.y = random.randint(250, 350)
        self.visible = True
        self.float_offset = 0

    def update(self):
        """Cập nhật vị trí gun - di chuyển từ phải sang trái"""
        if self.visible:
            self.rect.x -= 6  # Tăng tốc độ di chuyển
            
            # Hiệu ứng nổi lên xuống
            self.float_offset += 0.15 * self.float_direction
            if abs(self.float_offset) > 10:
                self.float_direction *= -1
            
            # Ẩn gun nếu đi ra khỏi màn hình
            if self.rect.x < -self.rect.width:
                self.visible = False

    def draw(self, screen):
        """Vẽ gun lên màn hình với hiệu ứng nổi"""
        if self.visible:
            # Vẽ với offset để tạo hiệu ứng nổi
            draw_y = self.rect.y + self.float_offset
            screen.blit(self.image, (self.rect.x, draw_y))
            
            # Vẽ text "+1 đạn" phía trên súng
            font = pygame.font.SysFont('arial', 14)
            text = font.render("+1 đạn", True, (255, 215, 0))
            text_rect = text.get_rect(center=(self.rect.centerx, draw_y - 20))
            screen.blit(text, text_rect)

    def collect(self):
        """Xử lý khi gun được thu thập"""
        self.visible = False