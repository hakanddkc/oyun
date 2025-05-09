import pygame, random, sqlite3
from spaceship import Spaceship
from obstacle import Obstacle, grid
from alien import Alien, MysteryShip
from laser import Laser
from powerup import PowerUp  # Yeni: PowerUp sınıfı

# -----------------------------------------------------
# VERİTABANI İŞLEMLERİ
# -----------------------------------------------------
def load_coins_from_db(user_id):
    """Veritabanından ilgili kullanıcının coin değerini çeker."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def load_highscore_from_db(user_id):
    """Veritabanından ilgili kullanıcının en yüksek skorunu çeker."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(score) FROM user_levels WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] is not None else 0


def update_coins_in_db(user_id, coins):
    """Veritabanındaki ilgili kullanıcının coin değerini günceller."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins=? WHERE id=?", (coins, user_id))
    conn.commit()
    conn.close()


def update_score_in_db(user_id, score):
    """Veritabanındaki ilgili kullanıcının skorunu günceller."""
    conn = sqlite3.connect("game_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_levels (user_id, score) VALUES (?, ?)", (user_id, score)
    )
    conn.commit()
    conn.close()


class Game:
    def __init__(self, screen_width, screen_height, offset,
                 level=1, user_id=1, spaceship_image_path=None):
        self.muted = False
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.offset = offset
        self.level = level
        self.user_id = user_id

        pygame.display.init()
        self.screen = pygame.display.set_mode((screen_width + offset, screen_height + 2*offset))
        pygame.display.set_caption("Python Space Invaders")

        if spaceship_image_path is None:
            spaceship_image_path = "Graphics/default_spaceship.png"

        self.spaceship_group = pygame.sprite.GroupSingle(
            Spaceship(screen_width, screen_height, offset, spaceship_image_path=spaceship_image_path)
        )
        self.obstacles = self.create_obstacles()
        self.aliens_group = pygame.sprite.Group()
        self.create_aliens()
        self.aliens_direction = 1
        self.alien_lasers_group = pygame.sprite.Group()
        self.mystery_ship_group = pygame.sprite.GroupSingle()
        self.lives = 3
        self.run = True
        self.score = 0
        self.highscore = load_highscore_from_db(self.user_id)
        self.coins = load_coins_from_db(self.user_id)

        self.explosion_sound = pygame.mixer.Sound("Sounds/explosion.ogg")
        pygame.mixer.music.load("Sounds/music.ogg")
        pygame.mixer.music.play(-1)

        # Power-up sistemi
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

        font = pygame.font.Font("Font/monogram.ttf", 40)
        self.screen.blit(font.render(f"LEVEL {self.level}", True, (243,216,63)), (570,740))
        self.create_mute_button()

        # Draw sprite groups
        self.spaceship_group.draw(self.screen)
        self.spaceship_group.sprite.lasers_group.draw(self.screen)
        for obs in self.obstacles:
            obs.blocks_group.draw(self.screen)
        self.aliens_group.draw(self.screen)
        self.alien_lasers_group.draw(self.screen)
        self.mystery_ship_group.draw(self.screen)
        self.powerups_group.draw(self.screen)

        # Score / Highscore / Coins
        self.screen.blit(font.render(str(self.score).zfill(5), False, (243,216,63)), (50,40))
        self.screen.blit(font.render(str(self.highscore).zfill(5), False, (243,216,63)), (550,40))
        self.screen.blit(font.render(f"Coins: {self.coins}", True, (243,216,63)), (50,80))

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

    def move_aliens(self):
        self.aliens_group.update(self.aliens_direction)
        for alien in self.aliens_group.sprites():
            if alien.rect.right >= self.screen_width + self.offset/2:
                self.aliens_direction = -1; self.alien_move_down(2)
            elif alien.rect.left <= self.offset/2:
                self.aliens_direction = 1; self.alien_move_down(2)

    def alien_move_down(self, d):
        for a in self.aliens_group.sprites(): a.rect.y += d

    def alien_shoot_laser(self):
        if self.aliens_group:
            shooter = random.choice(self.aliens_group.sprites())
            self.alien_lasers_group.add(Laser(shooter.rect.center, -6, self.screen_height))

    def create_mystery_ship(self):
        self.mystery_ship_group.add(MysteryShip(self.screen_width, self.offset))

    def create_powerup(self):
        pt = random.choice(["shield","double_shot"])
        self.powerups_group.add(PowerUp(self.screen_width, self.screen_height, self.offset, pt))

    def check_for_collisions(self):
        # Player lasers
        for laser in self.spaceship_group.sprite.lasers_group:
            # Aliens
            hits = pygame.sprite.spritecollide(laser, self.aliens_group, True)
            if hits:
                self.explosion_sound.play()
                for a in hits:
                    self.score += a.type*100; self.check_for_highscore()
                    self.coins += a.type*20; update_coins_in_db(self.user_id, self.coins)
                laser.kill()
            # Mystery ship
            if pygame.sprite.spritecollide(laser, self.mystery_ship_group, True):
                self.score += 500; self.explosion_sound.play(); self.check_for_highscore()
                self.coins += 100; update_coins_in_db(self.user_id, self.coins)
                laser.kill()
            # Powerups
            pus = pygame.sprite.spritecollide(laser, self.powerups_group, True)
            if pus:
                laser.kill()
                for pu in pus:
                    if pu.power_type=="shield": self.has_shield=True; self.powerup_timer=self.powerup_duration
                    else: self.has_double_shot=True; self.powerup_timer=self.powerup_duration
            # Obstacles
            for obs in self.obstacles:
                if pygame.sprite.spritecollide(laser, obs.blocks_group, True):
                    laser.kill()
        # Alien lasers
        for laser in self.alien_lasers_group:
            if pygame.sprite.spritecollide(laser, self.spaceship_group, False):
                laser.kill()
                if not self.has_shield:
                    self.lives -= 1
                    if self.lives<=0: self.game_over()
                else:
                    self.has_shield=False; self.powerup_timer=0
            for obs in self.obstacles:
                if pygame.sprite.spritecollide(laser, obs.blocks_group, True):
                    laser.kill()
        # Alien vs player/obs
        for alien in self.aliens_group:
            for obs in self.obstacles:
                pygame.sprite.spritecollide(alien, obs.blocks_group, True)
            if pygame.sprite.spritecollide(alien, self.spaceship_group, False):
                if not self.has_shield: self.lives -= 1
                else: self.has_shield=False; self.powerup_timer=0
                alien.kill()
                if self.lives<=0: self.game_over()

    def update_powerup_status(self):
        if self.powerup_timer>0: self.powerup_timer -= 1
        else: self.has_shield=False; self.has_double_shot=False

    def game_over(self):
        self.run = False
        update_score_in_db(self.user_id, self.score)

    def reset(self):
        self.run=True; self.lives=3
        self.spaceship_group.sprite.reset()
        self.aliens_group.empty(); self.alien_lasers_group.empty()
        self.powerups_group.empty(); self.create_aliens()
        self.mystery_ship_group.empty(); self.obstacles=self.create_obstacles()
        self.score=0; self.has_shield=False; self.has_double_shot=False; self.powerup_timer=0

    def next_level(self):
        self.level += 1; self.run=True; self.lives=3
        # reset spaceship so it can move again
        ship = self.spaceship_group.sprite
        ship.reset(); ship.lasers_group.empty()
        # clear old entities
        self.aliens_group.empty(); self.alien_lasers_group.empty()
        self.mystery_ship_group.empty(); self.powerups_group.empty()
        self.obstacles = self.create_obstacles()
        self.create_aliens()

    def check_for_highscore(self):
        if self.score > self.highscore:
            self.highscore = self.score
            update_score_in_db(self.user_id, self.score)

    def load_highscore(self):
        self.highscore = load_highscore_from_db(self.user_id)
