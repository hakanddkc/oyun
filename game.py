import pygame
import random
import sqlite3
from spaceship import Spaceship
from obstacle import Obstacle, grid
from alien import Alien, MysteryShip
from laser import Laser
from powerup import PowerUp
from boss import Boss


# -----------------------------------------------------
# VERİTABANI İŞLEMLERİ
# -----------------------------------------------------
def load_coins_from_db(user_id):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def load_highscore_from_db(user_id):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM user_levels WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else 0

def update_coins_in_db(user_id, coins):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit()
    conn.close()

def update_score_in_db(user_id, score):
    conn = sqlite3.connect("game_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO user_levels (user_id, score) VALUES (?, ?)", (user_id, score))
    conn.commit()
    conn.close()


# -----------------------------------------------------
# OYUN SINIFI
# -----------------------------------------------------
class Game:
    def __init__(self, screen_width, screen_height, offset,
                 level=1, user_id=1, spaceship_image_path=None):
        # temel ayarlar
        self.muted = False
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.level = level
        self.user_id = user_id
        # Boss grubunu baştan oluştur
        self.boss_group = pygame.sprite.GroupSingle()
        if self.level >= 5:
            from boss import Boss  # boss.py içinde tanımlı boss class'ı varsa
            self.boss_group.add(Boss(self.screen_width // 2, 100, health=10))
        self.boss_active = False
        self.boss_group = pygame.sprite.GroupSingle()
        self.boss_lasers_group = pygame.sprite.Group()

        # equip edilmiş geminin özelliklerini DB'den oku
        conn = sqlite3.connect("game_data.db")
        c = conn.cursor()
        c.execute("""
            SELECT s.image_path, s.health, s.shots
            FROM ships s
            JOIN user_ships us ON s.id = us.ship_id
            WHERE us.user_id = ? AND us.is_equipped = 1
        """, (self.user_id,))
        row = c.fetchone()
        conn.close()

        if row:
            spaceship_image_path, ship_health, ship_shots = row
        else:
            spaceship_image_path = spaceship_image_path or "Graphics/default_spaceship.png"
            ship_health, ship_shots = 3, 1

        # Pygame ekran ve başlık
        pygame.display.init()
        self.screen = pygame.display.set_mode((screen_width + offset, screen_height + 2*offset))
        pygame.display.set_caption("Python Space Invaders")

        # Spaceship: health ve shots parametreleriyle
        self.spaceship_group = pygame.sprite.GroupSingle(
            Spaceship(
                screen_width, screen_height, offset,
                image_path=spaceship_image_path,
                health=ship_health,
                shots=ship_shots
            )
        )

        # can değerini geminin health'ine ayarla
        self.lives = ship_health

        # diğer gruplar ve ayarlar
        self.obstacles = self.create_obstacles()
        self.aliens_group = pygame.sprite.Group()
        self.create_aliens()
        self.aliens_direction = 1
        self.alien_lasers_group = pygame.sprite.Group()
        self.mystery_ship_group = pygame.sprite.GroupSingle()
        self.run = True
        self.score = 0
        self.highscore = load_highscore_from_db(self.user_id)
        self.coins = load_coins_from_db(self.user_id)

        # sesler
        self.explosion_sound = pygame.mixer.Sound("Sounds/explosion.ogg")
        pygame.mixer.music.load("Sounds/music.ogg")
        pygame.mixer.music.play(-1)

        # power-up
        self.powerups_group = pygame.sprite.Group()
        self.has_shield = False
        self.has_double_shot = False
        self.powerup_timer = 0
        self.powerup_duration = 600

    def toggle_music(self):
        if self.muted:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
        self.muted = not self.muted

    def update_screen(self):
        self.screen.fill((50, 50, 50))
        pygame.draw.rect(self.screen, (243,216,63), (10,10,780,780), 2)
        pygame.draw.line(self.screen, (243,216,63), (25,730), (775,730), 3)
        self.boss_group.draw(self.screen)
        self.boss_lasers_group.draw(self.screen)
        for boss in self.boss_group:
            boss.draw_health_bar(self.screen)

        # Boss varsa can barını göster
        if self.boss_group.sprite:
            boss = self.boss_group.sprite
            bar_width = 200
            bar_height = 20
            bar_x = (self.screen_width + self.offset) // 2 - bar_width // 2
            bar_y = 20
            fill = int((boss.health / boss.max_health) * bar_width)
            pygame.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))  # Arka plan
            pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, fill, bar_height))  # Doluluk

        if self.boss_active:
            self.update_boss()

        font = pygame.font.Font("Font/monogram.ttf", 40)
        # Seviye
        self.screen.blit(font.render(f"LEVEL {self.level}", True, (243,216,63)), (570,740))
        # Mute butonu
        self.create_mute_button()

        # Sprite grupları
        self.spaceship_group.draw(self.screen)
        self.spaceship_group.sprite.lasers_group.draw(self.screen)
        for obs in self.obstacles:
            obs.blocks_group.draw(self.screen)
        self.aliens_group.draw(self.screen)
        self.alien_lasers_group.draw(self.screen)
        self.mystery_ship_group.draw(self.screen)
        self.powerups_group.draw(self.screen)


        # Score / Highscore / Coins / Health
        self.screen.blit(font.render(str(self.score).zfill(5), False, (243,216,63)), (50,40))
        self.screen.blit(font.render(str(self.highscore).zfill(5), False, (243,216,63)), (550,40))
        self.screen.blit(font.render(f"Coins: {self.coins}", True, (243,216,63)), (50,80))
        small_font = pygame.font.Font("Font/monogram.ttf", 24)
        self.screen.blit(small_font.render(f"HEALTH: {self.lives}", True, (243,216,63)), (50,110))

        pygame.display.update()

    def create_mute_button(self):
        rect = pygame.Rect(self.screen_width-60, 10, 50, 50)
        icon = "volume-up" if not self.muted else "volume-mute"
        icon_img = pygame.image.load(f"Graphics/{icon}.png")
        icon_img = pygame.transform.scale(icon_img, (40,40))
        self.screen.blit(icon_img, rect)
        if pygame.mouse.get_pressed()[0] and rect.collidepoint(pygame.mouse.get_pos()):
            self.toggle_music()

    def create_obstacles(self):
        w = len(grid[0]) * 3
        gap = (self.screen_width + self.offset - 4*w) / 5
        obs = []
        for i in range(4):
            x = (i+1)*gap + i*w
            obs.append(Obstacle(x, self.screen_height-150))
        return obs

    def create_aliens(self):
        rows = min(self.level, 10)
        cols = 11
        for row in range(rows):
            for col in range(cols):
                x = 75 + col*55
                y = 110 + row*55
                t = 3 if row==0 else 2 if row==1 else 1
                self.aliens_group.add(Alien(t, x+self.offset/2, y))

    def update_boss(self):
        if not self.boss_group.sprite:
            return

        boss = self.boss_group.sprite
        boss.update(self.boss_lasers_group, self.screen_width + self.offset)

        # Boss can barı
        bar_width = 200
        bar_height = 20
        bar_x = (self.screen_width + self.offset) // 2 - bar_width // 2
        bar_y = 20
        fill = int((boss.health / boss.max_health) * bar_width)
        pygame.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, fill, bar_height))

    def move_aliens(self):
        self.aliens_group.update(self.aliens_direction)
        for alien in self.aliens_group.sprites():
            if alien.rect.right >= self.screen_width + self.offset/2:
                self.aliens_direction = -1
                self.alien_move_down(2)
            elif alien.rect.left <= self.offset/2:
                self.aliens_direction = 1
                self.alien_move_down(2)

    def alien_move_down(self, d):
        for a in self.aliens_group.sprites():
            a.rect.y += d

    def alien_shoot_laser(self):
        if self.aliens_group:
            shooter = random.choice(self.aliens_group.sprites())
            # Aşağıdan yukarıya atacak şekilde speed pozitif
            self.alien_lasers_group.add(Laser(shooter.rect.center, -6, self.screen_height))

    def create_mystery_ship(self):
        self.mystery_ship_group.add(MysteryShip(self.screen_width, self.offset))

    def create_powerup(self):
        pt = random.choice(["shield","double_shot"])
        self.powerups_group.add(PowerUp(self.screen_width, self.screen_height, self.offset, pt))

    def check_for_collisions(self):
        # Oyuncu lazerleri vs uzaylılar
        for laser in self.spaceship_group.sprite.lasers_group.copy():
            # Uzaylıya çarparsa
            hits = pygame.sprite.spritecollide(laser, self.aliens_group, True)
            if hits:
                self.explosion_sound.play()
                for a in hits:
                    self.score += a.type * 20
                    self.check_for_highscore()
                    self.coins += a.type * 1
                    update_coins_in_db(self.user_id, self.coins)
                laser.kill()

            # Boss'a çarparsa
            if pygame.sprite.spritecollide(laser, self.boss_group, False):
                laser.kill()
                boss = self.boss_group.sprite
                boss.health -= 1
                if boss.health <= 0:
                    self.score += 200
                    self.coins += 50
                    update_coins_in_db(self.user_id, self.coins)
                    self.boss_group.empty()
                    self.explosion_sound.play()

            # Gizemli gemiye çarparsa
            if pygame.sprite.spritecollide(laser, self.mystery_ship_group, True):
                self.score += 100
                self.explosion_sound.play()
                self.check_for_highscore()
                self.coins += 50
                update_coins_in_db(self.user_id, self.coins)
                laser.kill()

            # Power-up'a çarparsa
            for pu in pygame.sprite.spritecollide(laser, self.powerups_group, True):
                laser.kill()
                if pu.power_type == "shield":
                    self.has_shield = True
                    self.powerup_timer = self.powerup_duration
                else:
                    self.has_double_shot = True
                    self.powerup_timer = self.powerup_duration

            # Engel'e çarparsa
            for obs in self.obstacles:
                if pygame.sprite.spritecollide(laser, obs.blocks_group, True):
                    laser.kill()
                    break

        # Uzaylı lazerleri vs oyuncu
        for laser in self.alien_lasers_group.copy():
            if pygame.sprite.spritecollide(laser, self.spaceship_group, False):
                laser.kill()
                if not self.has_shield:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over()
                else:
                    self.has_shield = False
                    self.powerup_timer = 0
            for obs in self.obstacles:
                if pygame.sprite.spritecollide(laser, obs.blocks_group, True):
                    laser.kill()
                    break

        # Boss lazerleri vs oyuncu ve engeller
        for laser in self.boss_lasers_group.copy():
            if pygame.sprite.spritecollide(laser, self.spaceship_group, False):
                laser.kill()
                if not self.has_shield:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over()
                else:
                    self.has_shield = False
                    self.powerup_timer = 0
            for obs in self.obstacles:
                if pygame.sprite.spritecollide(laser, obs.blocks_group, True):
                    laser.kill()
                    break

        # Uzaylılar vs engel/oyuncu
        for alien in self.aliens_group.copy():
            for obs in self.obstacles:
                pygame.sprite.spritecollide(alien, obs.blocks_group, True)
            if pygame.sprite.spritecollide(alien, self.spaceship_group, False):
                if not self.has_shield:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over()
                else:
                    self.has_shield = False
                    self.powerup_timer = 0
                alien.kill()

        # Seviye tamamlandı mı kontrol et
        self.check_for_level_completion()

    def check_for_level_completion(self):
        if self.level == 5:
            # Eğer alien'lar bitti ama boss henüz gelmediyse boss oluştur
            if not self.aliens_group and not self.boss_group:
                if not hasattr(self, 'boss_spawned') or not self.boss_spawned:
                    from boss import Boss
                    self.boss_group.add(Boss(self.screen_width // 2, 100, health=10))
                    self.boss_spawned = True  # boss artık sahnede

            # boss sahneye gelmişti ama şimdi yoksa: level tamamlanmış
            elif not self.boss_group and getattr(self, 'boss_spawned', False):
                self.run = False
                self.victory = True
        else:
            # 1–4 ve 6–10. seviyelerde sadece uzaylılara göre karar ver
            if not self.aliens_group:
                self.run = False
                self.victory = True

    def update_powerup_status(self):
        if self.powerup_timer > 0:
            self.powerup_timer -= 1
        else:
            self.has_shield = False
            self.has_double_shot = False

    def game_over(self):
        self.run = False
        update_score_in_db(self.user_id, self.score)

    def reset(self):
        self.run = True
        # Canı tekrar geminin max health'ine ayarla
        self.lives = self.spaceship_group.sprite.health
        self.spaceship_group.sprite.reset()
        self.aliens_group.empty()
        self.alien_lasers_group.empty()
        self.powerups_group.empty()
        self.create_aliens()
        self.mystery_ship_group.empty()
        self.obstacles = self.create_obstacles()
        self.score = 0
        self.has_shield = False
        self.has_double_shot = False
        self.powerup_timer = 0

    def next_level(self):
        self.level += 1
        self.run = True
        self.lives = self.spaceship_group.sprite.health
        ship = self.spaceship_group.sprite
        ship.reset()
        ship.lasers_group.empty()
        self.aliens_group.empty()
        self.alien_lasers_group.empty()
        self.mystery_ship_group.empty()
        self.powerups_group.empty()
        self.obstacles = self.create_obstacles()
        self.create_aliens()

    def check_for_highscore(self):
        if self.score > self.highscore:
            self.highscore = self.score
            update_score_in_db(self.user_id, self.score)

    def load_highscore(self):
        self.highscore = load_highscore_from_db(self.user_id)
