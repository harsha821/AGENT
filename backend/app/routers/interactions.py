from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Interaction, HCP
from app.schemas import InteractionCreate, InteractionUpdate, InteractionOut

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("", response_model=InteractionOut)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    hcp = db.query(HCP).filter(HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")

    interaction = Interaction(**payload.model_dump(), created_via="form")
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.get("", response_model=list[InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return db.query(Interaction).order_by(Interaction.created_at.desc()).all()


@router.put("/{interaction_id}", response_model=InteractionOut)
def update_interaction(interaction_id: int, payload: InteractionUpdate, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"status": "deleted", "id": interaction_id}
