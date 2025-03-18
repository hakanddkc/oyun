import pygame

class Laser(pygame.sprite.Sprite):
    def __init__(self, position, speed, screen_height):
        super().__init__()
        # Füze resmini yükle
        raw_image = pygame.image.load("Graphics/fuze.png").convert_alpha()
        # Örneğin, 10x30 piksele ölçekleyelim (füze boyutu için uygun bir oran seçebilirsin)
        self.image = pygame.transform.scale(raw_image, (10, 30))
        self.rect = self.image.get_rect(center=position)
        self.speed = speed
        self.screen_height = screen_height

    def update(self):
        self.rect.y -= self.speed
        if self.rect.y > self.screen_height + 15 or self.rect.y < 0:
            self.kill()