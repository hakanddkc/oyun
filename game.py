import pygame, random
from spaceship import Spaceship
from obstacle import Obstacle
from obstacle import grid
from alien import Alien
from laser import Laser
from alien import MysteryShip
from powerup import PowerUp  # Yeni: PowerUp sınıfı

# Coin işlemleri için fonksiyonlar
def load_coins_from_file():
    try:
        with open("coins.txt", "r") as file:
            return int(file.read().strip())
    except Exception:
        return 500  # Varsayılan başlangıç parası

def save_coins_to_file(coins):
    with open("coins.txt", "w") as file:
        file.write(str(coins))

class Game:
    def __init__(self, screen_width, screen_height, offset, level=1):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.level = level  # Seçilen level burada saklanır.
        self.spaceship_group = pygame.sprite.GroupSingle()
        self.spaceship_group.add(Spaceship(self.screen_width, self.screen_height, self.offset))
        self.obstacles = self.create_obstacles()
        self.aliens_group = pygame.sprite.Group()
        self.create_aliens()
        self.aliens_direction = 1
        self.alien_lasers_group = pygame.sprite.Group()
        self.mystery_ship_group = pygame.sprite.GroupSingle()
        self.lives = 3  # Oyuncunun başlangıç canı
        self.run = True
        self.score = 0
        self.highscore = 0
        # Coin değeri artık sabit 500 yerine, dosyadan yükleniyor.
        self.coins = load_coins_from_file()
        self.explosion_sound = pygame.mixer.Sound("Sounds/explosion.ogg")
        self.load_highscore()
        pygame.mixer.music.load("Sounds/music.ogg")
        pygame.mixer.music.play(-1)

        # Güçlendirme (power-up) sistemi
        self.powerups_group = pygame.sprite.Group()
        self.has_shield = False
        self.has_double_shot = False
        self.powerup_timer = 0
        self.powerup_duration = 600  # Yaklaşık 10 saniye (60 FPS'de 600 frame)

    def create_obstacles(self):
        obstacle_width = len(grid[0]) * 3
        gap = (self.screen_width + self.offset - (4 * obstacle_width)) / 5
        obstacles = []
        for i in range(4):
            offset_x = (i + 1) * gap + i * obstacle_width
            obstacle = Obstacle(offset_x, self.screen_height - 100)
            obstacles.append(obstacle)
        return obstacles

    def create_aliens(self):
        # Seviye arttıkça alien satır sayısı artar:
        rows = 5 + (self.level - 1)  # Level 1: 5 satır, Level 2: 6 satır, vb.
        columns = 11
        for row in range(rows):
            for column in range(columns):
                x = 75 + column * 55
                y = 110 + row * 55
                if row == 0:
                    alien_type = 3
                elif row in (1, 2):
                    alien_type = 2
                else:
                    alien_type = 1
                alien = Alien(alien_type, x + self.offset / 2, y)
                self.aliens_group.add(alien)

    def move_aliens(self):
        self.aliens_group.update(self.aliens_direction)
        for alien in self.aliens_group.sprites():
            if alien.rect.right >= self.screen_width + self.offset / 2:
                self.aliens_direction = -1
                self.alien_move_down(2)
            elif alien.rect.left <= self.offset / 2:
                self.aliens_direction = 1
                self.alien_move_down(2)

    def alien_move_down(self, distance):
        for alien in self.aliens_group.sprites():
            alien.rect.y += distance

    def alien_shoot_laser(self):
        if self.aliens_group.sprites():
            random_alien = random.choice(self.aliens_group.sprites())
            laser_sprite = Laser(random_alien.rect.center, -6, self.screen_height)
            self.alien_lasers_group.add(laser_sprite)

    def create_mystery_ship(self):
        self.mystery_ship_group.add(MysteryShip(self.screen_width, self.offset))

    def create_powerup(self):
        # Rastgele "shield" veya "double_shot" güçlendirmesi oluştur
        power_type = random.choice(["shield", "double_shot"])
        powerup_sprite = PowerUp(self.screen_width, self.screen_height, self.offset, power_type)
        self.powerups_group.add(powerup_sprite)

    def check_for_collisions(self):
        # Spaceship Laser'ları: Uzay gemisinin ateşi
        if self.spaceship_group.sprite.lasers_group:
            for laser_sprite in self.spaceship_group.sprite.lasers_group:
                aliens_hit = pygame.sprite.spritecollide(laser_sprite, self.aliens_group, True)
                if aliens_hit:
                    self.explosion_sound.play()
                    for alien in aliens_hit:
                        self.score += alien.type * 100
                        self.check_for_highscore()
                        # Her düşman öldürünce, alien türüne göre coin ekle (örneğin: tür * 20)
                        self.coins += alien.type * 20
                        laser_sprite.kill()
                if pygame.sprite.spritecollide(laser_sprite, self.mystery_ship_group, True):
                    self.score += 500
                    self.explosion_sound.play()
                    self.check_for_highscore()
                    self.coins += 100  # Mystery ship vurulduğunda 100 coin
                    laser_sprite.kill()
                # PowerUp çarpışması
                powerups_hit = pygame.sprite.spritecollide(laser_sprite, self.powerups_group, True)
                if powerups_hit:
                    laser_sprite.kill()
                    for pu in powerups_hit:
                        if pu.power_type == "shield":
                            self.has_shield = True
                            self.powerup_timer = self.powerup_duration
                        elif pu.power_type == "double_shot":
                            self.has_double_shot = True
                            self.powerup_timer = self.powerup_duration
                for obstacle in self.obstacles:
                    if pygame.sprite.spritecollide(laser_sprite, obstacle.blocks_group, True):
                        laser_sprite.kill()

        # Alien Laser'ları: Düşman ateşi
        if self.alien_lasers_group:
            for laser_sprite in self.alien_lasers_group:
                if pygame.sprite.spritecollide(laser_sprite, self.spaceship_group, False):
                    laser_sprite.kill()
                    if not self.has_shield:
                        self.lives -= 1
                        if self.lives <= 0:
                            self.game_over()
                    else:
                        self.has_shield = False
                        self.powerup_timer = 0
                for obstacle in self.obstacles:
                    if pygame.sprite.spritecollide(laser_sprite, obstacle.blocks_group, True):
                        laser_sprite.kill()

        # Alien'ler: Uzay gemisine temas ederse
        if self.aliens_group:
            for alien in self.aliens_group:
                for obstacle in self.obstacles:
                    pygame.sprite.spritecollide(alien, obstacle.blocks_group, True)
                if pygame.sprite.spritecollide(alien, self.spaceship_group, False):
                    if not self.has_shield:
                        self.lives -= 1
                    else:
                        self.has_shield = False
                        self.powerup_timer = 0
                    alien.kill()
                    if self.lives <= 0:
                        self.game_over()

    def update_powerup_status(self):
        if self.powerup_timer > 0:
            self.powerup_timer -= 1
        else:
            self.has_shield = False
            self.has_double_shot = False

    def game_over(self):
        self.run = False

    def reset(self):
        self.run = True
        self.lives = 3
        self.spaceship_group.sprite.reset()
        self.aliens_group.empty()
        self.alien_lasers_group.empty()
        self.powerups_group.empty()
        self.create_aliens()
        self.mystery_ship_group.empty()
        self.obstacles = self.create_obstacles()
        self.score = 0
        # self.coins burada resetlenmiyor; mevcut coin değeri korunuyor.
        self.has_shield = False
        self.has_double_shot = False
        self.powerup_timer = 0
        self.defeat = False

    def next_level(self):
        self.level += 1
        self.run = True
        self.lives = 3  # Yeni levelde can sıfırlansın
        self.aliens_group.empty()
        self.alien_lasers_group.empty()
        self.mystery_ship_group.empty()
        self.powerups_group.empty()
        self.obstacles = self.create_obstacles()
        self.create_aliens()

    def check_for_highscore(self):
        if self.score > self.highscore:
            self.highscore = self.score
            with open("highscore.txt", "w") as file:
                file.write(str(self.highscore))

    def load_highscore(self):
        try:
            with open("highscore.txt", "r") as file:
                self.highscore = int(file.read())
        except FileNotFoundError:
            self.highscore = 0
