from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import verify_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_business_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    """
    JWT token se business_id (sub) nikaalti hai.
    Har protected route mein Depends(get_current_business_id) lagao.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token nahi mila — login karo"
        )

    payload = verify_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid ya expired hai"
        )

    business_id = payload.get("sub")

    if not business_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mein business_id nahi hai"
        )

    return business_id