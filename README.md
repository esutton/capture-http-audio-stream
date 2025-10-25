# capture-http-audio-stream
Experiments to capture internet streaming radio

# The Spy FM

https://thespyfm.com/

The simplest programmatic endpoints that The Spy publishes are:
```
# AAC/HLS redirect:
https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2AAC.aac

# MP3 redirect (commonly available):
# Note: Did not see any ICY messages
https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3
```

```
# Play in VLC / mpv:
vlc "https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3"

# Save to file with ffmpeg (MP3):
ffmpeg -i "https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3" -c copy out.mp3
```


### ffmpeg Display ICY messages
```
ffmpeg -icy 1 -i "https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3" -f null -
```

This should display console messages such as StreamTitle.
``` 
ICY Metadata: StreamTitle='Talking Heads - Once In A Lifetime';
```
- I saw no console messages displayed. 
- How can split stream into track files? Silence gap? Change in freq?


 ### If ICY metadata is available

You can pipe ffmpeg’s stdout metadata into your own code, or use -f segment to split manually when a title changes.

Example using ffmpeg’s built-in segmenter:
```
ffmpeg -icy 1 -i "https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3" \
       -f segment -segment_time 0 -reset_timestamps 1 \
       -segment_list out_playlist.m3u8 -y "track-%03d.mp3"
```

### If ICY metadata is not available

Then you can only split the continuous stream by time, silence detection, or external data.

🕒 Option A – Split by fixed time

Say you just want 5-minute segments:

Each file will contain about 5 minutes of audio.
Not perfect for songs, but simple and reliable.
```
ffmpeg -i "https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3" \
       -f segment -segment_time 300 -c copy "segment_%03d.mp3"
```

Option B – Split by silence (approximate song boundaries)

If the station leaves short silences between songs (many do), you can use ffmpeg’s silencedetect filter:
```
ffmpeg -i "https://playerservices.streamtheworld.com/api/livestream-redirect/KOSUHD2.mp3" \
  -af silencedetect=noise=-30dB:d=2 \
  -f null - 2> silence.log

# Example output
[silencedetect @ 0x...] silence_start: 123.4
[silencedetect @ 0x...] silence_end: 125.7 | silence_duration: 2.3
```

You can then parse that log and cut the audio accordingly:
```
ffmpeg -i stream.mp3 -ss START -to END -c copy output.mp3
```

Option C – Use external “now playing” API

Many modern radio networks (including StreamTheWorld stations) have JSON or XML “now playing” feeds on their websites — even if the raw stream has no ICY data.

For The Spy (KOSU HD2), you can often find this by inspecting their player page.
If available, your Python script could poll that endpoint every few seconds, detect song title changes, and then tell ffmpeg (or Python’s file writer) to start a new file.

Would you like me to find The Spy’s live “now playing” metadata API (if one exists) so you could use that to split tracks even if ICY metadata is absent?



I did a search but couldn’t confidently find a public, documented “now playing” API specific to The Spy (or its StreamTheWorld feed) that guarantees current-track metadata independent of ICY.

However, I found some leads and strategies you can try — they may or may not work depending on how The Spy / StreamTheWorld is configured:

⸻

🔍 Leads & Clues
	1.	StreamTheWorld “livestream” API
I found that StreamTheWorld provides a /api/livestream endpoint which returns an XML configuration including mountpoints, servers, etc.  ￼
That doesn’t necessarily guarantee now playing metadata (artist/title), but it’s how the streaming backend config is exposed.
	2.	Toofishes blog — StreamTheWorld command-line script
A blog describes how to use the StreamTheWorld API to fetch mountpoint and server info given a callsign.  ￼
The blog doesn’t show “now playing” metadata, but it is a path to discovering how the streams are provisioned.

⸻

🛠 Strategy: Discover a Hidden “Now Playing” Feed

Here are things you can try to locate a working metadata API for The Spy:
	•	View network requests in the browser player
  
Go to The Spy’s web player (on their site) while a song is playing, 
open the browser’s developer tools (Network tab), 
filter for json / xml / api / nowplaying strings, 
and see if there’s a request to fetch “current track” or “now playing” data.

	•	Try standard radio metadata endpoints
Many stations expose endpoints like:
```
https://playerservices.streamtheworld.com/nowplaying?station=KOSUHD2
https://provisioning.streamtheworld.com/nowplaying?mount=KOSUHD2
https://api.thespyfm.com/nowplaying
```

Use StreamTheWorld’s “live_stream_config” XML
Fetch:
```
https://playerservices.streamtheworld.com/api/livestream?version=1.8&mount=KOSUHD2

curl -A "Mozilla/5.0" "https://playerservices.streamtheworld.com/api/livestream?version=1.2&mount=SPYFMAAC&lang=en"

```

Inspect the XML to see if there are tags for metadata. (The sample XML configuration I saw in search results includes <mountpoints> and <status> etc.)  ￼

	•	Check affiliated station or aggregator APIs
Since The Spy is affiliated with KOSU, check if KOSU’s site or backend offers a “Now Playing / On Air” feed that includes The Spy metadata. (KOSU’s “Now Playing” content is visible on its site for its NPR programming)  ￼

⸻

If you like, I can try to programmatically probe a few candidate endpoints right now (XML, JSON guesses) and see if any return live metadata for The Spy, then share the working URL with you. Do you want me to do that?




