-- Glass minimap: Dynamic Island morph when collapsing / restoring, and a Spotify-style scroll for long zone names.
-- Keyframes come in identical -a / -b pairs: switching to the other one restarts an animation.
pcall(function()
    local doc = document
    local function by_id(i) return doc:GetElementById(i) end

    -- morph: the state that just appeared springs in from the shape of the other one
    local flip = false
    local function island(id)
        local e = by_id(id)
        if not e then return end
        flip = not flip
        local name = (id == 'minimap-minimized') and 'gl-pill' or 'gl-panel'
        e.style.animation = '0.5s back-out 1 ' .. name .. (flip and '-a' or '-b')
    end
    doc:AddEventListener('click', function(ev)
        pcall(function()
            local t = ev.target_element
            while t and t ~= doc do
                if t:IsClassSet('btn-minimize') then island('minimap-minimized') return end
                if t:IsClassSet('btn-restore') then island('minimap-normal') return end
                t = t.parent_node
            end
        end)
    end)

    -- marquee: text wider than its box scrolls back and forth (a class named mq plus the distance in dp picks the distance)
    local MQ = { { text = 'zone-name-text', box = 'zone-name', dp = 112 },
                 { text = 'zone-name-min-text', box = 'zone-name-min', dp = 120 } }
    local last = {}
    local function fit(m)
        local t, b = by_id(m.text), by_id(m.box)
        if not (t and b) then return end
        local bw = b.client_width
        if not (bw > 0) then return end
        local over = (t.offset_width - bw) / (bw / m.dp)
        local key = 0
        if over > 1 then key = math.min(math.floor(over / 4 + 0.5) * 4, 160) end
        if over > 1 and 4 > key then key = 4 end
        if key ~= last[m.text] then
            if last[m.text] and last[m.text] > 0 then t:SetClass('mq-' .. last[m.text], false) end
            if key > 0 then t:SetClass('mq-' .. key, true) end
            last[m.text] = key
        end
    end
    -- a hidden element's animation ends once a second and wakes us up (zone names change as you travel)
    local tick = by_id('gl-tick')
    local tflip = false
    local function step()
        for _, m in ipairs(MQ) do pcall(fit, m) end
        if tick then
            tflip = not tflip
            tick:SetClass('tk-a', tflip)
            tick:SetClass('tk-b', not tflip)
        end
    end
    if tick then tick:AddEventListener('animationend', function() pcall(step) end) end
    pcall(step)
end)
