from dataclasses import dataclass, field
from functools import total_ordering
from pathlib import Path
from typing import Literal, Optional
import logging
import math
import re

from charm.lib.errors import ChartParseError
from charm.lib.generic.song import BPMChangeEvent, Seconds
from charm.lib.utils import clamp

NUM = r"[\d.-]+"
INT = r"\d+"
ZO = r"[01]"
RE_KV_TYPE_1 = r"(.+):(.+)"
RE_KV_TYPE_2 = r"(.+): (.+)"
RE_KV_TYPE_3 = r"(.+) : (.+)"
RE_TIMING_POINT = fr"({NUM}),({NUM}),({INT}),({INT}),({INT}),({INT}),({ZO}),({INT})$"
RE_DEFAULT = fr"({INT}),({INT}),({INT}),({INT}),({INT})"
RE_HIT_SAMPLE = fr"({INT}):({INT}):({INT}):({INT}):(.+)?"
RE_HIT_CIRCLE = fr"{RE_DEFAULT},({RE_HIT_SAMPLE})$"
RE_PIPE_SEP_INT = r"\d+(\|\d+)*"
RE_PIPE_SEP_COLON_SEP_INT = r"\d+:\d+(?:\|\d+:\d+)*"

RE_SLIDER = fr"{RE_DEFAULT},([BCLP])\|({RE_PIPE_SEP_COLON_SEP_INT}),({INT}),({NUM}),({RE_HIT_SAMPLE})$"
RE_SPINNER = fr"{RE_DEFAULT},({INT}),({RE_HIT_SAMPLE})$"
RE_HOLD = fr"{RE_DEFAULT},({INT}):({RE_HIT_SAMPLE})$"

logger = logging.getLogger("charm")


@dataclass
class OsuTimingPoint(BPMChangeEvent):
    """A BPMChangeEvent with additional osu! specific information."""
    meter: int = 4
    sample_set: int = 0
    sample_index: int = 0
    volume: float = 1
    uninherited: bool = False
    effects: int = 0
    slider_velocity_multipler: float = 1

    @property
    def kiai_time(self) -> bool:
        return bool(self.effects & 0b0001)

    @property
    def omit_barline(self) -> bool:
        return bool(self.effects & 0b1000)


@dataclass
class OsuHitSample:
    """A representation of the current hit sample settings."""
    normal_set: int = 0
    addition_set: int = 0
    index: int = 0
    volume: float = 0
    filename: Optional[str] = None


@total_ordering
@dataclass
class OsuHitObject:
    """A generic osu! note."""
    x: int
    y: int
    time: Seconds
    object_type: int
    hit_sound: int

    @property
    def hit_sound_normal(self) -> bool:
        return bool(self.hit_sound & 0b0001)

    @property
    def hit_sound_whistle(self) -> bool:
        return bool(self.hit_sound & 0b0010)

    @property
    def hit_sound_finish(self) -> bool:
        return bool(self.hit_sound & 0b0100)

    @property
    def hit_sound_clap(self) -> bool:
        return bool(self.hit_sound & 0b1000)

    @property
    def new_combo(self) -> bool:
        return bool(self.object_type & 0b0100)

    @property
    def combo_skip(self) -> int:
        return (self.object_type & 0b1110000) >> 4

    @property
    def taiko_kat(self) -> bool:
        return self.hit_sound_clap or self.hit_sound_whistle

    @property
    def taiko_large(self) -> bool:
        return self.hit_sound_finish

    def get_lane(self, lanes: int) -> int:
        """Used to determine the lane in osu!mania."""
        lane_calc = math.floor(self.x * lanes / 512)
        return clamp(0, lane_calc, lanes - 1)

    def __lt__(self, other: "OsuHitObject") -> bool:
        return (self.time, self.x, other.y) < (other.time, other.x, other.y)

    def __eq__(self, other: "OsuHitObject") -> bool:
        return (self.time, self.x, other.y) == (other.time, other.x, other.y)


@dataclass
class OsuHitCircle(OsuHitObject):
    """A standard osu! note."""
    hit_sample: OsuHitSample


@dataclass
class OsuPoint:
    x: float
    y: float


