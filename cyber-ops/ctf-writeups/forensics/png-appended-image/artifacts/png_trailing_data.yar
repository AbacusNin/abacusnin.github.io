rule png_immediate_stripped_image_candidate
{
    meta:
        description = "PNG IEND bytes immediately followed by a stripped IHDR header"
        status = "triage_only"
    strings:
        $sig = { 89 50 4E 47 0D 0A 1A 0A }
        $iend = { 00 00 00 00 49 45 4E 44 AE 42 60 82 }
        $next_ihdr = { 00 00 00 0D 49 48 44 52 }
    condition:
        $sig at 0 and $iend and
        for any i in (1..#iend) : (
            $next_ihdr at (@iend[i] + 12)
        )
}
