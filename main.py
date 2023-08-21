from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


class Todo(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(lt=6, gt=0, description="The priority must be between 1-5")
    complete: bool


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/")
async def read_all(db: Session = Depends(get_db)):
    return db.query(models.Todos).all()


@app.get("/todo/{todo_id}")
async def read_task(todo_id: int, db: Session = Depends(get_db)):
    final = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if final is not None:
        return final
    raise HTTPException(status_code=404, detail="Item Not Found")


@app.post("/")
async def create_todo(todo: Todo, db: Session = Depends(get_db)):
    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.complete = todo.complete
    todo_model.priority = todo.priority

    db.add(todo_model)
    db.commit()

    return {
        'status': 201,
        'transaction': 'Successful'
    }


@app.put("/todo/{todo_id}")
async def update_todo(todo_id: int, updated_todo: Todo, db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo_model.title = updated_todo.title
    todo_model.description = updated_todo.description
    todo_model.complete = updated_todo.complete
    todo_model.priority = updated_todo.priority

    db.add(todo_model)
    db.commit()


@app.delete("/")
async def delete_todo(todo_id:int,db: Session = Depends(get_db)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is not None:
        db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
        db.commit()
        return {
            'status':201,
            'transaction':'Successful'
        }
    raise HTTPException(status_code=404, detail="Error in Deleting the Todo")