@dataclass
class OsuSlider(OsuHitObject):
    """A slider note in osu!"""
    curve_type: Literal['B', 'C', 'L', 'P']
    curve_points: list[OsuPoint]
    slides: int
    px_length: float
    edge_sounds: list[int]
    edge_sets: list[str]
    hit_sample: OsuHitSample

    end_time: Seconds = None

    @property
    def length(self) -> Seconds:
        return self.end_time - self.time


@dataclass
class OsuSpinner(OsuHitObject):
    """A spinner note in osu!"""
    end_time: Seconds
    hit_sample: OsuHitSample

    @property
    def length(self) -> Seconds:
        return self.end_time - self.time


@dataclass
class OsuHold(OsuHitObject):
    """A hold note specific to osu!mania."""
    end_time: Seconds
    hit_sample: OsuHitSample

    @property
    def length(self) -> Seconds:
        return self.end_time - self.time


@dataclass
class OsuGeneralData:
    """General attributes on an osu! chart."""
    audio_filename: str = None
    audio_leadin: Seconds = 0
    preview_time: Seconds = -0.001
    countdown_type: int = 0
    sample_set: Literal["normal", "soft", "drum"] = "normal"
    stack_leniency: float = 0.7
    mode: int = 0

    MODE_NAMES = ("normal", "taiko", "catch", "mania")

    @property
    def mode_name(self) -> str:
        return self.MODE_NAMES[self.mode]


@dataclass
class OsuMetadata:
    """Metadata that an osu! chart supports."""
    title: str = None
    title_unicode: Optional[str] = None
    artist: str = None
    artist_unicode: Optional[str] = None
    charter: str = None
    difficulty: str = None
    source: str = None
    tags: list[str] = None


@dataclass
class OsuDifficulty:
    """Definitions relating to the osu! engine."""
    hp_drain_rate: float = None
    circle_size: float = None
    overall_difficulty: float = None
    approach_rate: float = None
    slider_multiplier: float = None
    slider_tick_rate: float = None

    @property
    def hp(self) -> float:
        return self.hp_drain_rate

    @hp.setter
    def hp(self, v: float):
        self.hp_drain_rate = v

    @property
    def cs(self) -> float:
        return self.circle_size

    @cs.setter
    def cs(self, v: float):
        self.circle_size = v

    @property
    def od(self) -> float:
        return self.overall_difficulty

    @od.setter
    def od(self, v: float):
        self.overall_difficulty = v

    @property
    def ar(self) -> float:
        return self.approach_rate

    @ar.setter
    def ar(self, v: float):
        self.approach_rate = v


@dataclass
class OsuEvent:
    """A generic osu! event."""
    event_type: int
    time: Seconds

    EVENT_NAMES = ('background', 'video', 'break', 'sample')

    @property
    def event_name(self) -> str:
        return self.EVENT_NAMES[self.event_type]


@dataclass
class OsuBackgroundEvent(OsuEvent):
    """An osu! event that changes the chart background."""
    filename: str
    x_offset: float
    y_offset: float


@dataclass
class OsuVideoEvent(OsuEvent):
    """An osu! event that plays a video."""
    filename: str


@dataclass
class OsuBreakEvent(OsuEvent):
    """An osu! event defining a break."""
    end_time: Seconds

    @property
    def length(self) -> Seconds:
        return self.end_time - self.time


@dataclass
class OsuSampleEvent(OsuEvent):
    """An osu! event that plays a sample."""
    filename: str
    volume: float = 1


def get_standard_data_from_match(m: re.Match[str]) -> tuple[int, int, int, int, int]:
    x = int(m.group(1))
    y = int(m.group(2))
    time = int(m.group(3)) / 1000
    object_type = int(m.group(4))
    hit_sound = int(m.group(5))

    return x, y, time, object_type, hit_sound


def hit_sample_from_match(m: re.Match[str]) -> OsuHitSample:
    normal_set = int(m.group(1))
    addition_set = int(m.group(2))
    index = int(m.group(3))
    volume = int(m.group(4))
    filename = m.group(5) or None

    hit_sample = OsuHitSample(normal_set, addition_set, index, volume, filename)
    return hit_sample


