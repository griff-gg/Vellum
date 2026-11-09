pcall(function()
    local doc = document
    local tests = { 'grad', 'glow', 'hard', 'inset', 'drop', 'blur' }
    local active = nil
    local function pick(name)
        local demo = doc:GetElementById('gp-demo')
        if not demo then return end
        for _, t in ipairs(tests) do
            demo:SetClass('t-' .. t, false)
            local b = doc:GetElementById('gp-' .. t)
            if b then b:SetClass('on', false) end
        end
        if active == name then
            active = nil
            demo.inner_rml = 'all off'
            return
        end
        active = name
        demo:SetClass('t-' .. name, true)
        local b = doc:GetElementById('gp-' .. name)
        if b then b:SetClass('on', true) end
        demo.inner_rml = string.upper(name) .. ' on'
    end
    doc:AddEventListener('click', function(ev)
        pcall(function()
            local id = ev.target_element.id
            if string.sub(id, 1, 3) == 'gp-' and id ~= 'gp-demo' then pick(string.sub(id, 4)) end
        end)
    end)
end)
