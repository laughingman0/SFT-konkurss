import os

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///./mathdb2.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
class Structuring(BaseModel):
    TestName: str
    Context_for_tasks_and_tasks_themselves: list[str]
    conclusions: str