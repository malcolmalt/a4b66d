from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    File,
    UploadFile,
    BackgroundTasks,
)
from sqlalchemy.orm.session import Session

from api import schemas
from api.dependencies.auth import get_current_user
from api.dependencies.db import get_db
from api.crud.prospect_files import ProspectFilesCrud
from os import SEEK_END
from api.core.constants import FILE_SIZE_LIMIT


router = APIRouter(prefix="/api", tags=["prospects_files"])


@router.post("/prospect_files", response_model=schemas.ProspectFileUploadResponse)
def post_csv(
    file: UploadFile = File(...),
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Check if user is logged in
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )

    # Check if file size is under file size limit
    file.file.seek(0, SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > FILE_SIZE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size too large",
        )

    # If the user selects no file or not a csv file, throw error
    if file.filename == "" or file.filename[-3:] != "csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect File Type"
        )

    # Create file inside of the database
    prospect_file_id, preview = ProspectFilesCrud.create_prospect_file(
        db, current_user.id, file
    )

    return {"id": prospect_file_id, "preview": preview}


@router.post(
    "/prospect_files/{prospect_file_id}/prospects",
    response_model=schemas.ProspectFileAddCSVResponse,
)
def add_csv_to_database(
    prospect_file_id: int,
    data: schemas.ProspectFileAddToDatabase,
    background_tasks: BackgroundTasks,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Check if the user is logged in
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )

    # Check if the the user has the prospect file
    prospect_file = ProspectFilesCrud.get_prospect_file_id(
        db, current_user.id, prospect_file_id
    )
    if not prospect_file:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"File with id {prospect_file_id} does not exist",
        )

    # Add prospects
    background_tasks.add_task(
        ProspectFilesCrud.add_prospect_file,
        db,
        current_user.id,
        prospect_file_id,
        data.email_index,
        data.first_name_index,
        data.last_name_index,
        data.force,
        data.has_header,
    )

    return {"id": prospect_file.id, "total_rows": prospect_file.total_rows}


@router.get(
    "/prospect_files/{prospect_file_id}/progress",
    response_model=schemas.ProspectFileProgressResponse,
)
def csv_progress(
    prospect_file_id: int,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Check if user is logged in
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )

    # Check if user has the prospect file
    prospect_file = ProspectFilesCrud.get_prospect_file_id(
        db, current_user.id, prospect_file_id
    )
    if not prospect_file:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"File with id {prospect_file_id} does not exist",
        )

    # Get progress
    total, done = ProspectFilesCrud.get_progress(db, current_user.id, prospect_file_id)

    return {"total": total, "done": done}
