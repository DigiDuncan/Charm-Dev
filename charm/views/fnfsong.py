import logging
from pathlib import Path

import arcade

from charm.lib import anim
from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors
from charm.lib.gamemodes.fnf import CameraFocusEvent, FNFEngine, FNFHighway, FNFSceneManager, FNFSong
from charm.lib.keymap import KeyMap
from charm.lib.logsection import LogSection
from charm.lib.oggsound import OGGSound
from charm.lib.settings import Settings
from charm.lib.trackcollection import TrackCollection
from charm.lib.utils import map_range

logger = logging.getLogger("charm")


class FNFSongView(DigiView):
    def __init__(self, path: Path, *args, **kwargs):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, *args, **kwargs)
        self.path = path
        self.engine: FNFEngine = None
        self.highway_1: FNFHighway = None
        self.highway_2: FNFHighway = None
        self.songdata: FNFSong = None
        self.tracks: TrackCollection = None
        self.song_time_text: arcade.Text = None
        self.score_text: arcade.Text = None
        self.judge_text: arcade.Text = None
        self.grade_text: arcade.Text = None
        self.pause_text: arcade.Text = None
        self.dead_text: arcade.Text = None
        self.last_camera_event: CameraFocusEvent = None
        self.last_spotlight_position: float = 0
        self.last_spotlight_change: float = 0
        self.go_to_spotlight_position: int = 0
        self.spotlight_position: float = 0
        self.hp_bar_length: float = 250
        self.key_state: tuple[bool, bool, bool, bool] = [False] * 4
        self.player_sprite: arcade.Sprite = None
        self.player_anim: int = None
        self.player_anim_missed: bool = False
        self.paused: bool = False
        self.show_text: bool = True
        self.logo_width: int = None
        self.small_logos_forward: arcade.SpriteList = None
        self.small_logos_backward: arcade.SpriteList = None
        self.distractions = True

        self.scene: FNFSceneManager = None
        self.success = False

    @shows_errors
    def setup(self):
        super().setup()

        with LogSection(logger, "loading song data"):
            path = self.path
            self.songdata = FNFSong.parse(path)
            if not self.songdata:
                raise ValueError("No valid chart found!")

        with LogSection(logger, "scene"):
            self.scene = FNFSceneManager(self.songdata.charts[0])

        self.highway_1 = self.scene.highway_1
        self.highway_2 = self.scene.highway_2
        self.engine = self.scene.engine
        self.player_sprite = self.scene.player_sprite

        with LogSection(logger, "loading sound"):
            soundfiles = [f for f in path.iterdir() if f.is_file() and f.suffix in [".ogg", ".mp3", ".wav"]]
            trackfiles = []
            for s in soundfiles:
                trackfiles.append(OGGSound(s) if s.suffix == ".ogg" else arcade.Sound(s))
            self.tracks = TrackCollection(trackfiles)

            self.window.theme_song.volume = 0

        with LogSection(logger, "loading text"):
            self.song_time_text = arcade.Text("??:??", (self.size[0] // 2), 10, font_size=24,
                                            anchor_x="center", color=arcade.color.BLACK,
                                            font_name="bananaslip plus plus")

            self.score_text = arcade.Text("0", (self.size[0] // 2), self.size[1] - 10, font_size=24,
                                        anchor_x="center", anchor_y="top", color=arcade.color.BLACK,
                                        font_name="bananaslip plus plus")

            self.judge_text = arcade.Text("", (self.size[0] // 2), self.size[1] // 2, font_size=48,
                                        anchor_x="center", anchor_y="center", color=arcade.color.BLACK,
                                        font_name="bananaslip plus plus")

            self.grade_text = arcade.Text("Clear", (self.size[0] // 2), self.size[1] - 135, font_size=16,
                                        anchor_x="center", anchor_y="center", color=arcade.color.BLACK,
                                        font_name="bananaslip plus plus")

            self.pause_text = arcade.Text("PAUSED", (self.size[0] // 2), (self.size[1] // 2), font_size=92,
                                        anchor_x="center", anchor_y="center", color=arcade.color.BLACK,
                                        font_name="bananaslip plus plus")

            self.dead_text = arcade.Text("DEAD.", (self.size[0] // 2), (self.size[1] // 3) * 2, font_size=64,
                                        anchor_x="center", anchor_y="center", color=arcade.color.BLACK,
                                        font_name="bananaslip plus plus")

        with LogSection(logger, "loading gum wrapper"):
            # Generate "gum wrapper" background
            self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

        with LogSection(logger, "finalizing"):
            self.last_camera_event = CameraFocusEvent(0, 2)
            self.last_spotlight_position = 0
            self.last_spotlight_change = 0
            self.go_to_spotlight_position = 0
            self.spotlight_position = 0

            self.hp_bar_length = 250

            self.key_state = [False] * 4

            self.player_sprite.set_animation("BF idle dance")
            self.player_sprite.scale = 0.5
            self.player_sprite.right = Settings.width - 10
            self.player_sprite.bottom = 10
            self.player_anim = None
            self.player_anim_missed = False

            self.paused = False
            self.show_text = True

            self.window.update_rp(f"Playing {self.songdata.metadata.title}")

            self.success = True

    def on_show(self):
        if self.success is False:
            self.window.show_view(self.back)
        self.tracks.play()
        super().on_show()

    @shows_errors
    def on_key_something(self, symbol: int, modifiers: int, press: bool):
        if symbol in self.engine.mapping:
            i = self.engine.mapping.index(symbol)
            self.key_state[i] = press
            self.highway_1.strikeline[i].alpha = 255 if press else 64
        self.engine.process_keystate(self.key_state)

    @shows_errors
    def on_key_press(self, symbol: int, modifiers: int):
        keymap = KeyMap()
        match symbol:
            case keymap.back:
                self.back.setup()
                self.tracks.close()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])
            case keymap.pause:
                self.paused = not self.paused
                self.tracks.pause() if self.paused else self.tracks.play()
            case arcade.key.EQUAL:
                self.tracks.seek(self.tracks.time + 5)
            case arcade.key.MINUS:
                self.tracks.seek(self.tracks.time - 5)
            case arcade.key.S:
                self.tracks.log_sync()
            case arcade.key.KEY_8:
                self.distractions = not self.distractions

        self.on_key_something(symbol, modifiers, True)
        return super().on_key_press(symbol, modifiers)

    @shows_errors
    def on_key_release(self, symbol: int, modifiers: int):
        self.on_key_something(symbol, modifiers, False)
        return super().on_key_release(symbol, modifiers)

    @shows_errors
    def on_update(self, delta_time):
        super().on_update(delta_time)

        if not self.tracks.loaded:
            return

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

        time = f"{int(self.tracks.time // 60)}:{int(self.tracks.time % 60):02}"
        if self.song_time_text._label.text != time:
            self.song_time_text._label.text = time
        if self.score_text._label.text != str(self.engine.score):
            self.score_text._label.text = str(self.engine.score)
        if self.judge_text._label.text != self.engine.latest_judgement:
            self.judge_text._label.text = self.engine.latest_judgement

        self.get_spotlight_position(self.tracks.time)

        self.judge_text.y = anim.ease_circout((self.size[1] // 2) + 20, self.size[1] // 2, self.engine.latest_judgement_time, self.engine.latest_judgement_time + 0.25, self.engine.chart_time)
        self.judge_text.color = tuple(self.judge_text.color[0:3]) + (int(anim.ease_circout(255, 0, self.engine.latest_judgement_time + 0.25, self.engine.latest_judgement_time + 0.5, self.engine.chart_time)),)
        if self.engine.accuracy is not None:
            if self.grade_text._label.text != f"{self.engine.fc_type} | {round(self.engine.accuracy * 100, 2)}% ({self.engine.grade})":
                self.grade_text._label.text = f"{self.engine.fc_type} | {round(self.engine.accuracy * 100, 2)}% ({self.engine.grade})"

        if (self.engine.last_p1_note, self.engine.last_note_missed) != (self.player_anim, self.player_anim_missed):
            # logger.debug(f"animation changed from {(self.engine.last_p1_note, self.engine.last_note_missed)} to {(self.boyfriend_anim, self.boyfriend_anim_missed)}")
            if self.engine.last_p1_note is None:
                self.player_sprite.set_animation("BF idle dance")
                self.player_anim = None
            else:
                a = ""
                match self.engine.last_p1_note:
                    case 0:
                        a = "BF NOTE LEFT"
                        self.player_anim = self.engine.last_p1_note
                    case 1:
                        a = "BF NOTE DOWN"
                        self.player_anim = self.engine.last_p1_note
                    case 2:
                        a = "BF NOTE UP"
                        self.player_anim = self.engine.last_p1_note
                    case 3:
                        a = "BF NOTE RIGHT"
                        self.player_anim = self.engine.last_p1_note
                if self.engine.last_note_missed:
                    a += " MISS"
                    self.player_anim_missed = True
                else:
                    self.player_anim_missed = False
                self.player_sprite.set_animation(a)

        self.scene.update(self.tracks.time, delta_time)

    def get_spotlight_position(self, song_time: float):
        focus_pos = {
            1: 0,
            0: Settings.width // 2
        }
        cameraevents = [e for e in self.songdata.charts[0].events if isinstance(e, CameraFocusEvent) and e.time < self.tracks.time + 0.25]
        if cameraevents:
            current_camera_event = cameraevents[-1]
            if self.last_camera_event != current_camera_event:
                self.last_spotlight_change = song_time
                self.last_spotlight_position = self.spotlight_position
                self.go_to_spotlight_position = focus_pos[current_camera_event.focused_player]
                self.last_camera_event = current_camera_event
        self.spotlight_position = anim.ease_circout(self.last_spotlight_position, self.go_to_spotlight_position, self.last_spotlight_change, self.last_spotlight_change + 0.125, song_time)

    def hp_draw(self):
        hp_min = self.size[0] // 2 - self.hp_bar_length // 2
        hp_max = self.size[0] // 2 + self.hp_bar_length // 2
        hp_normalized = map_range(self.engine.hp, self.engine.min_hp, self.engine.max_hp, 0, 1)
        hp = anim.lerp(hp_min, hp_max, hp_normalized)
        arcade.draw_lrtb_rectangle_filled(
            hp_min, hp_max,
            self.size[1] - 100, self.size[1] - 110,
            arcade.color.BLACK
        )
        arcade.draw_circle_filled(hp, self.size[1] - 105, 20, arcade.color.BLUE)

    def spotlight_draw(self):
        arcade.draw_lrtb_rectangle_filled(
            self.spotlight_position - Settings.width / 2, self.spotlight_position, Settings.height, 0,
            arcade.color.BLACK + (127,)
        )
        arcade.draw_lrtb_rectangle_filled(
            self.spotlight_position + Settings.width / 2, self.spotlight_position + Settings.width, Settings.height, 0,
            arcade.color.BLACK + (127,)
        )

    @shows_errors
    def on_draw(self):
        self.clear() if self.distractions else self.clear(arcade.color.SLATE_GRAY)
        self.camera.use()

        # Charm BG
        if self.distractions:
            self.small_logos_forward.draw()
            self.small_logos_backward.draw()
            self.player_sprite.draw()

        if self.show_text:
            self.song_time_text.draw()
            self.score_text.draw()
            self.judge_text.draw()
            self.grade_text.draw()
            if self.engine.has_died:
                self.dead_text.draw()

        if self.paused:
            self.pause_text.draw()

        self.hp_draw()

        self.highway_2.draw()
        if self.distractions:
            self.spotlight_draw()
        self.highway_1.draw()

        super().on_draw()
