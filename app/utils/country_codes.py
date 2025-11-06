SUPPORTED_COUNTRY_CODES = {
    "AF", "AL", "DZ", "AS", "AD", "AO", "AI", "AG", "AR", "AM", "AW", "AU", "AT", "AZ",
    "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ", "BM", "BT", "BO", "BA", "BW", "BR",
    "BN", "BG", "BF", "BI", "KH", "CM", "CA", "CV", "KY", "CF", "TD", "CL", "CO", "KM",
    "CG", "CD", "CK", "CR", "CI", "HR", "CW", "CY", "CZ", "DK", "DJ", "DM", "DO", "EC",
    "EG", "SV", "GQ", "ER", "EE", "ET", "FK", "FO", "FJ", "FI", "FR", "GF", "PF", "GA",
    "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD", "GP", "GU", "GT", "GG", "GN", "GW",
    "GY", "HT", "HN", "HK", "HU", "IS", "IN", "ID", "IQ", "IE", "IL", "IT", "JM", "JP",
    "JE", "JO", "KZ", "KE", "KI", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LI", "LT",
    "LU", "MO", "MK", "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT",
    "MX", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM", "NA", "NR", "NP", "NL", "NC",
    "NZ", "NI", "NE", "NG", "NU", "MP", "NO", "OM", "PK", "PW", "PS", "PA", "PG", "PY",
    "PE", "PH", "PL", "PT", "PR", "QA", "RE", "RO", "RU", "RW", "BL", "SH", "KN", "LC",
    "MF", "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC", "SL", "SG", "SK", "SI",
    "SB", "SO", "ZA", "KR", "SS", "ES", "LK", "SR", "SE", "CH", "TW", "TJ", "TZ", "TH",
    "TL", "TG", "TO", "TT", "TN", "TR", "TM", "TC", "TV", "UG", "UA", "AE", "GB", "US",
    "UY", "UZ", "VU", "VA", "VE", "VN", "VG", "VI", "WF", "YE", "ZM", "ZW"
}

def is_valid_country_code(code: str) -> bool:
    """Check if a country code is supported by CJ Dropshipping."""
    if not code:
        return False
    return code.upper() in SUPPORTED_COUNTRY_CODES
