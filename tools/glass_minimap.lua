-- Glass minimap: a bouncy pop when collapsing / restoring, and a Spotify-style scroll for long zone names.
-- Keyframes come in identical -a / -b pairs: switching to the other one restarts an animation.
pcall(function()
    local doc = document
    local function by_id(i) return doc:GetElementById(i) end

    -- pop: the state that just appeared bounces in
    local flip = false
    local function island(id)
        local e = by_id(id)
        if not e then return end
        flip = not flip
        local name = (id == 'minimap-minimized') and 'gl-pill' or 'gl-panel'
        e.style.animation = '0.38s back-out 1 ' .. name .. (flip and '-a' or '-b')
    end

    -- marquee: text wider than its box scrolls back and forth (a class named mq plus the distance in dp picks the distance).
    -- Uses the measured width when the game reports one, otherwise an estimate from the letter count.
    local MQ = { { text = 'zone-name-text', box = 'zone-name', dp = 116 },
                 { text = 'zone-name-min-text', box = 'zone-name-min', dp = 118 } }
    local last = {}
    local function fit(m)
        local t, b = by_id(m.text), by_id(m.box)
        if not (t and b) then return end
        local bw, tw = b.client_width, t.offset_width
        local ratio = 1
        local width
        if bw and tw and bw > 1 and tw > 1 then
            ratio = bw / m.dp
            width = tw / ratio
        else
            width = string.len(t.inner_rml or '') * 6.2
        end
        local over = width - m.dp + 4
        local key = 0
        if over > 2 then key = math.min(math.max(math.floor(over / 4 + 0.5) * 4, 4), 160) end
        if key ~= last[m.text] then
            print('[glass minimap] ' .. m.text .. ' box ' .. tostring(bw) .. ' text ' .. tostring(tw) .. ' width_dp ' .. tostring(width) .. ' scroll ' .. key)
            if last[m.text] and last[m.text] > 0 then t:SetClass('mq-' .. last[m.text], false) end
            if key > 0 then t:SetClass('mq-' .. key, true) end
            last[m.text] = key
        end
    end
    local function refit()
        for _, m in ipairs(MQ) do pcall(fit, m) end
    end

    doc:AddEventListener('click', function(ev)
        pcall(function()
            local t = ev.target_element
            while t and t ~= doc do
                if t:IsClassSet('btn-minimize') then island('minimap-minimized') refit() return end
                if t:IsClassSet('btn-restore') then island('minimap-normal') refit() return end
                t = t.parent_node
            end
        end)
    end)
    doc:AddEventListener('mouseover', function() pcall(refit) end)
    doc:AddEventListener('show', function() pcall(refit) end)

    -- a hidden element's animation ends every 1.2 s and wakes us up (zone names change as you travel)
    local tick = by_id('gl-tick')
    local tflip = false
    local function step()
        refit()
        if tick then
            tflip = not tflip
            tick:SetClass('tk-a', tflip)
            tick:SetClass('tk-b', not tflip)
        end
    end
    if tick then tick:AddEventListener('animationend', function() pcall(step) end) end
    pcall(step)
end)
