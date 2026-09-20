from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import uuid

from db import get_db
from models import BetaFeedback, FeedbackVote, User
from schemas import FeedbackCreate, FeedbackResponse, FeedbackStatusUpdate
from auth import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.get("", response_model=List[FeedbackResponse])
def get_feedback(
    sort_by: str = Query("upvotes", description="Sort by 'upvotes' or 'recent'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(BetaFeedback)
    
    if sort_by == "recent":
        query = query.order_by(desc(BetaFeedback.created_at))
    else:
        query = query.order_by(desc(BetaFeedback.upvotes_count), desc(BetaFeedback.created_at))
        
    feedbacks = query.all()
    
    # Get user votes
    user_votes = db.query(FeedbackVote.feedback_id).filter(FeedbackVote.user_id == current_user.id).all()
    voted_feedback_ids = {v[0] for v in user_votes}
    
    results = []
    for f in feedbacks:
        results.append(FeedbackResponse(
            id=str(f.id),
            user_id=str(f.user_id),
            title=f.title,
            description=f.description,
            category=f.category,
            status=f.status,
            upvotes_count=f.upvotes_count,
            has_upvoted=f.id in voted_feedback_ids,
            created_at=f.created_at
        ))
        
    return results

@router.post("", response_model=FeedbackResponse)
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_feedback = BetaFeedback(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        upvotes_count=1
    )
    db.add(new_feedback)
    db.flush() # flush to get id
    
    vote = FeedbackVote(user_id=current_user.id, feedback_id=new_feedback.id)
    db.add(vote)
    
    db.commit()
    db.refresh(new_feedback)
    
    return FeedbackResponse(
        id=str(new_feedback.id),
        user_id=str(new_feedback.user_id),
        title=new_feedback.title,
        description=new_feedback.description,
        category=new_feedback.category,
        status=new_feedback.status,
        upvotes_count=new_feedback.upvotes_count,
        has_upvoted=True,
        created_at=new_feedback.created_at
    )

@router.post("/{feedback_id}/vote")
def toggle_vote(
    feedback_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    feedback = db.query(BetaFeedback).filter(BetaFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
        
    existing_vote = db.query(FeedbackVote).filter(
        FeedbackVote.user_id == current_user.id,
        FeedbackVote.feedback_id == feedback_id
    ).first()
    
    if existing_vote:
        # Remove vote
        db.delete(existing_vote)
        feedback.upvotes_count -= 1
        upvoted = False
    else:
        # Add vote
        vote = FeedbackVote(user_id=current_user.id, feedback_id=feedback_id)
        db.add(vote)
        feedback.upvotes_count += 1
        upvoted = True
        
    db.commit()
    
    return {"upvoted": upvoted, "upvotes_count": feedback.upvotes_count}
