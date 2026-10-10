local json_data = {}

-- ToDo: slices, animations

for sprite_name, file in pairs(app.params) do
    json_data[sprite_name] = {}
    json_data[sprite_name]["frames"] = {}
    app.command.OpenFile { ui = false, filename = file }
    for _, frame in ipairs(app.sprite.frames) do
        local frame_number_str = string.format("%04d", frame.frameNumber)
        local frame_name = sprite_name .. "." .. frame_number_str
        local rel_path = frame_name .. ".png"
        local frame_duration_ms = frame.duration * 1000
        local frame_data = {
            rel_path = rel_path,
            frame_number = frame.frameNumber,
            duration = frame_duration_ms,
        }
        json_data[sprite_name]["frames"][frame_name] = frame_data
    end
    app.command.CloseFile()
end

print(json.encode(json_data))
