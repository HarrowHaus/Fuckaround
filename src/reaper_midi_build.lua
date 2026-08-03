-- Build a MIDI-only session from $SESSION_DATA: tempo map, section
-- markers, one track per part. No audio, no FX, no render — just save.

local scratch = os.getenv("SCRATCH") or "/tmp"
local logf = io.open(scratch .. "/midi_build.log", "w")
local function log(s) logf:write(tostring(s) .. "\n") logf:flush() end

dofile(os.getenv("SESSION_DATA"))
log("data loaded: end_s=" .. SONG.end_s)

local function add_track(idx, name)
  reaper.InsertTrackAtIndex(idx, false)
  local tr = reaper.GetTrack(0, idx)
  reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", name, true)
  return tr
end

local function add_midi_item(tr, notes)
  if #notes == 0 then return end
  local item = reaper.CreateNewMIDIItemInProj(tr, 0, SONG.end_s, false)
  local take = reaper.GetActiveTake(item)
  for _, nt in ipairs(notes) do
    local p0 = reaper.MIDI_GetPPQPosFromProjTime(take, nt[1])
    local p1 = reaper.MIDI_GetPPQPosFromProjTime(take, nt[2])
    reaper.MIDI_InsertNote(take, false, false, p0, p1, 0, nt[3], nt[4], true)
  end
  reaper.MIDI_Sort(take)
end

for _, t in ipairs(SONG.tempo) do
  reaper.SetTempoTimeSigMarker(0, -1, t[1], -1, -1, t[2], 4, 4, false)
end
for _, r in ipairs(SONG.regions) do
  reaper.AddProjectMarker(0, true, r[1], r[2], r[3], -1)
end
log("tempo+regions done: " .. #SONG.tempo .. " tempo pts, " ..
    #SONG.regions .. " regions")

for i, mt in ipairs(SONG.midi) do
  local tr = add_track(i - 1, mt.name)
  add_midi_item(tr, mt.notes)
end
log("tracks done: " .. #SONG.midi)

reaper.Main_SaveProjectEx(0, SONG.rpp, 0)
log("saved: " .. SONG.rpp)
logf:close()
reaper.Main_OnCommand(40004, 0)  -- quit
