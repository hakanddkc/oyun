import pygame
import random
from laser import Laser

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, health=10):
        super().__init__()
        try:
            original_image = pygame.image.load("Graphics/mystery.png").convert_alpha()
            # 🔴 Burada boss boyutu yeniden ölçekleniyor
            self.image = pygame.transform.scale(original_image, (80, 60))  # Genişlik: 80, Yükseklik: 60
        except:
            self.image = pygame.Surface((80, 60))
            self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.health = health
        self.max_health = health
        self.move_direction = 1  # Sağa başlasın

    def update(self, laser_group, screen_width):
        # 🔁 Sağa-sola hareket
        self.rect.x += 2 * self.move_direction
        if self.rect.right >= screen_width or self.rect.left <= 0:
            self.move_direction *= -1  # Yön değiştir

        # 🔫 Ateş etme şansı
        if random.randint(0, 30) == 0:
            fire_positions = [
                (self.rect.centerx - 40, self.rect.bottom),
                (self.rect.centerx, self.rect.bottom),
                (self.rect.centerx + 40, self.rect.bottom),
                (self.rect.centerx - 20, self.rect.bottom - 20),
                (self.rect.centerx + 20, self.rect.bottom - 20)
            ]
            for pos in fire_positions:
                laser_group.add(Laser(pos, 6, 800, direction="down"))  # ⬇ Boss aşağı ateş eder
