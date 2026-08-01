-- Build the session described by $SESSION_DATA (emitted by
-- reaper_session.py), save the .RPP, render the master. Headless-safe:
-- everything is API-driven, no actions that open dialogs.

local scratch = os.getenv("SCRATCH") or "/tmp"
local logf = io.open(scratch .. "/reaper_build.log", "w")
local function log(s) logf:write(tostring(s) .. "\n") logf:flush() end

dofile(os.getenv("SESSION_DATA"))
log("data loaded: end_s=" .. SONG.end_s)

-- ---------------------------------------------------------------- helpers
local function db2lin(db) return 10 ^ (db / 20) end

local function add_track(idx, name, parent_depth)
  reaper.InsertTrackAtIndex(idx, false)
  local tr = reaper.GetTrack(0, idx)
  reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", name, true)
  if parent_depth then
    reaper.SetMediaTrackInfo_Value(tr, "I_FOLDERDEPTH", parent_depth)
  end
  return tr
end

local function add_fx(tr, spec)
  local fxi = reaper.TrackFX_AddByName(tr, spec.fx, false, -1)
  if fxi < 0 then log("FX MISS: " .. spec.fx) return -1 end
  -- set params by (case-insensitive, substring) name match
  local n = reaper.TrackFX_GetNumParams(tr, fxi)
  local function set_by_name(pname, value)
    local lname = string.lower(pname)
    for p = 0, n - 1 do
      local _, nm = reaper.TrackFX_GetParamName(tr, fxi, p, "")
      if string.lower(nm) == lname then
        reaper.TrackFX_SetParam(tr, fxi, p, value)
        return p
      end
    end
    for p = 0, n - 1 do
      local _, nm = reaper.TrackFX_GetParamName(tr, fxi, p, "")
      if string.find(string.lower(nm), lname, 1, true) then
        reaper.TrackFX_SetParam(tr, fxi, p, value)
        return p
      end
    end
    log("  param miss '" .. pname .. "' on " .. spec.fx)
    return nil
  end
  if string.find(spec.fx, "Parametric") and not PEQ_DUMPED then
    PEQ_DUMPED = true
    for p = 0, math.min(n - 1, 45) do
      local _, nm = reaper.TrackFX_GetParamName(tr, fxi, p, "")
      log("  peq param " .. p .. ": " .. nm)
    end
  end
  if spec.params then
    for _, pv in ipairs(spec.params) do set_by_name(pv.name, pv.value) end
  end
  -- LSP PEQ bands: params are named e.g. "Filter type 0", "Frequency 0"...
  if spec.bands then
    local typemap = {}    -- discover enum values by setting + reading name?
    -- LSP PEQ filter type enum order: Off, Bell, Hi-pass, Hi-shelf,
    -- Lo-pass, Lo-shelf, Notch, Resonance, Allpass, Bandpass, LUFS(?)
    local tv = {bell = 1, hipass = 2, hishelf = 3, lopass = 4, loshelf = 5}
    for _, b in ipairs(spec.bands) do
      local i, ty, fr, gn, q = b[1], b[2], b[3], b[4], b[5]
      set_by_name("Filter type " .. i, tv[ty] or 1)
      set_by_name("Frequency " .. i, fr)
      if gn ~= 0 then set_by_name("Gain " .. i, db2lin(gn)) end
      if q ~= 0 then set_by_name("Quality " .. i, q) end
    end
  end
  return fxi
end

local function add_audio_item(tr, file, vol_db, pan)
  local item = reaper.AddMediaItemToTrack(tr)
  local take = reaper.AddTakeToMediaItem(item)
  local src = reaper.PCM_Source_CreateFromFile(file)
  if not src then log("SRC MISS: " .. file) return end
  reaper.SetMediaItemTake_Source(take, src)
  local len = reaper.GetMediaSourceLength(src)
  reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0.0)
  reaper.SetMediaItemInfo_Value(item, "D_LENGTH", len)
  reaper.SetMediaItemTakeInfo_Value(take, "D_VOL", db2lin(vol_db or 0))
  if pan and pan ~= 0 then
    reaper.SetMediaItemTakeInfo_Value(take, "D_PAN", pan)
  end
  local base = file:match("([^/]+)$")
  reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", base, true)
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

local function fxparam_env(tr, fxi, pname, points)
  if #points == 0 then return end
  local n = reaper.TrackFX_GetNumParams(tr, fxi)
  local pidx = nil
  for p = 0, n - 1 do
    local _, nm = reaper.TrackFX_GetParamName(tr, fxi, p, "")
    if string.find(string.lower(nm), string.lower(pname), 1, true) then
      pidx = p break
    end
  end
  if not pidx then log("env param miss: " .. pname) return end
  local env = reaper.GetFXEnvelope(tr, fxi, pidx, true)
  for _, pt in ipairs(points) do
    reaper.InsertEnvelopePoint(env, pt[1], pt[2], 0, 0, false, true)
  end
  reaper.Envelope_SortPoints(env)
end

-- ---------------------------------------------------------------- tempo
for i, t in ipairs(SONG.tempo) do
  reaper.SetTempoTimeSigMarker(0, -1, t[1], -1, -1, t[2], 4, 4, false)
end
for _, r in ipairs(SONG.regions) do
  reaper.AddProjectMarker(0, true, r[1], r[2], r[3], -1)
