from fastapi import UploadFile
from sqlalchemy.orm.session import Session
from api.models import ProspectFiles, Prospect
from api.core.constants import PREVIEW_MAX
import re


class ProspectFilesCrud:
    @classmethod
    def create_prospect_file(
        cls, db: Session, user_id: int, file: UploadFile
    ) -> tuple[int, list[list[str]]]:

        # Create Preview
        data = file.file
        total_rows = 0
        preview = []
        preview_count = 0
        for line in data:
            ls = re.split(",", line.decode("UTF-8").strip())
            if preview_count < PREVIEW_MAX:
                preview.append(ls)
                preview_count += 1
            total_rows += 1

        # Set file back to start
        data.seek(0)

        # Add prospect to the database
        prospect_file = ProspectFiles(
            file=data.read(), total_rows=total_rows, user_id=user_id
        )
        db.add(prospect_file)
        db.commit()
        db.refresh(prospect_file)
        return (prospect_file.id, preview)

    @classmethod
    def add_prospect_file(
        cls,
        db: Session,
        user_id: int,
        prospect_file_id: int,
        email_id: int,
        first_id: int,
        last_id: int,
        force: bool,
        header: bool,
    ) -> ProspectFiles:

        # Get file from DB and decode
        prospect_file = db.query(ProspectFiles).get((prospect_file_id, user_id))
        file = prospect_file.file
        decode = file.decode("UTF-8")
        rows = iter(re.split("\\n", decode))

        # Deal with header
        if header:
            rows.__next__()
            prospect_file.total_rows -= 1

        # Loop through file and append prospect objects to list
        prospect_list = []
        for row in rows:
            if row != "":
                row = row.strip()
                items = re.split(",", row)
                duplicate = (
                    db.query(Prospect)
                    .filter(
                        Prospect.email == items[email_id], Prospect.user_id == user_id
                    )
                    .first()
                )
                if not duplicate:
                    prospect = Prospect(
                        email=items[email_id],
                        first_name=items[first_id],
                        last_name=items[last_id],
                        user_id=user_id,
                        prospect_file_id=prospect_file_id,
                    )
                    prospect_list.append(prospect)
                else:
                    if force:
                        duplicate.first_name = items[first_id]
                        duplicate.last_name = items[last_id]
                    duplicate.prospect_file_id = prospect_file_id

        # Add all prospects to DB
        db.add_all(prospect_list)
        db.commit()
        return prospect_file

    @classmethod
    def get_progress(
        cls, db: Session, user_id: int, prospect_file_id: int
    ) -> tuple[int, int]:
        # Find prospect file and subtract prospects before upload from current prospect count
        prospect_file = (
            db.query(ProspectFiles).filter(ProspectFiles.id == prospect_file_id).first()
        )
        total_prospects_done = (
            db.query(Prospect)
            .filter(
                Prospect.user_id == user_id,
                Prospect.prospect_file_id == prospect_file_id,
            )
            .count()
        )
        return (prospect_file.total_rows, total_prospects_done)

    @classmethod
    def get_prospect_file_id(
        cls, db: Session, user_id: int, prospect_file_id: int
    ) -> ProspectFiles:
        # Check if a prospect file id exists
        return (
            db.query(ProspectFiles)
            .filter(
                ProspectFiles.id == prospect_file_id, ProspectFiles.user_id == user_id
            )
            .first()
        )
