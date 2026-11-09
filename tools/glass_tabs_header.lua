-- Glass tabs in the title row: the pill (div#gl-tab-slider) slides to the clicked tab.
-- Each tab carries gl-tab="0..7"; the tabset still switches the panels, we only move the pill.
pcall(function()
    local doc = document
    doc:AddEventListener('click', function(ev)
        pcall(function()
            local t = ev.target_element
            while t and t ~= doc do
                local idx = tonumber(t:GetAttribute('gl-tab'))
                if idx ~= nil then
                    local pill = doc:GetElementById('gl-tab-slider')
                    if pill then
                        for i = 1, 7 do pill:SetClass('at' .. i, idx == i) end
                    end
                    return
                end
                t = t.parent_node
            end
        end)
    end)
end)
