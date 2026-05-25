"""
Dua's Pink Paradise - Android Edition
======================================
Built with Kivy + KivyMD for Android deployment via Buildozer.

Install locally:
    pip install kivy kivymd plyer pillow

Build APK:
    buildozer android debug
"""

import math, random, threading, time
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.graphics import (
    Canvas, Color, Ellipse, Rectangle, Line,
    PushMatrix, PopMatrix, Translate, Rotate, Scale,
    RenderContext, Mesh
)
from kivy.graphics.transformation import Matrix
from kivy.graphics.opengl import (
    glEnable, glDisable, GL_DEPTH_TEST, GL_BLEND,
    glBlendFunc, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.vector import Vector
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.snackbar import Snackbar

try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

# ─────────────────────────────────────────────────────────────
#  Constants & palette
# ─────────────────────────────────────────────────────────────
W, H        = Window.size
PINK        = (1.0, 0.71, 0.76, 1)
HOT_PINK    = (1.0, 0.08, 0.58, 1)
DARK_PINK   = (0.85, 0.33, 0.53, 1)
SAKURA_PINK = (1.0, 0.60, 0.71, 1)
TRUNK_BROWN = (0.55, 0.35, 0.17, 1)
SKY_PINK    = (1.0, 0.85, 0.91, 1)
WATER_PINK  = (1.0, 0.45, 0.67, 1)
GRASS_PINK  = (1.0, 0.78, 0.86, 1)

MESSAGES = [
    "💖 Every star is a wish I made for you, Dua.",
    "🌸 You bloom like sakura in every season of my heart.",
    "💎 Rarer than any gem — that's how precious you are.",
    "🌅 With you, every sunset looks like a painting of love.",
    "✨ In a world of colours, you are my favourite pink.",
    "🦋 Your smile is the magic that makes the world beautiful.",
    "🌺 You are the reason flowers bloom a little brighter.",
]

# ─────────────────────────────────────────────────────────────
#  Fake 3-D helpers (isometric-style projection onto 2-D canvas)
#  Kivy's Mesh supports OpenGL geometry; we use a simple
#  painter's-algorithm scene for broad Android compatibility.
# ─────────────────────────────────────────────────────────────
def iso_project(x, y, z, cam_x=0, cam_z=0, scale=48):
    """
    Simple isometric-style projection.
    World coords → screen coords.
    """
    rx = x - cam_x
    rz = z - cam_z
    sx = W / 2 + (rx - rz) * scale * 0.866
    sy = H / 2 - (rx + rz) * scale * 0.5 + y * scale
    return sx, sy


def heart_points(cx, cz, radius=3.5, steps=40):
    """Parametric heart curve in XZ plane."""
    pts = []
    for i in range(steps + 1):
        t = (i / steps) * 2 * math.pi
        x = cx + radius * 16 * math.sin(t) ** 3 / 16
        z = cz + radius * (
            13 * math.cos(t)
            - 5 * math.cos(2 * t)
            - 2 * math.cos(3 * t)
            - math.cos(4 * t)
        ) / 16
        pts.append((x, z))
    return pts


# ─────────────────────────────────────────────────────────────
#  World objects
# ─────────────────────────────────────────────────────────────
class WorldObject:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def depth(self, cam_x, cam_z):
        return (self.x - cam_x) + (self.z - cam_z)


class SakuraTree(WorldObject):
    def __init__(self, x, z):
        super().__init__(x, 0, z)
        self.trunk_h = random.uniform(1.8, 2.5)
        self.blobs = [
            (random.uniform(-0.5, 0.5), self.trunk_h + random.uniform(0, 0.8),
             random.uniform(-0.5, 0.5), random.uniform(0.9, 1.4))
            for _ in range(3)
        ]

    def draw(self, canvas, cam_x, cam_z, scale):
        # trunk
        bx, by = iso_project(self.x, 0, self.z, cam_x, cam_z, scale)
        tx, ty = iso_project(self.x, self.trunk_h, self.z, cam_x, cam_z, scale)
        with canvas:
            Color(*TRUNK_BROWN)
            Line(points=[bx, by, tx, ty], width=max(2, scale * 0.08))
            # blobs
            for ox, oy, oz, r in self.blobs:
                blobx = self.x + ox
                bloby = oy
                blobz = self.z + oz
                px, py = iso_project(blobx, bloby, blobz, cam_x, cam_z, scale)
                sr = r * scale * 0.55
                c = random.choice([SAKURA_PINK, PINK, HOT_PINK])
                Color(c[0], c[1], c[2], 0.92)
                Ellipse(pos=(px - sr, py - sr * 0.6), size=(sr * 2, sr * 1.2))


class Heart(WorldObject):
    def __init__(self, x, z, msg_index):
        super().__init__(x, 0.5, z)
        self.msg_index = msg_index
        self.collected = False
        self.pulse = random.uniform(0, math.pi * 2)

    def draw(self, canvas, cam_x, cam_z, scale, dt):
        if self.collected:
            return
        self.pulse += dt * 3
        bob = math.sin(self.pulse) * 0.15
        px, py = iso_project(self.x, self.y + bob, self.z, cam_x, cam_z, scale)
        sr = scale * 0.38
        with canvas:
            Color(*HOT_PINK, 1)
            # Draw heart shape using two circles + triangle approximation
            Ellipse(pos=(px - sr * 0.9, py - sr * 0.1), size=(sr, sr))
            Ellipse(pos=(px - sr * 0.1, py - sr * 0.1), size=(sr, sr))
            # bottom triangle via polygon approximation
            from kivy.graphics import Triangle
            Triangle(points=[
                px - sr * 0.9, py - sr * 0.1,
                px + sr * 0.9, py - sr * 0.1,
                px,            py - sr * 0.85,
            ])

    def screen_pos(self, cam_x, cam_z, scale):
        return iso_project(self.x, self.y, self.z, cam_x, cam_z, scale)


class Player(WorldObject):
    def __init__(self):
        super().__init__(0, 0, 0)
        self.speed = 4.0
        self.vx = 0.0
        self.vz = 0.0
        self.facing = 0.0   # degrees, for body lean visual
        self.profile_tex = None

    def move(self, jx, jy, dt):
        if abs(jx) > 0.05 or abs(jy) > 0.05:
            self.vx = jx * self.speed
            self.vz = -jy * self.speed
            self.facing = math.degrees(math.atan2(jx, jy))
        else:
            self.vx *= 0.85
            self.vz *= 0.85
        self.x = max(-18, min(18, self.x + self.vx * dt))
        self.z = max(-18, min(18, self.z + self.vz * dt))

    def draw(self, canvas, cam_x, cam_z, scale):
        px, py = iso_project(self.x, 0, self.z, cam_x, cam_z, scale)
        body_w = scale * 0.45
        body_h = scale * 0.75
        head_r = scale * 0.28
        with canvas:
            # Shadow
            Color(0.7, 0.3, 0.5, 0.3)
            Ellipse(pos=(px - body_w * 0.8, py - 6), size=(body_w * 1.6, 10))
            # Body
            Color(*HOT_PINK)
            Rectangle(pos=(px - body_w / 2, py), size=(body_w, body_h))
            # Head
            Color(1.0, 0.87, 0.80, 1)
            Ellipse(pos=(px - head_r, py + body_h - head_r * 0.4), size=(head_r * 2, head_r * 2))
            # Eyes
            Color(0.2, 0.1, 0.1, 1)
            Ellipse(pos=(px - head_r * 0.35, py + body_h + head_r * 0.3), size=(5, 5))
            Ellipse(pos=(px + head_r * 0.15, py + body_h + head_r * 0.3), size=(5, 5))


# ─────────────────────────────────────────────────────────────
#  Game Canvas (scene renderer)
# ─────────────────────────────────────────────────────────────
class GameCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale = 42
        self.player = Player()
        self.cam_x  = 0.0
        self.cam_z  = -6.0

        # Build world
        tree_positions = [
            (-12, -12), (12, -12), (-12, 12), (12, 12),
            (0, -16),   (-16, 0),  (16, 0),   (0, 16),
            (-7, 5),    (7, -5),   (-5, -9),  (5, 9),
        ]
        self.trees = [SakuraTree(x, z) for x, z in tree_positions]

        heart_positions = [
            (-8, -4), (8, 3), (-3, 10), (6, -10), (-10, 6), (0, -14), (13, -6),
        ]
        self.hearts = [
            Heart(x, z, i % len(MESSAGES))
            for i, (x, z) in enumerate(heart_positions)
        ]

        self.collected_count = 0
        self.message_text    = ""
        self.message_timer   = 0.0

        Clock.schedule_interval(self._update, 1 / 60)

    # joystick input set by parent
    def set_joystick(self, jx, jy):
        self._jx = jx
        self._jy = jy

    _jx = 0.0
    _jy = 0.0

    def _update(self, dt):
        self.player.move(self._jx, self._jy, dt)

        # Camera smooth follow
        target_cx = self.player.x
        target_cz = self.player.z - 6
        self.cam_x += (target_cx - self.cam_x) * 5 * dt
        self.cam_z += (target_cz - self.cam_z) * 5 * dt

        # Heart collection
        for h in self.hearts:
            if h.collected:
                continue
            hx, hy = h.screen_pos(self.cam_x, self.cam_z, self.scale)
            px, py = iso_project(self.player.x, 0, self.player.z,
                                  self.cam_x, self.cam_z, self.scale)
            dist = math.hypot(hx - px, hy - py)
            if dist < self.scale * 0.7:
                h.collected = True
                self.collected_count += 1
                self.message_text  = MESSAGES[h.msg_index]
                self.message_timer = 4.0
                if self.collected_count == len(self.hearts):
                    Clock.schedule_once(lambda dt: self._all_collected(), 4.2)

        if self.message_timer > 0:
            self.message_timer -= dt

        self._render(dt)

    def _all_collected(self):
        self.message_text  = "🌸 You found every heart! You are truly magical, Dua! 🌸"
        self.message_timer = 6.0

    def _render(self, dt):
        self.canvas.clear()
        cx, cz   = self.cam_x, self.cam_z
        sc       = self.scale

        with self.canvas:
            # ── Sky ──────────────────────────────────────
            Color(*SKY_PINK)
            Rectangle(pos=(0, 0), size=self.size)

            # ── Ground tiles (simple gradient bands) ─────
            for row in range(12):
                t = row / 12
                r = GRASS_PINK[0] - t * 0.08
                g = GRASS_PINK[1] - t * 0.12
                b = GRASS_PINK[2] - t * 0.06
                Color(r, g, b, 1)
                y_band = row * self.height / 12
                Rectangle(pos=(0, y_band), size=(self.width, self.height / 12 + 1))

            # ── Heart lake ───────────────────────────────
            lake_pts = heart_points(0, 2, radius=3.2)
            screen_lake = []
            for lx, lz in lake_pts:
                sx, sy = iso_project(lx, -0.05, lz, cx, cz, sc)
                screen_lake += [sx, sy]
            if len(screen_lake) >= 6:
                Color(*WATER_PINK, 0.85)
                from kivy.graphics import Line as KLine
                # Fill approximation: draw many ellipses
                for i in range(0, len(screen_lake) - 2, 2):
                    mx = (screen_lake[i] + W / 2) / 2
                    my = (screen_lake[i+1] + H / 2) / 2
                    Color(*WATER_PINK, 0.55)
                    Ellipse(pos=(mx - 6, my - 4), size=(12, 8))
                Color(*WATER_PINK, 0.7)
                Line(points=screen_lake, width=2, close=True)

            # ── Sort & draw world objects (painter's algo) ─
            objects = sorted(
                self.trees + [h for h in self.hearts if not h.collected],
                key=lambda o: o.depth(cx, cz)
            )
            for obj in objects:
                if isinstance(obj, SakuraTree):
                    obj.draw(self.canvas, cx, cz, sc)
                elif isinstance(obj, Heart):
                    obj.draw(self.canvas, cx, cz, sc, dt)

            # ── Player ───────────────────────────────────
            self.player.draw(self.canvas, cx, cz, sc)


# ─────────────────────────────────────────────────────────────
#  On-screen Joystick
# ─────────────────────────────────────────────────────────────
class TouchJoystick(Widget):
    jx = NumericProperty(0)
    jy = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.touch_uid  = None
        self.base_pos   = (0, 0)
        self.knob_pos   = (0, 0)
        self.radius     = 55
        self.knob_r     = 22
        self._draw_stick()
        self.bind(pos=self._draw_stick, size=self._draw_stick)

    def _draw_stick(self, *_):
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        self.base_pos = (cx, cy)
        self.knob_pos = (cx, cy)
        self._redraw()

    def _redraw(self):
        self.canvas.clear()
        cx, cy   = self.base_pos
        kx, ky   = self.knob_pos
        r        = self.radius
        kr       = self.knob_r
        with self.canvas:
            Color(1, 0.4, 0.6, 0.35)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
            Color(1, 0.08, 0.58, 0.75)
            Ellipse(pos=(kx - kr, ky - kr), size=(kr * 2, kr * 2))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.touch_uid is None:
            self.touch_uid = touch.uid
            self._update_knob(touch)
            return True

    def on_touch_move(self, touch):
        if touch.uid == self.touch_uid:
            self._update_knob(touch)
            return True

    def on_touch_up(self, touch):
        if touch.uid == self.touch_uid:
            self.touch_uid = None
            self.knob_pos  = self.base_pos
            self.jx = 0
            self.jy = 0
            self._redraw()
            return True

    def _update_knob(self, touch):
        cx, cy = self.base_pos
        dx = touch.x - cx
        dy = touch.y - cy
        dist = math.hypot(dx, dy)
        if dist > self.radius:
            dx = dx / dist * self.radius
            dy = dy / dist * self.radius
        self.knob_pos = (cx + dx, cy + dy)
        self.jx = dx / self.radius
        self.jy = dy / self.radius
        self._redraw()


# ─────────────────────────────────────────────────────────────
#  Profile photo picker
# ─────────────────────────────────────────────────────────────
def pick_profile_photo(on_success):
    """Open gallery via plyer; calls on_success(path) on main thread."""
    def _pick():
        if not PLYER_AVAILABLE:
            return
        try:
            filechooser.open_file(
                on_selection=lambda sel: Clock.schedule_once(
                    lambda dt: on_success(sel[0]) if sel else None, 0
                ),
                filters=["*.png", "*.jpg", "*.jpeg"],
                multiple=False,
            )
        except Exception as e:
            print(f"[Profile] File picker error: {e}")
    threading.Thread(target=_pick, daemon=True).start()


# ─────────────────────────────────────────────────────────────
#  Root UI layout
# ─────────────────────────────────────────────────────────────
class GameUI(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ── Game scene ───────────────────────────────────
        self.game = GameCanvas(size=self.size, pos=self.pos)
        self.add_widget(self.game)
        self.bind(size=lambda *_: setattr(self.game, 'size', self.size))

        # ── Joystick (bottom-left) ───────────────────────
        self.joystick = TouchJoystick(
            size=(160, 160),
            pos=(20, 20),
        )
        self.joystick.bind(jx=self._on_joy, jy=self._on_joy)
        self.add_widget(self.joystick)

        # ── HUD: title ───────────────────────────────────
        self.title_lbl = Label(
            text="[b]💖 Dua's Pink Paradise 💖[/b]",
            markup=True,
            font_size="18sp",
            color=(0.7, 0, 0.35, 1),
            size_hint=(None, None),
            size=(320, 40),
            pos_hint={"center_x": 0.5, "top": 1.0},
        )
        self.add_widget(self.title_lbl)

        # ── HUD: counter ─────────────────────────────────
        self.counter_lbl = Label(
            text="💗 Hearts: 0 / 7",
            font_size="15sp",
            color=(0.8, 0.1, 0.4, 1),
            size_hint=(None, None),
            size=(200, 36),
            pos_hint={"right": 1.0, "top": 0.97},
        )
        self.add_widget(self.counter_lbl)

        # ── HUD: message banner ──────────────────────────
        self.msg_lbl = Label(
            text="",
            font_size="14sp",
            color=(0.65, 0, 0.3, 1),
            size_hint=(None, None),
            size=(360, 56),
            pos_hint={"center_x": 0.5, "center_y": 0.42},
            halign="center",
            text_size=(360, None),
            markup=True,
        )
        self.add_widget(self.msg_lbl)

        # ── Profile photo frame ──────────────────────────
        self.profile_frame = Widget(
            size_hint=(None, None),
            size=(72, 72),
            pos_hint={"right": 0.98, "top": 0.90},
        )
        with self.profile_frame.canvas:
            Color(*HOT_PINK)
            self._pf_rect = Rectangle(
                pos=self.profile_frame.pos,
                size=self.profile_frame.size,
            )
        self.profile_frame.bind(pos=self._update_pf, size=self._update_pf)
        self.add_widget(self.profile_frame)

        self.profile_img = KivyImage(
            size_hint=(None, None),
            size=(66, 66),
            pos_hint={"right": 0.975, "top": 0.893},
            allow_stretch=True,
            keep_ratio=True,
        )
        self.add_widget(self.profile_img)

        # ── Profile button ───────────────────────────────
        self.profile_btn = Button(
            text="📷 Profile",
            size_hint=(None, None),
            size=(110, 38),
            pos_hint={"right": 0.98, "top": 0.77},
            background_color=(1, 0.08, 0.58, 1),
            color=(1, 1, 1, 1),
            font_size="13sp",
        )
        self.profile_btn.bind(on_release=self._on_profile)
        self.add_widget(self.profile_btn)

        # ── Periodic UI update ───────────────────────────
        Clock.schedule_interval(self._update_hud, 1 / 10)

    def _update_pf(self, widget, *_):
        self._pf_rect.pos  = widget.pos
        self._pf_rect.size = widget.size

    def _on_joy(self, *_):
        self.game.set_joystick(self.joystick.jx, self.joystick.jy)

    def _on_profile(self, *_):
        pick_profile_photo(self._set_profile_image)

    def _set_profile_image(self, path):
        self.profile_img.source = path
        self.profile_img.reload()

    def _update_hud(self, dt):
        c = self.game.collected_count
        self.counter_lbl.text = f"💗 Hearts: {c} / 7"
        if self.game.message_timer > 0:
            self.msg_lbl.text = self.game.message_text
        else:
            self.msg_lbl.text = ""


# ─────────────────────────────────────────────────────────────
#  App entry point
# ─────────────────────────────────────────────────────────────
class DuasParadiseApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Pink"
        self.theme_cls.theme_style     = "Light"
        Window.clearcolor               = (1, 0.85, 0.91, 1)
        return GameUI()

    def on_start(self):
        """This runs when the app starts."""
        print("[Game] Dua's Pink Paradise started ❤️")
        # Starts the heartbeat monitor thread
        threading.Thread(target=self.background_monitor, daemon=True).start()

    def background_monitor(self):
        """Standard system health check for ICS project."""
        while True:
            print("[SYSTEM] Heartbeat Active: Monitoring App Health...")
            time.sleep(30)

if __name__ == "__main__":
    DuasParadiseApp().run()