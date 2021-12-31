from fastapi import UploadFile
from sqlalchemy.orm.session import Session
from api.models import ProspectFiles, Prospect
from api.core.constants import PREV_MAX
import re

class ProspectFilesCrud:
    @classmethod
    def create_prospectFile(cls, db: Session, user_id: int, file: UploadFile) -> tuple[int, list[list[str]]]:

        # Create Preview
        dataIO = file.file
        totalLines = 0
        preview = []
        previewCount = 0
        for line in dataIO:
            ls = re.split(",", line.decode('UTF-8').strip())
            if previewCount < PREV_MAX:
                preview.append(ls)
                previewCount += 1
            totalLines += 1

        # Set fileIO back to start
        dataIO.seek(0)

        beforeUpload = db.query(Prospect).filter(Prospect.user_id == user_id).count()

        # Add prospect to the database
        prospectFile = ProspectFiles(file=dataIO.read(), total_rows=totalLines, prospects_before_upload=beforeUpload, preview=str(preview), user_id=user_id)
        db.add(prospectFile)
        db.commit()
        db.refresh(prospectFile)
        return (prospectFile.id, preview)

    @classmethod
    def add_prospectFile(cls, db: Session, user_id: int, pfId: int, email_id: int, first_id: int, last_id: int, force: bool, header: bool) -> ProspectFiles:

        # Get file from DB and decode
        pf = db.query(ProspectFiles).get((pfId, user_id))
        pf.prospects_before_upload = db.query(Prospect).filter(Prospect.user_id == user_id).count()
        file = pf.file
        decode = file.decode('UTF-8')
        rows = iter(re.split("\\n", decode))

        # Deal with header
        if header:
            rows.__next__()
            pf.total_rows -= 1
    
        # Loop through file and append prospect objects to list
        proList = []
        duplicateCount = 0
        for row in rows:
            if row != "":
                row = row.strip()
                items = re.split(",", row)
                dup = db.query(Prospect).filter(Prospect.email == items[email_id], Prospect.user_id == user_id).first()
                if not dup:
                    pros = Prospect(email=items[email_id], first_name=items[first_id], last_name=items[last_id], user_id=user_id)
                    proList.append(pros)
                    # db.add(pros)
                else:
                    if force:
                        dup.first_name = items[first_id]
                        dup.last_name = items[last_id]
                    duplicateCount += 1
                    # pf.prospects_before_upload -= 1      
            # db.commit()
    
        # Add all prospects to DB
        pf.prospects_before_upload -= duplicateCount            
        db.add_all(proList)
        db.commit()
                
        return pf

    @classmethod
    def get_progress(cls, db: Session, user_id: int, progress_id: int) -> tuple[int, int]:
        # Find prospect file and subtract prospects before upload from current prospect count
        pf = db.query(ProspectFiles).filter(ProspectFiles.id == progress_id).first()
        totalProspects = db.query(Prospect).filter(Prospect.user_id == user_id).count()
        progress = totalProspects - pf.prospects_before_upload
        return (pf.total_rows, progress)

    @classmethod
    def get_pfId(cls, db: Session, user_id: int, pfId: int) -> ProspectFiles:
        # Check if a prospect file id exists 
        return db.query(ProspectFiles).filter(ProspectFiles.id == pfId, ProspectFiles.user_id == user_id).first()
