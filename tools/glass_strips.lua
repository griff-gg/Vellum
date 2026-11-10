-- Glass tab rows whose tabs change at runtime (skills, shop): the pill glides to the clicked or selected tab.
-- It reads where the tab really is (offset_left / offset_width), so it works for any number of tabs.
-- The first line of this script (added per page) lists the strip ids; each strip has a pill div with id gl-dyn- followed by the strip id.
pcall(function()
    local doc = document
    local function by_id(i) return doc:GetElementById(i) end

    local function put(pill, tab)
        local w = tab.offset_width
        if not (w and w > 1) then return end
        pill.style.left = tostring(tab.offset_left) .. 'px'
        pill.style.width = tostring(w) .. 'px'
    end
    local function selected(c)
        local ok, sel = pcall(function() return c:IsClassSet('selected') or c:IsClassSet('active') end)
        return ok and sel
    end
    local function sync()
        for _, id in ipairs(STRIPS) do
            local strip, pill = by_id(id), by_id('gl-dyn-' .. id)
            if strip and pill then
                local c = strip.first_child
                while c do
                    if c ~= pill and selected(c) then
                        put(pill, c)
                        break
                    end
                    c = c.next_sibling
                end
            end
        end
    end

    -- a click moves the pill straight away (the page marks the tab selected a moment later)
    doc:AddEventListener('click', function(ev)
        pcall(function()
            local t = ev.target_element
            while t and t ~= doc do
                local p = t.parent_node
                if p then
                    for _, id in ipairs(STRIPS) do
                        if p.id == id then
                            local pill = by_id('gl-dyn-' .. id)
                            if pill then put(pill, t) end
                            return
                        end
                    end
                end
                t = p
            end
        end)
    end)

    -- a hidden element's short animation wakes us up twice a second: tabs appear and change with your class
    local tick = by_id('gl-strips-tick')
    local flip = false
    local function step()
        pcall(sync)
        if tick then
            flip = not flip
            tick:SetClass('tk-a', flip)
            tick:SetClass('tk-b', not flip)
        end
    end
    if tick then tick:AddEventListener('animationend', function() pcall(step) end) end
    doc:AddEventListener('show', function() pcall(sync) end)
    pcall(step)
end)
