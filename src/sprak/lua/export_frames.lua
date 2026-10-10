for name, file in pairs(app.params) do
    local sprite_name = name .. ".{frame0001}.png"
    app.command.OpenFile { filename = file }
    app.command.SaveFileCopyAs { filename = sprite_name, filenameFormat = sprite_name }
    app.command.CloseFile()
end
