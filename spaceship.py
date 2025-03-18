import pygame
from laser import Laser

class Spaceship(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, offset, spaceship_image_path="Graphics/spaceship.png"):
        super().__init__()
        self.offset = offset
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 1) Gemi resmini yükle
        raw_image = pygame.image.load(spaceship_image_path).convert_alpha()

        # 2) Örneğin 80x80 piksele ölçekleyelim
        scaled_image = pygame.transform.scale(raw_image, (80, 80))
        self.image = scaled_image

        # 3) Yeni self.image'e göre rect ayarlayalım
        self.rect = self.image.get_rect(midbottom=((self.screen_width + self.offset)//2, self.screen_height))

        self.speed = 6
        self.lasers_group = pygame.sprite.Group()
        self.laser_ready = True
        self.laser_time = 0
        self.laser_delay = 300
        self.laser_sound = pygame.mixer.Sound("Sounds/laser.ogg")

    def get_user_input(self):
        keys = pygame.key.get_pressed()

        # Sağ ok tuşu veya D tuşu ile sağa hareket
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed

        # Sol ok tuşu veya A tuşu ile sola hareket
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed

        # Ateş (Space)
        if keys[pygame.K_SPACE] and self.laser_ready:
            self.laser_ready = False
            laser = Laser(self.rect.center, 5, self.screen_height)
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
        if self.rect.right > self.screen_width:
            self.rect.right = self.screen_width
        # Sol (offset) sınır
        if self.rect.left < self.offset:
            self.rect.left = self.offset

    def recharge_laser(self):
        """ Belli bir gecikmeden sonra tekrar ateşlenebilir. """
        if not self.laser_ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_time >= self.laser_delay:
                self.laser_ready = True

    def reset(self):
        """
        Can kaybı veya level reset durumunda
        gemiyi tekrar taban konuma alır ve lasers_group'u boşaltır.
        """
        self.rect = self.image.get_rect(midbottom=((self.screen_width + self.offset)//2, self.screen_height))
        self.lasers_group.empty()
