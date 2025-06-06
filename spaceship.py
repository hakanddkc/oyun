import pygame
from laser import Laser

class Spaceship(pygame.sprite.Sprite):
    def __init__(
        self,
        screen_width,
        screen_height,
        offset,
        image_path="Graphics/spaceship.png",
        health=3,
        shots=1
    ):
        super().__init__()
        # Temel parametreler
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset

        # Gemi özellikleri
        self.max_health = health
        self.health = health
        self.max_shots = shots

        # Gemi görselini yükle ve ölçekle
        raw_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(raw_image, (80, 80))
        self.rect = self.image.get_rect(
            midbottom=((self.screen_width + self.offset) // 2, self.screen_height)
        )

        # Hareket ve atış kontrolü
        self.speed = 8
        self.lasers_group = pygame.sprite.Group()
        self.laser_ready = True
        self.laser_time = 0
        self.laser_delay = 300
        self.laser_sound = pygame.mixer.Sound("Sounds/laser.ogg")

    def get_user_input(self):
        keys = pygame.key.get_pressed()
        # Sağ/sol hareket
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed

        # Ateş etme: yukarı doğru spread atış
        if (keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.laser_ready:
            self.laser_ready = False
            cx, cy = self.rect.center
            spacing = 20
            for i in range(self.max_shots):
                offset_x = (i - (self.max_shots - 1) / 2) * spacing
                laser = Laser((cx + offset_x, cy), speed=6, screen_height=self.screen_height)
                self.lasers_group.add(laser)
            self.laser_time = pygame.time.get_ticks()
            self.laser_sound.play()

    def update(self):
        self.get_user_input()
        self.constrain_movement()
        self.lasers_group.update()
        self.recharge_laser()

    def constrain_movement(self):
        # Sağ sınır
        if self.rect.right > self.screen_width + self.offset:
            self.rect.right = self.screen_width + self.offset
        # Sol sınır
        if self.rect.left < self.offset:
            self.rect.left = self.offset

    def recharge_laser(self):
        if not self.laser_ready:
            now = pygame.time.get_ticks()
            if now - self.laser_time >= self.laser_delay:
                self.laser_ready = True

    def reset(self):
        # Gemi pozisyonu ve mermileri sıfırlama
        self.rect = self.image.get_rect(
            midbottom=((self.screen_width + self.offset) // 2, self.screen_height)
        )
        self.lasers_group.empty()
