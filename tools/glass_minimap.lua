-- Glass minimap: a Dynamic Island style morph when collapsing / restoring (size only, no fading), and a Spotify-style scroll for long zone names.
-- Keyframes come in identical -a / -b pairs: switching to the other one restarts an animation.
pcall(function()
    local doc = document
    local function by_id(i) return doc:GetElementById(i) end

    -- morph: the state that just appeared springs in from the shape of the other one (no opacity: fades render badly here)
    local flip = false
    local function island(id)
        local e = by_id(id)
        if not e then return end
        flip = not flip
        local name = (id == 'minimap-minimized') and 'gl-pill' or 'gl-panel'
        e.style.animation = '0.45s back-out 1 ' .. name .. (flip and '-a' or '-b')
    end

    -- marquee: text wider than its box scrolls back and forth (a class named mq plus the distance in dp picks the distance).
    -- Uses the measured width when the game reports one, otherwise an estimate from the letter count.
    local MQ = { { text = 'zone-name-text', box = 'zone-name', dp = 104 },
                 { text = 'zone-name-min-text', box = 'zone-name-min', dp = 104 } }
    local last = {}
    local function fit(m)
        local t, b = by_id(m.text), by_id(m.box)
        if not (t and b) then return end
        -- the game reports an inline box no wider than its clip box, so the width is estimated from the letters:
        -- the title is small spaced capitals, about 7.4 dp per letter, narrower for spaces, quotes and thin letters
        local bw, tw = b.client_width, t.offset_width
        local width = 0
        for ch in string.gmatch(t.inner_rml or '', '.') do
            if ch == ' ' then width = width + 4.6
            elseif ch == "'" or ch == '.' or ch == ',' or ch == '-' then width = width + 4.9
            elseif ch == 'I' or ch == 'i' or ch == 'j' or ch == 'J' or ch == '1' then width = width + 4.8
            elseif ch == 'M' or ch == 'm' or ch == 'W' or ch == 'w' then width = width + 10.2
            else width = width + 7.4 end
        end
        if bw and tw and bw > 1 and tw > 1 then width = math.max(width, tw / (bw / m.dp)) end
        local over = width - m.dp + 10
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
