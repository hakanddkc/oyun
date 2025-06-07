import pygame
import random
import os

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, offset, power_type="life"):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.power_type = power_type  # Sadece "life" buff'ı desteklenir

        # PowerUp resmi
        powerup_image = "Graphics/life_powerup.png"

        # Resmi yükle, yoksa varsayılan yüzey kullan
        if os.path.exists(powerup_image):
            self.image = pygame.image.load(powerup_image).convert_alpha()
            # Resmi 30x30 boyutuna ölçeklendir
            self.image = pygame.transform.scale(self.image, (30, 30))
        else:
            # Resim bulunamazsa turuncu bir dikdörtgen oluştur
            self.image = pygame.Surface((30, 30))
            self.image.fill((255, 128, 0))  # Turuncu renk

        self.rect = self.image.get_rect()

        # PowerUp'ı ekranın üstünde rastgele bir x konumunda başlat
        self.rect.x = random.randint(int(self.offset), int(self.screen_width + self.offset - 30))
        self.rect.y = 0

        self.speed_y = 2  # Dikey hareket hızı

    def update(self):
        self.rect.y += self.speed_y
        # PowerUp ekranın altına çıkarsa yok edilir
        if self.rect.y > self.screen_height + 100:
            self.kill()