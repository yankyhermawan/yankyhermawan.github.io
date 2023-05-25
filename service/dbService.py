from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
import json
from service.dbStructure import MapData

load_dotenv()

dbUrl = os.environ["DB_URL"]

class CreateConnection():
    def __init__(self):
        self.engine = create_engine(dbUrl)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
    
    def getAll(self):
        allData = self.session.query(MapData).all()
        json_data = json.dumps([str(data) for data in allData])
        return json_data