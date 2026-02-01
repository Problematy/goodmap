from platzky import FeatureFlag

CategoriesHelp = FeatureFlag(alias="CATEGORIES_HELP", description="Show category help text")
UseLazyLoading = FeatureFlag(
    alias="USE_LAZY_LOADING", description="Enable lazy loading of location fields"
)
EnableAdminPanel = FeatureFlag(alias="ENABLE_ADMIN_PANEL", description="Enable admin panel")
