-- Glass: the pill under the arena tabs (All / Dungeons / PvP) slides to the clicked tab.
-- The arena script marks each tab with arena-filter="0|1|2"; we only move the pill, it still does the filtering.
pcall(function()
    local doc = document
    doc:AddEventListener('click', function(ev)
        pcall(function()
            local t = ev.target_element
            while t and t ~= doc do
                local idx = tonumber(t:GetAttribute('arena-filter'))
                if idx ~= nil then
                    local pill = doc:GetElementById('gl-arena-slider')
                    if pill then
                        pill:SetClass('at1', idx == 1)
                        pill:SetClass('at2', idx == 2)
                    end
                    return
                end
                t = t.parent_node
            end
        end)
    end)
end)
