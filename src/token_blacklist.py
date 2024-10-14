# In-memory storage for blacklisted tokens

# A set to store blacklisted tokens
# Using a set for O(1) lookup time when checking if a token is blacklisted
# In a production environment, replace with a database
blacklisted_tokens = set()

# Adds a token to blacklist
# Args: token (str): The JWT token to be blacklisted
# Called when a user logs out or when a token needs to be invalidated
def add_to_blacklist(token: str):
    blacklisted_tokens.add(token)

# Checks if a given token is blacklisted
# Args: token (str): The JWT token to check
# Returns: bool: True if the token is blacklisted, False otherwise
# Called before processing a request to ensure the token is still valid
def is_blacklisted(token: str) -> bool:
    return token in blacklisted_tokens
