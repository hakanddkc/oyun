# powerup.py
import pygame
import random
import os

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, offset, power_type):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.power_type = power_type  # Örneğin: "shield", "double_shot" vb.

        # PowerUp resimlerini tanımlayan sözlük.
        # PNG dosyalarınızın doğru yolda olduğundan emin olun.
        powerup_images = {
            "shield": "Graphics/shield_powerup.png",
            "double_shot": "Graphics/double_shot_powerup.png"
            # İhtiyacınıza göre başka güç türleri de ekleyebilirsiniz.
        }

        # Eğer tanımlı güç türüne ait bir resim varsa yükle, yoksa varsayılan bir yüzey kullan.
        if power_type in powerup_images and os.path.exists(powerup_images[power_type]):
            self.image = pygame.image.load(powerup_images[power_type]).convert_alpha()
            # İsteğe bağlı: Resmi 30x30 boyutuna ölçeklendiriyoruz.
            self.image = pygame.transform.scale(self.image, (30, 30))
        else:
            # Eğer PNG dosyası bulunamazsa, farklı renkte bir dikdörtgen oluşturulur.
            self.image = pygame.Surface((30, 30))
            if power_type == "shield":
                self.image.fill((0, 255, 255))  # Turkuaz renk
            else:
                self.image.fill((255, 128, 0))  # Turuncu renk

        self.rect = self.image.get_rect()

        # PowerUp’ı ekranın üstünde rastgele bir x konumunda başlatıp aşağı doğru hareket ettirir.
        self.rect.x = random.randint(int(self.offset), int(self.screen_width + self.offset - 30))
        self.rect.y = 0

        self.speed_y = 2  # Dikey hareket hızı

    def update(self):
        self.rect.y += self.speed_y
        # PowerUp ekranın altına çıkarsa, yok edilir.
        if self.rect.y > self.screen_height + 100:
            self.kill()
