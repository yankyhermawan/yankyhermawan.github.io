from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

class MapData(declarative_base()):    
    __tablename__ = "Map Data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    def __str__(self):
        return self.name