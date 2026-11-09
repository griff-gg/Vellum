-- Glass: the pill under the options tabs slides to the clicked tab. Each tab carries gl-tab="0..6";
-- the tabset still switches the panels, we only move the pill.
pcall(function()
    local doc = document
    doc:AddEventListener('click', function(ev)
        pcall(function()
            local t = ev.target_element
            while t and t ~= doc do
                local idx = tonumber(t:GetAttribute('gl-tab'))
                if idx ~= nil then
                    local pill = doc:GetElementById('gl-opt-slider')
                    if pill then
                        for i = 1, 6 do pill:SetClass('at' .. i, idx == i) end
                    end
                    return
                end
                t = t.parent_node
            end
        end)
    end)
end)
