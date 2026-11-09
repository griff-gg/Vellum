-- Glass: each time the window opens it fades and settles in, then a streak of light crosses the glass.
-- Two identical keyframe sets (-a / -b): switching to the other one restarts the animation.
pcall(function()
    local doc = document
    local flip = false
    local function opened()
        flip = not flip
        doc:SetClass('gl-shown-a', flip)
        doc:SetClass('gl-shown-b', not flip)
        doc.style.animation = '0.15s cubic-out 1 ' .. (flip and 'gl-open-a' or 'gl-open-b')
    end
    doc:AddEventListener('show', function() pcall(opened) end)
    opened()
end)