@dataclass
class RawOsuChart:
    general: OsuGeneralData = field(default_factory=OsuGeneralData)
    metadata: OsuMetadata = field(default_factory=OsuMetadata)
    difficulty: OsuDifficulty = field(default_factory=OsuDifficulty)
    timing_points: list[OsuTimingPoint] = field(default_factory=list)
    hit_objects: list[OsuHitObject] = field(default_factory=list)

    @classmethod
    def parse(cls, path: Path) -> "RawOsuChart":
        """https://osu.ppy.sh/wiki/en/Client/File_formats/Osu_(file_format)"""
        with open(path) as p:
            lines = p.readlines()

        chart = RawOsuChart()
        line_num = 0

        current_header = None
        for line in lines:
            line_num += 1
            line = line.strip()
            if line == "":
                continue
            if line.startswith("["):
                current_header = line.strip().removeprefix("[").removesuffix("]")
            elif current_header is None:
                continue
            elif current_header == "General":
                if m := re.match(RE_KV_TYPE_2, line):
                    match m.group(1):
                        case "AudioFilename":
                            chart.general.audio_filename = m.group(2)
                        case "AudioLeadIn":
                            chart.general.audio_leadin = int(m.group(2)) / 1000
                        case "PreviewTime":
                            chart.general.preview_time = int(m.group(2)) / 1000
                        case "Countdown":
                            chart.general.countdown_type = int(m.group(2))
                        case "SampleSet":
                            chart.general.sample_set = m.group(2).lower()
                        case "StackLeniency":
                            chart.general.stack_leniency = float(m.group(2))
                        case "Mode":
                            chart.general.mode = int(m.group(2))
                        # Skipping LetterboxInBreaks
                        # Skipping SpecialStyle
                        # Skipping WidescreenStoryboard
                        case "LetterboxInBreaks" | "SpecialStyle" | "WidescreenStoryboard":
                            continue
                        case _:
                            logger.debug(f"Unknown General metadata '{line}' (Line {line_num}).")
            elif current_header == "Editor":
                # We're ignoring editor-only data right now, since we don't have a chart editor.
                pass
            elif current_header == "Metadata":
                if m := re.match(RE_KV_TYPE_1, line):
                    match m.group(1):
                        case "Title":
                            chart.metadata.title = m.group(2)
                        case "TitleUnicode":
                            chart.metadata.title_unicode = m.group(2)
                        case "Artist":
                            chart.metadata.artist = m.group(2)
                        case "ArtistUnicode":
                            chart.metadata.artist_unicode = m.group(2)
                        case "Creator":
                            chart.metadata.charter = m.group(2)
                        case "Version":
                            chart.metadata.difficulty = m.group(2)
                        case "Source":
                            chart.metadata.source = m.group(2)
                        case "Tags":
                            chart.metadata.tags = m.group(2).split(" ")
                        case _:
                            logger.debug(f"Unknown Metadata metadata '{m.group(2)}' (Line {line_num}).")
            elif current_header == "Difficulty":
                if m := re.match(RE_KV_TYPE_1, line):
                    match m.group(1):
                        case "HPDrainRate":
                            chart.difficulty.hp_drain_rate = float(m.group(2))
                        case "CircleSize":
                            chart.difficulty.circle_size = float(m.group(2))
                        case "OverallDifficulty":
                            chart.difficulty.overall_difficulty = float(m.group(2))
                        case "ApproachRate":
                            chart.difficulty.approach_rate = float(m.group(2))
                        case "SliderMultiplier":
                            chart.difficulty.slider_multiplier = float(m.group(2))
                        case "SliderTickRate":
                            chart.difficulty.slider_tick_rate = float(m.group(2))
                        case _:
                            logger.debug(f"Unknown Difficulty metadata '{m.group(2)} (Line {line_num})'.")
            elif current_header == "Events":
                pass
            elif current_header == "TimingPoints":
                if m := re.match(RE_TIMING_POINT, line):
                    uninherited = bool(int(m.group(7)))
                    time = int(float(m.group(1))) / 1000
                    beat_length = float(m.group(2))
                    meter = int(m.group(3))
                    sample_set = int(m.group(4))
                    sample_index = int(m.group(5))
                    volume = int(m.group(6)) / 100
                    effects = int(m.group(8))
                    if uninherited:
                        bpm = (1 / beat_length * 1000 * 60)
                        chart.timing_points.append(
                            OsuTimingPoint(time, bpm, meter, sample_set, sample_index, volume, uninherited, effects)
                        )
                    else:
                        slider_vel = 1 / (beat_length / -100)
                        current_timing_point = chart.timing_points[-1]
                        chart.timing_points.append(
                            OsuTimingPoint(time, current_timing_point.new_bpm, meter, sample_set, sample_index, volume, uninherited, effects, slider_vel)
                        )

                else:
                    raise ChartParseError(line_num, f"Unparseable timing point '{line}'.")
            elif current_header == "Colours":
                # Ignoring colors for now.
                pass
            elif current_header == "HitObjects":
                # x,y,time,type,hitSound,hitSample
                if m := re.match(RE_HIT_CIRCLE, line):
                    x, y, time, object_type, hit_sound = get_standard_data_from_match(m)
                    # Hit sample
                    hit_sample_data = m.group(6)
                    m2 = re.search(RE_HIT_SAMPLE, hit_sample_data)
                    if m2 is None:
                        raise ChartParseError(line_num, f"Unparseable hit sample data '{line}'.")
                    hit_sample = hit_sample_from_match(m2)
                    chart.hit_objects.append(OsuHitCircle(x, y, time, object_type, hit_sound, hit_sample))
                elif m := re.match(RE_SLIDER, line):
                    x, y, time, object_type, hit_sound = get_standard_data_from_match(m)
                    # Slider specific
                    slider_type = m.group(6)
                    raw_curve_points = m.group(7)
                    raw_curve_points = raw_curve_points.split("|")
                    raw_curve_points = [s.split(":") for s in raw_curve_points]
                    curve_points = []
                    for p in raw_curve_points:
                        curve_points.append(OsuPoint(int(p[0]), int(p[1])))
                    slides = int(m.group(8))
                    length = float(m.group(9))
                    # Hit sample
                    hit_sample_data = m.group(10)
                    m2 = re.search(RE_HIT_SAMPLE, hit_sample_data)
                    if m2 is None:
                        raise ChartParseError(line_num, f"Unparseable hit sample data '{line}'.")
                    hit_sample = hit_sample_from_match(m2)
                    slider = OsuSlider(x, y, time, object_type, hit_sound,
                                       slider_type, curve_points, slides, length, [], [], hit_sample)
                    chart.hit_objects.append(slider)

                elif m := re.match(RE_SPINNER, line):
                    x, y, time, object_type, hit_sound = get_standard_data_from_match(m)
                    end_time = int(m.group(6)) / 1000
                    # Hit sample
                    hit_sample_data = m.group(7)
                    m2 = re.search(RE_HIT_SAMPLE, hit_sample_data)
                    if m2 is None:
                        raise ChartParseError(line_num, f"Unparseable hit sample data '{line}'.")
                    hit_sample = hit_sample_from_match(m2)
                    chart.hit_objects.append(OsuSpinner(x, y, time, object_type, hit_sound, end_time, hit_sample))
                elif m := re.match(RE_HOLD, line):
                    x, y, time, object_type, hit_sound = get_standard_data_from_match(m)
                    end_time = int(m.group(6)) / 1000
                    # Hit sample
                    hit_sample_data = m.group(7)
                    m2 = re.search(RE_HIT_SAMPLE, hit_sample_data)
                    if m2 is None:
                        raise ChartParseError(line_num, f"Unparseable hit sample data '{line}'.")
                    hit_sample = hit_sample_from_match(m2)
                    chart.hit_objects.append(OsuHold(x, y, time, object_type, hit_sound, end_time, hit_sample))
                else:
                    raise ChartParseError(line_num, f"Unknown hit object '{line}'.")
            else:
                raise ChartParseError(line_num, f"Unknown header '{current_header}'.")

        for ho in chart.hit_objects:
            if isinstance(ho, OsuSlider):
                ho.end_time = chart.calculate_slider_length(ho) + ho.time

        return chart

    def calculate_slider_length(self, slider: OsuSlider) -> Seconds:
        latest_timing_point = [t for t in self.timing_points if t.time <= slider.time][-1]
        return (slider.px_length / (self.difficulty.slider_multiplier * 100 * latest_timing_point.slider_velocity_multipler) * latest_timing_point.beat_length) * slider.slides
