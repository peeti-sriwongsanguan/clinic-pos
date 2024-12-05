class ThemeConfig:
    # Brand Colors
    PRIMARY_PINK = "#FFE4E8"
    SECONDARY_PINK = "#FFB6C1"
    DARK_PINK = "#FF69B4"
    WHITE = "#FFFFFF"
    GRAY = "#666666"

    # Font Configuration
    THAI_FONT = "Sarabun"  # or "TH Sarabun New" if available
    ENGLISH_FONT = "Helvetica"

    @classmethod
    def get_font(cls, language='en', size=10, weight='normal'):
        """Get appropriate font based on language"""
        font_family = cls.THAI_FONT if language == 'th' else cls.ENGLISH_FONT
        return (font_family, size, weight)

    # Dynamic font properties
    @classmethod
    def MAIN_FONT(cls, language='en'):
        return cls.get_font(language, 10)

    @classmethod
    def HEADER_FONT(cls, language='en'):
        return cls.get_font(language, 14, 'bold')

    @classmethod
    def TITLE_FONT(cls, language='en'):
        return cls.get_font(language, 18, 'bold')