local json_data = {}

for name, file in pairs(app.params) do
    json_data[name] = {}
    json_data[name]["frames"] = {}
    json_data[name]["tags"] = {}
    json_data[name]["slices"] = {}

    app.command.OpenFile { filename = file }

    -- Save frames
    local filename = name .. ".{frame0001}.png"
    app.command.SaveFileCopyAs { filename = filename, filenameFormat = filename }

    -- Frame data
    for _, frame in ipairs(app.sprite.frames) do
        local frame_name = string.format("%s.%04d", name, frame.frameNumber)
        local frame_duration_ms = frame.duration * 1000
        local frame_filename = frame_name .. ".png"
        local frame_filepath = app.fs.joinPath(app.fs.currentPath, frame_filename)

        json_data[name]["frames"][frame_name] = {}
        json_data[name]["frames"][frame_name]["frame_number"] = frame.frameNumber
        json_data[name]["frames"][frame_name]["duration"] = frame_duration_ms
        json_data[name]["frames"][frame_name]["filepath"] = frame_filepath
    end

    -- Tag data
    for _, tag in ipairs(app.sprite.tags) do
        json_data[name]["tags"][tag.name] = {}
        json_data[name]["tags"][tag.name]["from"] = tag.fromFrame.frameNumber
        json_data[name]["tags"][tag.name]["to"] = tag.toFrame.frameNumber
    end

    -- Slice data
    for i, slice in ipairs(app.sprite.slices) do
        json_data[name]["slices"][i] = {}
        json_data[name]["slices"][i]["bounds"] = {}
        json_data[name]["slices"][i]["bounds"]["x"] = slice.bounds.x
        json_data[name]["slices"][i]["bounds"]["y"] = slice.bounds.y
        json_data[name]["slices"][i]["bounds"]["w"] = slice.bounds.width
        json_data[name]["slices"][i]["bounds"]["h"] = slice.bounds.height
        json_data[name]["slices"][i]["center"] = {}
        json_data[name]["slices"][i]["center"]["x"] = slice.center.x
        json_data[name]["slices"][i]["center"]["y"] = slice.center.y
        json_data[name]["slices"][i]["center"]["w"] = slice.center.width
        json_data[name]["slices"][i]["center"]["h"] = slice.center.height
    end

    app.command.CloseFile()
end

-- Output JSON
print(json.encode(json_data))
