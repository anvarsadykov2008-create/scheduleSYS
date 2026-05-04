
# ──── Auth ────

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRoleEnum
    teacher_id: Optional[int] = None
    group_id: Optional[int] = None
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True
