# This module stores the df_scaled in memory so other parts can use it.

_df_scaled = None  # internal variable (starts empty)

def set_df_scaled(df):
    """Call this once to register the preprocessed df_scaled."""
    global _df_scaled
    _df_scaled = df

def get_df_scaled():
    """Retrieve the registered df_scaled. Raises error if not set yet."""
    if _df_scaled is None:
        raise RuntimeError("df_scaled has not been set. Use set_df_scaled(df) first.")
    return _df_scaled
