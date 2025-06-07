import pygame
import random
from laser import Laser

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, health=10, level=1):
        super().__init__()
        self.move_direction = 1  # ⬅ En üstte olmalı

        try:
            if level == 10:
                original_image = pygame.image.load("Graphics/boss_hakan.png").convert_alpha()
            else:
                original_image = pygame.image.load("Graphics/mystery.png").convert_alpha()
            self.image = pygame.transform.scale(original_image, (80, 60))
        except:
            self.image = pygame.Surface((80, 60))
            self.image.fill((255, 0, 0))

        self.rect = self.image.get_rect(center=(x, y))

        # 💥 Sağlık değerleri
        if level == 10:
            self.health = 20
        else:
            self.health = health

        self.max_health = self.health  # 💡 Eksik olan satır buydu!


    def update(self, laser_group, screen_width):
        self.rect.x += 4 * self.move_direction
        if self.rect.right >= screen_width or self.rect.left <= 0:
            self.move_direction *= -1

        if random.randint(0, 50) == 0:
            fire_positions = [
                (self.rect.centerx - 40, self.rect.bottom),
                (self.rect.centerx, self.rect.bottom),
                (self.rect.centerx + 40, self.rect.bottom),
                (self.rect.centerx - 20, self.rect.bottom - 20),
                (self.rect.centerx + 20, self.rect.bottom - 20)
            ]
            for pos in fire_positions:
                laser_group.add(Laser(pos, 2, 800, direction="down"))
