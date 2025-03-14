# powerup.py
import pygame
import random

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, offset, power_type):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.power_type = power_type  # "shield", "double_shot" vb.

        # PowerUp’ın görünümü (basit bir dikdörtgen veya resim):
        if self.power_type == "shield":
            self.image = pygame.Surface((30, 30))
            self.image.fill((0, 255, 255))  # Turkuaz renk
        else:
            self.image = pygame.Surface((30, 30))
            self.image.fill((255, 128, 0))  # Turuncu renk

        self.rect = self.image.get_rect()

        # PowerUp’ı ekranın üstünde rastgele bir x konumunda başlatıp aşağı doğru hareket ettirebiliriz
        self.rect.x = random.randint(int(self.offset), int(self.screen_width + self.offset - 30))
        self.rect.y = 0

        self.speed_y = 2  # Dikey hız

    def update(self):
        self.rect.y += self.speed_y
        # Ekrandan çıkarsa kendini yok et
        if self.rect.y > self.screen_height + 100:
            self.kill()
