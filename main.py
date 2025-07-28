from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from bson.objectid import ObjectId

app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["student_db"]
students_collection = db["students"]

#  Student data model
class Student(BaseModel):
    name: str
    age: int

class StudentOut(Student):
    id:str

def student_serializer(student) -> dict:
    return{
       "id": str(student["_id"]),
        "name": student["name"],
        "age": student["age"] 
    }
#  List to store students
students = []

#  Root route
@app.get("/")
def read_root():
    return {"message": "Welcome to Student API"}

@app.get("/students", response_model=List[StudentOut])
def get_students():
    data = students_collection.find()
    return [student_serializer(s) for s in data]

@app.post("/students", response_model=StudentOut)
def add_student(student: Student):
    result = students_collection.insert_one(student.dict())
    new_student = students_collection.find_one({"_id": result.inserted_id})
    return student_serializer(new_student)

@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: str):
    student = students_collection.find_one({"_id": ObjectId(student_id)})
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_serializer(student)

from bson.errors import InvalidId
def validate_object_id(student_id:str):
    try:
        return ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: str, student: Student):
    object_id = validate_object_id(student_id)
    result = students_collection.update_one(
        {"_id": object_id},
        {"$set": student.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    updated_student = students_collection.find_one({"_id": object_id})
    return student_serializer(updated_student)

@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    object_id = validate_object_id(student_id)
    result = students_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted"}

