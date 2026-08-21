"""Feature flags for controlling optional GoodMap functionality.

Each flag can be toggled in the application configuration to enable or
disable the corresponding feature at runtime.

Flags:
    CategoriesHelp: Display help text alongside map categories to guide users.
    EnableAdminPanel: Expose the admin panel for managing map data.
"""

from platzky import FeatureFlag

CategoriesHelp = FeatureFlag(alias="CATEGORIES_HELP", description="Show category help text")
EnableAdminPanel = FeatureFlag(alias="ENABLE_ADMIN_PANEL", description="Enable admin panel")
