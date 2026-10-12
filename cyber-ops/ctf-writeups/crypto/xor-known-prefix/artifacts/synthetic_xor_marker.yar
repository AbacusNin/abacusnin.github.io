rule Synthetic_XOR_Marker_In_PE
{
    meta:
        description = "Lab-only encoded marker in an MZ file; adapt after case review"
        reference = "https://yara.readthedocs.io/en/stable/writingrules.html#xor-strings"

    strings:
        $marker = "lab-control.example" xor(0x01-0xff)

    condition:
        filesize <= 20MB and uint16(0) == 0x5a4d and $marker
}
