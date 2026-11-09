import os
import random
import tkinter as tk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# [FITUR 2] KONFIGURASI KESULITAN
# Semua angka "setelan" dikumpulkan di satu tempat (dictionary),
# jadi mau mengubah tingkat kesulitan cukup edit di sini,
# tanpa menyentuh logika game.
# ============================================================
DIFFICULTIES = {
    'Mudah':  {'lives': 5, 'ball_speed': 4, 'paddle_width': 120,
               'powerup_chance': 0.40, 'speed_gain': 0.1, 'multiplier': 1},
    'Normal': {'lives': 3, 'ball_speed': 5, 'paddle_width': 100,
               'powerup_chance': 0.30, 'speed_gain': 0.2, 'multiplier': 1},
    'Sulit':  {'lives': 2, 'ball_speed': 6, 'paddle_width': 80,
               'powerup_chance': 0.20, 'speed_gain': 0.3, 'multiplier': 2},
}

# ============================================================
# [FITUR 1] DATA LEVEL
# Tiap level = list berisi baris. Tiap karakter = 1 bata:
#   '0' = kosong, '1'-'4' = jumlah pukulan untuk menghancurkan bata.
# Satu baris punya 8 karakter (8 kolom bata).
# Mau tambah level? Cukup tambah satu list baru di sini.
# ============================================================
LEVELS = [
    # Level 1: pemanasan
    ["11111111",
     "22222222",
     "33333333"],
    # Level 2: papan catur
    ["12121212",
     "21212121",
     "34343434",
     "43434343"],
    # Level 3: piramida
    ["00033000",
     "00233200",
     "01233210",
     "12344321"],
    # Level 4: garis-garis
    ["44444444",
     "00000000",
     "33333333",
     "00000000",
     "22222222",
     "11111111"],
    # Level 5: benteng
    ["44444444",
     "43333334",
     "43222234",
     "43211234",
     "43222234"],
]


# ============================================================
# High score (satu file per tingkat kesulitan)
# ============================================================
def highscore_path(difficulty):
    return os.path.join(BASE_DIR, 'highscore_%s.txt' % difficulty.lower())


def load_high_score(difficulty):
    try:
        with open(highscore_path(difficulty), 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_high_score(difficulty, score):
    with open(highscore_path(difficulty), 'w') as f:
        f.write(str(score))


# ============================================================
# Kelas objek game
# ============================================================
class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    MAX_SPEED = 12
    MIN_SPEED = 3

    def __init__(self, canvas, x, y, speed):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = speed  # [MODIF] kecepatan awal ditentukan Game
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5

        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        score = 0
        destroyed_positions = []
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                pos = game_object.get_position()  # simpan sebelum dihapus
                if game_object.hit():
                    score += 30
                    destroyed_positions.append(pos)
                else:
                    score += 10
        return score, destroyed_positions


class Paddle(GameObject):
    def __init__(self, canvas, x, y, width):
        # [MODIF] lebar paddle sekarang mengikuti tingkat kesulitan
        self.normal_width = width
        self.wide_width = int(width * 1.6)
        self.width = width
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

    def set_width(self, new_width):
        x1, y1, x2, y2 = self.get_position()
        center = (x1 + x2) / 2
        canvas_w = self.canvas.winfo_width()
        nx1 = center - new_width / 2
        nx2 = center + new_width / 2
        if nx1 < 0:
            nx1, nx2 = 0, new_width
        if nx2 > canvas_w:
            nx1, nx2 = canvas_w - new_width, canvas_w
        self.canvas.coords(self.item, nx1, y1, nx2, y2)
        self.width = new_width


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2', 4: '#E74C3C'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
            return True
        self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])
        return False


# ============================================================
# Power-up (polymorphism lewat apply())
# ============================================================
class PowerUp(GameObject):
    COLOR = 'white'
    LABEL = '?'
    NAME = ''

    def __init__(self, canvas, x, y):
        self.width = 34
        self.height = 18
        self.fall_speed = 4
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=self.COLOR, outline='black')
        super(PowerUp, self).__init__(canvas, item)
        self.label = canvas.create_text(x, y, text=self.LABEL,
                                        font=('Arial', 10, 'bold'))

    def update(self):
        self.move(0, self.fall_speed)

    def move(self, x, y):
        super(PowerUp, self).move(x, y)
        self.canvas.move(self.label, x, y)

    def delete(self):
        super(PowerUp, self).delete()
        self.canvas.delete(self.label)

    def apply(self, game):
        raise NotImplementedError


class WidePaddlePowerUp(PowerUp):
    COLOR = '#3498DB'
    LABEL = 'W'
    NAME = 'Paddle melebar!'

    def apply(self, game):
        game.paddle.set_width(game.paddle.wide_width)
        game.cancel_timer(game.wide_timer)
        game.wide_timer = game.schedule(
            8000, lambda: game.paddle.set_width(game.paddle.normal_width))