end
log("tempo+regions done")

-- ---------------------------------------------------------------- tracks
local idx = 0

-- DRUMS folder
local drums = add_track(idx, "DRUMS", 1); idx = idx + 1
reaper.SetMediaTrackInfo_Value(drums, "D_VOL", db2lin(SONG.drum_bus_vol))
for _, f in ipairs(SONG.drum_glue) do add_fx(drums, f) end
for ci, child in ipairs(SONG.drums) do
  local depth = (ci == #SONG.drums) and -1 or 0
  local tr = add_track(idx, child.name, depth); idx = idx + 1
  reaper.SetMediaTrackInfo_Value(tr, "D_VOL", db2lin(child.vol))
  for _, it in ipairs(child.items) do
    add_audio_item(tr, it.file, it.vol, it.pan)
  end
  for _, f in ipairs(child.fx) do add_fx(tr, f) end
  if child.name == "SNARE" then SNARE_TR = tr end
end

-- audio buses
for _, bus in ipairs(SONG.buses) do
  local tr = add_track(idx, bus.name, 1); idx = idx + 1
  reaper.SetMediaTrackInfo_Value(tr, "D_VOL", db2lin(bus.vol))
  local fxis = {}
  for _, f in ipairs(bus.fx) do fxis[#fxis + 1] = {add_fx(tr, f), f.fx} end
  if bus.name == "GTRS" then
    -- ride: JS volume param envelope
    for _, e in ipairs(fxis) do
      if e[2] == "JS: utility/volume" then
        fxparam_env(tr, e[1], "volume", SONG.gtr_ride)
      end
    end
  end
  for ci, child in ipairs(bus.children) do
    local depth = (ci == #bus.children) and -1 or 0
    local ct = add_track(idx, child.name, depth); idx = idx + 1
    reaper.SetMediaTrackInfo_Value(ct, "D_VOL", db2lin(child.vol))
    if child.pan and child.pan ~= 0 then
      reaper.SetMediaTrackInfo_Value(ct, "D_PAN", child.pan)
    end
    for _, it in ipairs(child.items) do
      add_audio_item(ct, it.file, it.vol, it.pan)
    end
    for _, f in ipairs(child.fx) do add_fx(ct, f) end
  end
end

-- PLATE (snare send)
local plate = add_track(idx, "PLATE", 0); idx = idx + 1
reaper.SetMediaTrackInfo_Value(plate, "D_VOL", db2lin(-14.0))
for _, f in ipairs(SONG.plate_fx) do add_fx(plate, f) end
if SNARE_TR then
  local send = reaper.CreateTrackSend(SNARE_TR, plate)
  reaper.SetTrackSendInfo_Value(SNARE_TR, 0, send, "D_VOL", db2lin(0.0))
end

-- SOURCE folder: the composition as MIDI (muted, editable)
local src_parent = add_track(idx, "SOURCE (MIDI - the composition)", 1)
idx = idx + 1
reaper.SetMediaTrackInfo_Value(src_parent, "B_MUTE", 1)
for mi, mt in ipairs(SONG.midi) do
  local depth = (mi == #SONG.midi) and -1 or 0
  local tr = add_track(idx, mt.name, depth); idx = idx + 1
  reaper.SetMediaTrackInfo_Value(tr, "B_MUTE", 1)
  add_midi_item(tr, mt.notes)
end
log("tracks done: " .. idx)

-- ---------------------------------------------------------------- master
local master = reaper.GetMasterTrack(0)
local mfxis = {}
for _, f in ipairs(SONG.master_fx) do
  mfxis[#mfxis + 1] = {add_fx(master, f), f.fx}
end
-- vacuum sweep: master PEQ band-0 hipass frequency envelope
if #SONG.vacuum > 0 then
  for _, e in ipairs(mfxis) do
    if string.find(e[2], "Parametric") then
      fxparam_env(master, e[1], "frequency 0", SONG.vacuum)
      break
    end
  end
end
-- convergence trim on the JS volume instance
for _, e in ipairs(mfxis) do
  if e[2] == "JS: utility/volume" then
    local n = reaper.TrackFX_GetNumParams(master, e[1])
    for p = 0, n - 1 do
      local _, nm = reaper.TrackFX_GetParamName(master, e[1], p, "")
      if string.find(string.lower(nm), "volume", 1, true) then
        reaper.TrackFX_SetParam(master, e[1], p, SONG.master_trim)
        break
      end
    end
  end
end
log("master done, trim=" .. SONG.master_trim)

-- ---------------------------------------------------------------- render
reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 0, true)
reaper.GetSetProjectInfo(0, "RENDER_STARTPOS", 0, true)
reaper.GetSetProjectInfo(0, "RENDER_ENDPOS", SONG.end_s, true)
reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
reaper.GetSetProjectInfo_String(0, "RENDER_FILE", SONG.render_dir, true)
reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", SONG.render_pattern, true)
reaper.GetSetProjectInfo_String(0, "RENDER_FORMAT", "evaw", true)

reaper.Main_SaveProjectEx(0, SONG.rpp, 0)
log("saved rpp")
reaper.Main_OnCommand(42230, 0)   -- render, auto-close render dialog
log("render complete")
logf:close()
reaper.Main_OnCommand(40004, 0)  -- quit (project already saved)
