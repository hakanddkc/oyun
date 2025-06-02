import pygame

class Laser(pygame.sprite.Sprite):
    def __init__(self, position, speed, screen_height, direction="up"):
        super().__init__()

        # Füze resmi yükleniyor, hata durumunda görünür bir kırmızı dikdörtgen atanıyor
        try:
            raw_image = pygame.image.load("Graphics/fuze.png").convert_alpha()
            scaled_image = pygame.transform.scale(raw_image, (10, 30))
            self.image = scaled_image
        except:
            self.image = pygame.Surface((10, 30))
            self.image.fill((255, 0, 0))  # Görünürlük için kırmızı

        self.rect = self.image.get_rect(center=position)
        self.speed = speed
        self.screen_height = screen_height
        self.direction = direction.lower()  # Küçük harfe dönüştür, güvenli karşılaştırma için

    def update(self):
        if self.direction == "up":
            self.rect.y -= self.speed
            if self.rect.bottom < 0:
                self.kill()
        elif self.direction == "down":
            self.rect.y += self.speed
            if self.rect.top > self.screen_height:
                self.kill()