class SlowBallPowerUp(PowerUp):
    COLOR = '#F1C40F'
    LABEL = 'S'
    NAME = 'Bola melambat!'

    def apply(self, game):
        game.ball.speed = max(Ball.MIN_SPEED, game.ball.speed - 2)


class ExtraLifePowerUp(PowerUp):
    COLOR = '#2ECC71'
    LABEL = '+'
    NAME = 'Nyawa +1!'

    def apply(self, game):
        game.lives = min(game.lives + 1, game.max_lives)
        game.update_lives_text()


# ============================================================
# [FITUR 2] MENU AWAL
# Menu = Frame sendiri. Saat tombol diklik, Menu dihancurkan lalu
# Game dibuat dengan tingkat kesulitan yang dipilih.
# ============================================================
class Menu(tk.Frame):
    BG = '#D6D1F5'

    def __init__(self, master):
        super(Menu, self).__init__(master, bg=Menu.BG, width=610, height=400)
        self.pack_propagate(False)  # paksa ukuran frame tetap 610x400
        self.pack()

        tk.Label(self, text='BRICK BREAKER', bg=Menu.BG,
                 font=('Arial', 32, 'bold')).pack(pady=(40, 5))
        tk.Label(self, text='Pilih tingkat kesulitan', bg=Menu.BG,
                 font=('Arial', 14)).pack(pady=(0, 20))

        for name, cfg in DIFFICULTIES.items():
            label = '%s  (nyawa %d, skor x%d)' % (name, cfg['lives'],
                                                  cfg['multiplier'])
            # n=name: "mengunci" nilai name saat ini ke tiap tombol.
            # Tanpa ini, semua tombol akan memakai nama terakhir ('Sulit').
            tk.Button(self, text=label, width=28, font=('Arial', 12),
                      command=lambda n=name: self.start(n)).pack(pady=5)

        tk.Label(self, bg=Menu.BG, font=('Arial', 10),
                 text='Kontrol: panah / A-D gerak  |  Space mulai  |  P pause'
                 ).pack(side='bottom', pady=15)

    def start(self, difficulty):
        master = self.master
        self.destroy()
        Game(master, difficulty)


