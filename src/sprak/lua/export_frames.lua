local json_data = {}
local i = 1;

for name, file in pairs(app.params) do
    json_data[name] = {}
    json_data[name]["frames"] = {}
    json_data[name]["tags"] = {}
    json_data[name]["slices"] = {}

    app.command.OpenFile { filename = file }
    for _, frame in ipairs(app.sprite.frames) do
        local frame_name = string.format("%s.%04d", name, frame.frameNumber)
        local frame_duration_ms = frame.duration * 1000
        local frame_filename = i .. ".png"
        local frame_filepath = app.fs.joinPath(app.fs.currentPath, frame_filename)

        json_data[name]["frames"][frame_name] = {}
        json_data[name]["frames"][frame_name]["frame_number"] = frame.frameNumber
        json_data[name]["frames"][frame_name]["duration"] = frame_duration_ms
        json_data[name]["frames"][frame_name]["filepath"] = frame_filepath

        app.command.SaveFileCopyAs { filename = frame_filepath }
        i = i + 1
    end
    app.command.CloseFile()
end

print(json.encode(json_data))
