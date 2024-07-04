## Event
* time: `float` - The time this event happens (relative to the song start time) in seconds.

## Note
### Attributes
* chart: `Chart` - The chart this note belongs to.
* time: `float` - (in seconds, 0 is the beginning of the song)
* lane: `int` - The key the user will have to hit to trigger this note (which usually corrosponds with it's X position on the highway)
* length: `float`: the length of the note in seconds, 0 by default
* type: `str`: the note's type [different per gamemode.]

* hit: `bool`: has this note been hit?
* missed: `bool`: has this note been missed?
* hit_time: `float`: when was this note hit? (seconds)

### Properties
* end: `float` - The end time of the note (`self.time + self.length`)
* is_sustain: `bool` - If this note is a long note or not (`self.length > 0)`

## Chart
### Attributes
* song: `Song` - The Song this chart is associated with.
* gamemode: `str` - The gamemode you're expected to play this song in. (`4k`, `hero`, `taiko`, etc.)
* difficulty: `str` - The difficulty level of this chart. Each gamemode has different difficulties, so they aren't explicitly sortable.
* instrument: `str` - The instrument associated with chart. Some gamemodes don't have this so I'm not sure what to do in that instance. Can be thought of as "playstyle".
* notes: `list[Note]` - A list of all notes in this chart.
* events: `list[Event]` - A list of all chart-specific events in this chart.
* bpm: `float` - The starting BPM of this chart. This can change throughout the song, so shouldn't be expected to be static.

## Song
### Attributes
* path: `Path` - The path to the folder containing this song's files. (audio, charts, etc.)
* metadata: `Metadata` - 
* charts: `list[Chart]` - A list of every `Chart` associated with this song. These are all assumed to have a shared gamemode.
* events: `list[Event]` - A list of global events on this song. These are events that are not unique per-chart.

### Functions
* `get_chart(self, difficulty: Optional[str], instrument: Optional[str]) -> Chart` - Returns a chart matching the specified difficulty, instrument, or both.
* `events_by_type(self, t: Type) -> list[Event]` - Filters `.events` to only contain items of type `t`.
* `parse(cls, folder: Path) -> Song` - Returns a fully parsed Song object (raises `NotImplementedError` when used on the base class.)

## Highway

### Attributes
* chart: `Chart` - chart to render
* notes: `list[Note]` - copy of `self.chart.notes`
* pos: `tuple[int, int]` - where to render (x, y)
* size: `tuple[int, int]` - how large the highway is (w, h) 
* gap: `int` - px gap between lanes
* downscroll: `bool` - whether or not the notes come from the top of the screen and go down
* viewport: `float` - how many seconds of song are in view at a time
* static_camera: `arcade.cameera.Camera2D` - the camera designed to render static elements of the highway
* highway_camera: `arcade.cameera.Camera2D` - the camera designed to render moving (scrolling) elements of the highway
* song_time: `float` - the current time of the song (dictates current notes to render and their positions)

### Properties
* note_size: `int` - calculated width of a single note
* strikeline_y: `int` - calculated y to place the strikeline
* visible_notes: `list[Note]`※ - notes currently visible on screen

### Functions
* `lane_x(self, lane_num: int) -> int`: the x coordinate of a note in lane `lane_num`
* `note_y(self, at: float)` - the y coordinate of a note that occurs at `at` seconds into the song
* `update(song_time: float)` - update the highway to match the current song time
* `draw()` - draw the highway (raises `NotImplementedError` when used on the base class.)

## NoteSprite(arcade.Sprite)†
### Attributes
* note: `Note` - the note this sprite represents
* highway: `Highway` - the highway this note sprite is a part of

## Judgement
### Attributes
* name: `str` - the name of this judgement (formatted)
* key: `str` - a unique key for this judgement (also likely sprite name)
* ms: `int` - the maximum millseconds a note can be hit from 0 and get this judgement
* score: `int` - how much score a note with this judging provides
* accuracy_weight: `float` - how much scoring a note with this judging affects "weighted accuracy" (it's a rhythm game thing)
* hp_change: `float` - how much scoring a note with this judging affects HP

### Properties
* seconds: `float` - `self.ms / 1000`

## Results
### Attributes
* chart: `Chart` - the chart these results were generated for.
* hit_window: Seconds - see *Engine.*
* judgements: `list[Judgement]` - see *Engine.*
* all_judgements: `list[tuple[Seconds, Seconds, Judgement]]` - a list of tuples representing hit notes (correct time, offset from correct time, judgement it recieved)
* score: `int` - see *Engine.*
* hits: `int` - see *Engine.*
* misses: `int` - see *Engine.*
* accuracy: `float` - see *Engine.*
* grade: `str` - see *Engine.*
* fc_type: `str` - see *Engine.*
* streak: `int` - see *Engine.*
* max_streak: `int` - see *Engine.*

## Engine
### Attributes
* chart: `Chart` - the Chart to read notes from for scoring.
* mapping: `list[Key]`★ - mapping keys to lanes
* hit_window: `float`★ - the maximum seconds before a failed/missed note occurs
* judgements: `list[Judgement]` - the judgements used for scoring notes
* offset: `float` - the seconds difference between "song time" and "real time" (used for audio calibration)
* chart_time: `float` - seconds into the chart currently
* active_notes: `list[Note]` - notes we have not determined score for yet
* key_state: `list[bool]`★ - the current held keys, corresponds to mapping
* score: `int` - the current score
* hits: `int` - total count of notes hit
* misses: `int` - total count of notes missed
* streak: `int`† - current hit streak amount
* max_streak: `int`† - maximum hit streak amount so far
* max_notes: `int`※ - maximum possible notes in the chart
* weighed_hit_notes: `float` - it's a rhythm game thing honestly

### Properties
* accuracy: `float` - the current weighted accuracy
* grade: `str` the current grade (SS - F)
* fc_type: `str` - either a type of FC or a type of Clear

### Functions
* `update(self, song_time: float)` - update the engine to reflect the current song time (seconds)
* `process_keystate()` - recieve and process user input (raises `NotImplementedError` when used on the base class.)
* `get_note_judgement(self, note: Note)` - return what judgement a note should recieve
* `generate_results() -> Results` - generate a results object based on the current engine state

## Footnotes
† not currently on the base class/a generic.
★ to be phased out
※ may be unused
* Should `Note`s be `Event`s? Just noticed that they aren't.
* `highway_camera` should be renamed. `scrolling_camera`?
* `visible_notes` is likely broken. unused?
