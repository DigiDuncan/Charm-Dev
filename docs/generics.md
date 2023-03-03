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
