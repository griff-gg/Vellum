-- Glass zone notice: the pill drops in from the top edge with a bounce every time a new zone name arrives.
-- Keyframes come in identical -a / -b pairs: switching to the other one restarts the animation.
pcall(function()
    local doc = document
    local function by_id(i) return doc:GetElementById(i) end
    local flip = false
    local last = nil

    local function play()
        local e = by_id('gl-island')
        if not e then return end
        flip = not flip
        e.style.animation = '0.6s back-out 1 gl-drop' .. (flip and '-a' or '-b')
    end
    local function check()
        local z = by_id('zone-name')
        local txt = z and z.inner_rml or ''
        if txt ~= last then
            last = txt
            play()
        end
    end

    -- every time the game shows the notice, play it again
    doc:AddEventListener('show', function()
        last = nil
        pcall(check)
    end)

    -- a hidden element's short animation wakes us up a few times a second, in case the name changes while it is open
    local tick = by_id('gl-zn-tick')
    local tf = false
    local function step()
        pcall(check)
        if tick then
            tf = not tf
            tick:SetClass('tk-a', tf)
            tick:SetClass('tk-b', not tf)
        end
    end
    if tick then tick:AddEventListener('animationend', function() pcall(step) end) end
    pcall(step)
end)