# ============================================================
# Kelas utama
# ============================================================
class Game(tk.Frame):
    POWERUP_TYPES = [WidePaddlePowerUp, SlowBallPowerUp, ExtraLifePowerUp]

    def __init__(self, master, difficulty='Normal'):
        super(Game, self).__init__(master)
        self.difficulty = difficulty
        self.settings = DIFFICULTIES[difficulty]  # ambil setelan kesulitan
        self.lives = self.settings['lives']
        self.max_lives = self.settings['lives'] + 2
        self.score = 0
        self.level = 1  # [FITUR 1] level saat ini (mulai dari 1)
        self.high_score = load_high_score(difficulty)
        self.running = False
        self.paused = False
        self.powerups = []
        self.timers = []
        self.wide_timer = None
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326,
                             self.settings['paddle_width'])
        self.build_level()  # [FITUR 1] susun bata sesuai level

        self.hud = None
        self.score_hud = None
        self.high_hud = None
        self.level_hud = None
        self.pause_text = None
        self.setup_game()
        self.canvas.focus_set()

        self.canvas.bind('<Left>', lambda _: self.paddle.move(-15))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(15))
        self.canvas.bind('<a>', lambda _: self.paddle.move(-15))
        self.canvas.bind('<d>', lambda _: self.paddle.move(15))
        self.canvas.bind('<p>', lambda _: self.toggle_pause())

    # ---------- timer helper ----------
    def schedule(self, ms, func):
        timer_id = self.after(ms, func)
        self.timers.append(timer_id)
        return timer_id

    def cancel_timer(self, timer_id):
        if timer_id is not None:
            self.after_cancel(timer_id)

    # ---------- [FITUR 1] level ----------
    def build_level(self):
        """Baca pola LEVELS[level-1] lalu buat bata sesuai polanya."""
        # reset daftar objek (sisakan paddle saja)
        self.items = {self.paddle.item: self.paddle}
        pattern = LEVELS[self.level - 1]
        for row_index, row in enumerate(pattern):
            for col_index, char in enumerate(row):
                hits = int(char)        # '3' -> 3
                if hits > 0:            # 0 = tidak ada bata
                    x = 5 + col_index * 75 + 37.5
                    y = 50 + row_index * 22
                    self.add_brick(x, y, hits)

    def ball_speed(self):
        # kecepatan dasar kesulitan + tambahan 0.5 tiap level
        return self.settings['ball_speed'] + 0.5 * (self.level - 1)

    def level_cleared(self):
        self.running = False
        self.clear_powerups()
        if self.level >= len(LEVELS):
            self.show_end('Semua level selesai!')
            return
        bonus = 100 * self.level
        self.score += bonus
        self.update_score_text()
        t1 = self.draw_text(300, 190, 'Level %d selesai!' % self.level, 30)
        t2 = self.draw_text(300, 235, 'Bonus +%d' % bonus, 16)
        self.schedule(2000, lambda: self.next_level(t1, t2))

    def next_level(self, *texts):
        for t in texts:
            self.canvas.delete(t)
        self.level += 1
        self.build_level()
        self.setup_game()

    # ---------- setup ----------
    def setup_game(self):
        self.running = False
        self.clear_powerups()
        self.add_ball()
        self.update_lives_text()
        self.update_score_text()
        self.update_high_text()
        self.update_level_text()
        self.text = self.draw_text(300, 200, 'Tekan Space untuk mulai', 28)
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310, self.ball_speed())
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size=40):
        font = ('Arial', size, 'bold')
        return self.canvas.create_text(x, y, text=text, font=font)

    # ---------- HUD ----------
    def _update_hud(self, attr, x, text):
        """Buat teks HUD kalau belum ada, kalau sudah ada cukup ubah isinya."""
        current = getattr(self, attr)
        if current is None:
            setattr(self, attr, self.draw_text(x, 20, text, 13))
        else:
            self.canvas.itemconfig(current, text=text)

    def update_lives_text(self):
        self._update_hud('hud', 60, 'Nyawa: %s' % self.lives)

    def update_level_text(self):
        self._update_hud('level_hud', 175,
                         'Level: %d/%d' % (self.level, len(LEVELS)))

    def update_high_text(self):
        self._update_hud('high_hud', 335, 'Rekor: %s' % self.high_score)

    def update_score_text(self):
        self._update_hud('score_hud', 540, 'Skor: %s' % self.score)

    def notify(self, message):
        note = self.draw_text(300, 370, message, 14)
        self.schedule(1500, lambda: self.canvas.delete(note))

    # ---------- kontrol game ----------
    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.running = True
        self.game_loop()

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_text = self.draw_text(300, 250, 'PAUSE', 30)
        else:
            self.canvas.delete(self.pause_text)

    def game_loop(self):
        if self.paused:
            self.after(100, self.game_loop)
            return

        self.check_collisions()
        self.update_powerups()
        num_bricks = len(self.canvas.find_withtag('brick'))

        if num_bricks == 0:
            self.ball.speed = 0
            self.level_cleared()  # [FITUR 1] lanjut level / tamat
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = 0
            self.lives -= 1
            self.update_lives_text()
            if self.lives <= 0:
                self.show_end('Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(30, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        score, destroyed_positions = self.ball.collide(objects)

        if score:
            # skor dikali pengali kesulitan (Sulit = x2)
            self.score += score * self.settings['multiplier']
            self.update_score_text()

        for pos in destroyed_positions:
            self.ball.speed = min(
                self.ball.speed + self.settings['speed_gain'],
                Ball.MAX_SPEED)
            if random.random() < self.settings['powerup_chance']:
                self.spawn_powerup((pos[0] + pos[2]) / 2,
                                   (pos[1] + pos[3]) / 2)

    # ---------- power-up ----------
    def spawn_powerup(self, x, y):
        powerup_class = random.choice(Game.POWERUP_TYPES)
        self.powerups.append(powerup_class(self.canvas, x, y))

    def update_powerups(self):
        paddle_c = self.paddle.get_position()
        for p in self.powerups[:]:
            p.update()
            c = p.get_position()
            touching = (c[2] >= paddle_c[0] and c[0] <= paddle_c[2] and
                        c[3] >= paddle_c[1] and c[1] <= paddle_c[3])
            if touching:
                p.apply(self)
                self.notify(p.NAME)
                p.delete()
                self.powerups.remove(p)
            elif c[1] > self.height:
                p.delete()
                self.powerups.remove(p)

    def clear_powerups(self):
        for p in self.powerups:
            p.delete()
        self.powerups = []

    # ---------- layar akhir ----------
    def show_end(self, message):
        self.running = False
        self.clear_powerups()
        self.draw_text(300, 150, message, 30)
        self.draw_text(300, 200, 'Skor akhir: %s' % self.score, 18)
        self.draw_text(300, 228, 'Level tercapai: %d' % self.level, 14)

        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.difficulty, self.high_score)
            self.update_high_text()
            self.draw_text(300, 258, '*** REKOR BARU! ***', 16)

        self.draw_text(300, 300, 'R = main lagi   |   M = menu', 14)
        self.canvas.bind('<r>', lambda _: self.restart())
        self.canvas.bind('<m>', lambda _: self.back_to_menu())

    def _teardown(self):
        for t in self.timers:  # batalkan timer yang masih menggantung
            self.after_cancel(t)
        master = self.master
        self.destroy()
        return master

    def restart(self):
        master = self._teardown()
        Game(master, self.difficulty)  # kesulitan yang sama

    def back_to_menu(self):
        master = self._teardown()
        Menu(master)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks! v3')
    root.resizable(False, False)
    Menu(root)  # [FITUR 2] program dimulai dari menu, bukan langsung game
    root.mainloop()