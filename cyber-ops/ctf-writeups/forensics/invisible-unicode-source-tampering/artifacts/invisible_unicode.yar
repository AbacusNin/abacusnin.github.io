rule Invisible_Unicode_Source_Review
{
    meta:
        description = "Triage UTF-8 source files containing Unicode Tags or selected invisible controls"
        status = "synthetic proof of concept; review matches before action"
        author = "Abacus"
    strings:
        $tag_plane_a = { F3 A0 80 }
        $tag_plane_b = { F3 A0 81 }
        $zero_width_space = { E2 80 8B }
        $zero_width_joiner = { E2 80 8D }
        $right_to_left_override = { E2 80 AE }
        $word_joiner = { E2 81 A0 }
    condition:
        filesize <= 1000000 and any of them
}
