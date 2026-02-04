"""Feature flags for controlling optional GoodMap functionality.

Each flag can be toggled in the application configuration to enable or
disable the corresponding feature at runtime.

Flags:
    CategoriesHelp: Display help text alongside map categories to guide users.
    UseLazyLoading: Defer loading of location fields until they are needed,
        improving initial page load performance.
    EnableAdminPanel: Expose the admin panel for managing map data.
"""

from platzky import FeatureFlag

CategoriesHelp = FeatureFlag(alias="CATEGORIES_HELP", description="Show category help text")
UseLazyLoading = FeatureFlag(
    alias="USE_LAZY_LOADING", description="Enable lazy loading of location fields"
)
EnableAdminPanel = FeatureFlag(alias="ENABLE_ADMIN_PANEL", description="Enable admin panel")
