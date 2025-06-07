import pygame

class Laser(pygame.sprite.Sprite):
    def __init__(self, position, speed, screen_height, direction="up"):
        super().__init__()
        self.direction = direction.lower()  # Güvenli karşılaştırma

        try:
            if self.direction == "down":
                raw_image = pygame.image.load("Graphics/boss_laser.png").convert_alpha()
                scaled_image = pygame.transform.scale(raw_image, (12, 35))
            else:
                raw_image = pygame.image.load("Graphics/fuze.png").convert_alpha()
                scaled_image = pygame.transform.scale(raw_image, (10, 30))
            self.image = scaled_image
        except:
            # Hata durumunda görünür renkli dikdörtgenlerle ayır
            if self.direction == "down":
                self.image = pygame.Surface((12, 35))
                self.image.fill((255, 100, 0))  # Turuncu: boss lazeri
            else:
                self.image = pygame.Surface((10, 30))
                self.image.fill((0, 255, 0))  # Yeşil: oyuncu lazeri

        self.rect = self.image.get_rect(center=position)
        self.speed = speed
        self.screen_height = screen_height

    def update(self):
        if self.direction == "up":
            self.rect.y -= self.speed
            if self.rect.bottom < 0:
                self.kill()
        elif self.direction == "down":
            self.rect.y += self.speed
            if self.rect.top > self.screen_height:
                self.kill()
