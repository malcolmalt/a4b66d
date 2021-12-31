from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from sqlalchemy.orm.session import Session

from api import schemas
from api.dependencies.auth import get_current_user
from api.dependencies.db import get_db
from api.crud.prospectFiles import ProspectFilesCrud
from os import SEEK_END
from api.core.constants import FILE_SIZE_LIMIT 


router = APIRouter(prefix="/api", tags=["prospects_files"])

@router.post("/prospect_files", response_model=schemas.ProspectFileUploadResponse)
def post_csv(file: UploadFile = File(...), current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Check if user is logged in
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
    )

    # Check if file size is under file size limit
    file.file.seek(0, SEEK_END)
    fileSize = file.file.tell()
    file.file.seek(0)
    if fileSize > FILE_SIZE_LIMIT:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size too large")

    # If the user selects no file or not a csv file, throw error
    if file.filename == "" or file.filename[-3:] != "csv":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect File Type")
        
    # Create file inside of the database
    pf = ProspectFilesCrud.create_prospectFile(db, current_user.id, file)

    return {"id": pf[0], "preview": pf[1]}


@router.post("/prospect_files/{prospect_files_id}/prospects", response_model=schemas.ProspectFileAddCSVResponse)
def Add_Csv_To_Database(prospect_files_id: int, pf: schemas.ProspectFileAddToDatabase, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Check if the user is logged in
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
    )

    # Check if the the user has the prospect file
    pfcheck = ProspectFilesCrud.get_pfId(db, current_user.id, prospect_files_id)
    if not pfcheck:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"File with id {prospect_files_id} does not exist")
    
    # Check if user has access to the file
    if pfcheck.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"You do not have access to that file")
    
    # Add prospects and get progress
    pf = ProspectFilesCrud.add_prospectFile(db, current_user.id, prospect_files_id, pf.email_index, pf.first_name_index, pf.last_name_index, pf.force, pf.has_header)
    progress = ProspectFilesCrud.get_progress(db, current_user.id, prospect_files_id)

    return {'id': pf.id, "total_rows": pf.total_rows, "done": progress[1]}


@router.get("/prospect_files/{prospect_files_id}/progress", response_model=schemas.ProspectFileProgressResponse)
def csv_progress(prospect_files_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):

    # Check if user is logged in
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
    )

    # Check if user has the prospect file
    pfcheck = ProspectFilesCrud.get_pfId(db, current_user.id, prospect_files_id)
    if not pfcheck:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"File with id {prospect_files_id} does not exist")
    
    # Check if user has access to the file
    if pfcheck.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"You do not have access to that file")

    # Get progress
    progress = ProspectFilesCrud.get_progress(db, current_user.id, prospect_files_id)

    return {'total': progress[0], 'done': progress[1]}
