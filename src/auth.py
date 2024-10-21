from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from src import logger
from src.models import Employee
import time


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_SECRET_KEY: str = "aP3x!9Qz@2Lk#8Vw$7Jm^5Bn&4Xy*6Tg"
ALGORITHM = "HS256"
auth_access_token_expires: timedelta = timedelta(days=365)


def create_token(employee: Employee) -> str:
    is_admin = any(role.role.role_name =="ADMIN" for  role in employee.roles)
    data = {
        "sub": str(employee.id),
        "name": employee.firstname + " " + employee.lastname,
        "iat": datetime.now(timezone.utc),
        "admin": is_admin,
        "https://hasura.io/jwt/claims":{
            "x-hasura-allowed-roles": [ r.role.role_name.lower() for r in employee.roles ],
            "x-hasura-role": "admin" if is_admin else "employee",
            "x-hasura-user-id": str(employee.id),
            "x-hasura-employee-level": employee.position.level
        }
    }
    token = jwt.encode(data, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('sub')
        if user_id is None:
            raise credentials_exception
        else:
            print(user_id)
            return user_id
    except Exception as e:
        logger.exception(e)
        raise e

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)