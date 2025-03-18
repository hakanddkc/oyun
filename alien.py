import pygame, random

class Alien(pygame.sprite.Sprite):
    def __init__(self, type, x, y):
        super().__init__()
        self.type = type
        path = f"Graphics/alien_{type}.png"
        self.image = pygame.image.load(path)

        # Resmi boyutlandırıyoruz
        self.image = pygame.transform.scale(self.image, (40, 40))  # Boyutları küçültüyoruz (örneğin 40x40)

        # Uzaylıyı ekranda düzgün konumlandırıyoruz
        self.rect = self.image.get_rect(topleft = (x, y))

    def update(self, direction):
        self.rect.x += direction


class MysteryShip(pygame.sprite.Sprite):
    def __init__(self, screen_width, offset):
        super().__init__()
        self.screen_width = screen_width
        self.offset = offset
        self.image = pygame.image.load("Graphics/mystery.png")

        # Mystery Ship için boyutları küçültüyoruz
        self.image = pygame.transform.scale(self.image, (60, 40))  # Boyutları küçültüyoruz (örneğin 60x40)

        # Hareket yönünü belirliyoruz
        x = random.choice([self.offset/2, self.screen_width + self.offset - self.image.get_width()])
        if x == self.offset/2:
            self.speed = 3
        else:
            self.speed = -3

        self.rect = self.image.get_rect(topleft = (x, 90))

    def update(self):
        self.rect.x += self.speed
        if self.rect.right > self.screen_width + self.offset/2:
            self.kill()
        elif self.rect.left < self.offset/2:
            self.kill()
